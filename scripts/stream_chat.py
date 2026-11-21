#!/usr/bin/env python3
"""Live chat collection from streaming platforms.

Supports Twitch (via IRC) and YouTube (via Data API v3) for real-time chat monitoring.
All network operations are in background threads with graceful error handling.
"""
import json
import os
import re
import socket
import ssl
import threading
import time
from collections import deque
from datetime import datetime
from urllib.parse import urlparse


def extract_youtube_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"v=([A-Za-z0-9_-]{11})",           # ?v=VIDEO_ID
        r"youtu\.be/([A-Za-z0-9_-]{11})",   # youtu.be/VIDEO_ID
        r"youtube\.com/live/([A-Za-z0-9_-]{11})"  # /live/VIDEO_ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url or "")
        if match:
            return match.group(1)
    return None


class ChatCollectorBase:
    """Base class for platform chat collectors."""
    
    def __init__(self):
        self._chat_buffer = deque(maxlen=50000)
        self._lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._worker_thread = None
        self.connection_status = "initializing"
        self.error_message = None
    
    def begin_collection(self):
        """Start collecting messages in a background thread."""
        self._worker_thread = threading.Thread(
            target=self._safe_run, 
            daemon=True
        )
        self._worker_thread.start()
        return self
    
    def end_collection(self):
        """Stop the collection thread."""
        self._stop_flag.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
    
    def get_messages_in_range(self, start_epoch, end_epoch):
        """Retrieve messages within a time range."""
        with self._lock:
            return [
                dict(msg) for msg in self._chat_buffer
                if start_epoch <= msg["epoch"] <= end_epoch
            ]
    
    def clear_messages_before(self, epoch_cutoff):
        """Remove old messages to save memory."""
        with self._lock:
            while self._chat_buffer and self._chat_buffer[0]["epoch"] < epoch_cutoff:
                self._chat_buffer.popleft()
    
    def _record_message(self, epoch_time, username, message_text, msg_id=None):
        """Store a chat message."""
        with self._lock:
            self._chat_buffer.append({
                "epoch": float(epoch_time),
                "user": str(username or "unknown"),
                "text": str(message_text or "")[:500],
                "id": msg_id
            })
    
    def _safe_run(self):
        """Wrapper with error handling."""
        try:
            self.collect_messages()
        except Exception as exc:
            self.error_message = f"{type(exc).__name__}: {exc}"
            self.connection_status = "error"
    
    def collect_messages(self):
        """Override this to implement platform-specific collection."""
        raise NotImplementedError


class YouTubeLiveChatCollector(ChatCollectorBase):
    """Collects live chat from YouTube streams via Data API v3."""
    
    def __init__(self, video_id, api_key):
        super().__init__()
        self.video_id = video_id
        self.api_key = api_key
    
    def _fetch_json(self, api_url):
        """Make an authenticated API request."""
        import urllib.request
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    
    def collect_messages(self):
        """Poll YouTube's live chat messages endpoint."""
        import urllib.request
        import urllib.parse
        import urllib.error
        
        # Step 1: Get the live chat ID for this video
        video_params = urllib.parse.urlencode({
            "part": "liveStreamingDetails",
            "id": self.video_id,
            "key": self.api_key
        })
        video_url = f"https://www.googleapis.com/youtube/v3/videos?{video_params}"
        
        try:
            video_data = self._fetch_json(video_url)
        except urllib.error.HTTPError as e:
            self.connection_status = "error"
            self.error_message = f"YouTube API error: {e.code}"
            return
        
        items = video_data.get("items", [])
        if not items:
            self.connection_status = "error"
            self.error_message = "Video not found"
            return
        
        streaming_details = items[0].get("liveStreamingDetails", {})
        chat_id = streaming_details.get("activeLiveChatId")
        
        if not chat_id:
            self.connection_status = "error"
            self.error_message = "No active live chat"
            return
        
        # Step 2: Poll for messages
        self.connection_status = "connected"
        next_page = None
        
        while not self._stop_flag.is_set():
            msg_params = {
                "part": "snippet,authorDetails",
                "liveChatId": chat_id,
                "maxResults": 200,
                "key": self.api_key
            }
            if next_page:
                msg_params["pageToken"] = next_page
            
            msg_url = ("https://www.googleapis.com/youtube/v3/liveChat/messages?" +
                      urllib.parse.urlencode(msg_params))
            
            try:
                chat_data = self._fetch_json(msg_url)
            except urllib.error.HTTPError as e:
                self.connection_status = "error"
                self.error_message = f"Chat API error: {e.code}"
                return
            
            # Process messages
            for item in chat_data.get("items", []):
                snippet = item.get("snippet", {})
                author = item.get("authorDetails", {})
                
                # Parse timestamp
                published = snippet.get("publishedAt", "")
                try:
                    timestamp = datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    ).timestamp()
                except (ValueError, AttributeError):
                    timestamp = time.time()
                
                # Extract message text
                text_details = snippet.get("textMessageDetails", {})
                message = text_details.get("messageText") or snippet.get("displayMessage", "")
                
                # Extract author
                author_name = (author.get("displayName") or 
                             author.get("channelId") or "unknown")
                
                self._record_message(
                    timestamp,
                    author_name,
                    message,
                    item.get("id")
                )
            
            # Pagination and polling interval
            next_page = chat_data.get("nextPageToken")
            poll_ms = int(chat_data.get("pollingIntervalMillis", 5000))
            self._stop_flag.wait(max(1.0, poll_ms / 1000.0))


class TwitchIRCChatCollector(ChatCollectorBase):
    """Collects live chat from Twitch via IRC protocol."""
    
    def __init__(self, channel_name, bot_username, oauth_token):
        super().__init__()
        self.channel = channel_name.lower()
        self.username = bot_username.lower()
        self.token = oauth_token.removeprefix("oauth:").strip()
    
    def collect_messages(self):
        """Connect to Twitch IRC and stream messages."""
        ssl_context = ssl.create_default_context()
        
        with socket.create_connection(
            ("irc.chat.twitch.tv", 6697), timeout=20
        ) as sock:
            with ssl_context.wrap_socket(
                sock, server_hostname="irc.chat.twitch.tv"
            ) as secure_sock:
                secure_sock.settimeout(1.0)
                
                # Authenticate
                secure_sock.sendall(f"PASS oauth:{self.token}\r\n".encode())
                secure_sock.sendall(f"NICK {self.username}\r\n".encode())
                secure_sock.sendall("CAP REQ :twitch.tv/tags\r\n".encode())
                secure_sock.sendall(f"JOIN #{self.channel}\r\n".encode())
                
                self.connection_status = "connected"
                line_buffer = b""
                
                while not self._stop_flag.is_set():
                    try:
                        chunk = secure_sock.recv(4096)
                        if not chunk:
                            self.connection_status = "disconnected"
                            return
                        line_buffer += chunk
                    except socket.timeout:
                        continue
                    
                    # Process complete lines
                    while b"\r\n" in line_buffer:
                        line_bytes, line_buffer = line_buffer.split(b"\r\n", 1)
                        line_text = line_bytes.decode("utf-8", errors="replace")
                        
                        # Handle PING
                        if line_text.startswith("PING "):
                            pong = "PONG " + line_text[5:] + "\r\n"
                            secure_sock.sendall(pong.encode())
                            continue
                        
                        # Parse chat message
                        self._parse_irc_message(line_text)
    
    def _parse_irc_message(self, line):
        """Extract message details from IRC format."""
        # Parse IRCv3 tags if present
        tag_dict = {}
        if line.startswith("@"):
            tags_str, _, line = line.partition(" ")
            for tag in tags_str[1:].split(";"):
                if "=" in tag:
                    key, value = tag.split("=", 1)
                    tag_dict[key] = value
        
        # Only process PRIVMSG
        if " PRIVMSG " not in line:
            return
        
        # Extract username and message
        prefix, _, remainder = line.partition(" PRIVMSG ")
        username = prefix.lstrip(":").split("!", 1)[0]
        _, _, message_text = remainder.partition(" :")
        
        # Parse timestamp from tags (milliseconds)
        try:
            epoch_time = float(tag_dict.get("tmi-sent-ts", "0")) / 1000.0
        except ValueError:
            epoch_time = time.time()
        
        if epoch_time == 0:
            epoch_time = time.time()
        
        self._record_message(
            epoch_time,
            tag_dict.get("user-id") or username,
            message_text,
            tag_dict.get("id")
        )


def create_chat_collector(stream_url, video_id_override=None, env=None):
    """Factory function to create the appropriate chat collector.
    
    Args:
        stream_url: The stream URL (YouTube or Twitch)
        video_id_override: Explicit video ID for YouTube
        env: Environment variables dict (defaults to os.environ)
        
    Returns:
        (collector, platform_name, error_reason) tuple
        collector is None if creation failed, with error_reason explaining why
    """
    environment = env if env is not None else os.environ
    parsed = urlparse(stream_url or "")
    hostname = (parsed.hostname or "").lower()
    hostname = hostname.removeprefix("www.")
    
    # YouTube detection
    if hostname in ("youtube.com", "m.youtube.com", "youtu.be"):
        api_key = environment.get("YOUTUBE_API_KEY", "").strip()
        if not api_key:
            return None, "youtube", "YOUTUBE_API_KEY environment variable not set"
        
        vid_id = video_id_override or extract_youtube_video_id(stream_url)
        if not vid_id:
            return None, "youtube", "Could not extract video ID from URL"
        
        collector = YouTubeLiveChatCollector(vid_id, api_key)
        return collector, "youtube", None
    
    # Twitch detection
    if hostname == "twitch.tv":
        # Extract channel from URL path
        path_segments = [p for p in parsed.path.split("/") if p]
        channel = path_segments[0] if path_segments else None
        
        if not channel:
            return None, "twitch", "Could not extract channel name from URL"
        
        bot_user = environment.get("TWITCH_CHAT_USERNAME", "").strip()
        bot_token = environment.get("TWITCH_CHAT_TOKEN", "").strip()
        
        if not bot_user or not bot_token:
            return (None, "twitch",
                    "TWITCH_CHAT_USERNAME and TWITCH_CHAT_TOKEN environment variables not set")
        
        collector = TwitchIRCChatCollector(channel, bot_user, bot_token)
        return collector, "twitch", None
    
    return None, "unknown", f"Unsupported platform: {hostname or 'none'}"
