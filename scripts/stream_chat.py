#!/usr/bin/env python3
"""Live chat collection from streaming platforms.

Generator-based chat fetchers for Twitch IRC and YouTube Data API v3.
Each source yields normalized ChatMessage records into a list with time-bounded capture.
"""
import json
import os
import re
import socket
import ssl
import time
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlparse


# Normalized chat message structure
ChatMessage = namedtuple("ChatMessage", ["timestamp", "username", "text"])


def extract_youtube_video_id(url):
    """Parse YouTube video ID from URL."""
    patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/live/([A-Za-z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url or "")
        if match:
            return match.group(1)
    return None


def parse_irc_message(raw_line):
    """Parse IRCv3 message per RFC1459 and IRCv3 message-tags spec.
    
    Format: [@tags] [:prefix] COMMAND [params] [:trailing]
    
    Returns: (command, params, trailing, tags_dict) or None
    """
    line = raw_line.strip()
    if not line:
        return None
    
    # Parse tags (IRCv3)
    tags = {}
    if line.startswith("@"):
        tags_end = line.find(" ")
        if tags_end == -1:
            return None
        tags_str = line[1:tags_end]
        line = line[tags_end + 1:].lstrip()
        
        # Parse tag=value pairs separated by semicolon
        for tag_pair in tags_str.split(";"):
            if "=" in tag_pair:
                key, value = tag_pair.split("=", 1)
                tags[key] = value
    
    # Parse prefix (optional, starts with colon)
    if line.startswith(":"):
        prefix_end = line.find(" ")
        if prefix_end == -1:
            return None
        line = line[prefix_end + 1:].lstrip()
    
    # Parse command and parameters
    if " :" in line:
        # Has trailing parameter
        command_params, trailing = line.split(" :", 1)
        parts = command_params.split()
    else:
        # No trailing
        parts = line.split()
        trailing = None
    
    if not parts:
        return None
    
    command = parts[0]
    params = parts[1:] if len(parts) > 1 else []
    
    return (command, params, trailing, tags)


def collect_twitch_irc(channel, username, oauth_token, duration_seconds=None, max_messages=10000):
    """Generator-based Twitch IRC collector.
    
    Connects to Twitch IRC, yields ChatMessage records until time limit or message limit.
    
    Args:
        channel: Twitch channel name
        username: Bot username for IRC connection
        oauth_token: OAuth token (with or without 'oauth:' prefix)
        duration_seconds: Stop after N seconds (None = unlimited)
        max_messages: Stop after N messages (default 10000)
        
    Yields:
        ChatMessage(timestamp, username, text) tuples
    """
    channel = channel.lower()
    username = username.lower()
    token = oauth_token.removeprefix("oauth:").strip()
    
    start_time = time.time()
    message_count = 0
    
    # Connect to Twitch IRC over TLS
    ssl_context = ssl.create_default_context()
    
    with socket.create_connection(("irc.chat.twitch.tv", 6697), timeout=20) as sock:
        with ssl_context.wrap_socket(sock, server_hostname="irc.chat.twitch.tv") as tls_sock:
            tls_sock.settimeout(2.0)  # 2s timeout for recv
            
            # Send IRC handshake
            tls_sock.sendall(f"PASS oauth:{token}\r\n".encode())
            tls_sock.sendall(f"NICK {username}\r\n".encode())
            tls_sock.sendall("CAP REQ :twitch.tv/tags\r\n".encode())
            tls_sock.sendall(f"JOIN #{channel}\r\n".encode())
            
            buffer = ""
            
            while True:
                # Check time limit
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break
                
                # Check message limit
                if message_count >= max_messages:
                    break
                
                # Read data
                try:
                    chunk = tls_sock.recv(4096).decode("utf-8", errors="replace")
                    if not chunk:
                        break
                    buffer += chunk
                except socket.timeout:
                    continue
                except Exception:
                    break
                
                # Process complete lines
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    
                    # Handle PING
                    if line.startswith("PING"):
                        pong_target = line.split(" ", 1)[1] if " " in line else ""
                        tls_sock.sendall(f"PONG {pong_target}\r\n".encode())
                        continue
                    
                    # Parse IRC message
                    parsed = parse_irc_message(line)
                    if not parsed:
                        continue
                    
                    command, params, trailing, tags = parsed
                    
                    # Only process PRIVMSG
                    if command != "PRIVMSG":
                        continue
                    
                    # Extract timestamp from tags
                    ts_ms = tags.get("tmi-sent-ts", "")
                    try:
                        timestamp = float(ts_ms) / 1000.0
                    except (ValueError, ZeroDivisionError):
                        timestamp = time.time()
                    
                    # Extract username
                    user_from_tag = tags.get("display-name") or tags.get("user-id", "")
                    
                    # Extract message text (trailing parameter)
                    message_text = trailing or ""
                    
                    if message_text:
                        yield ChatMessage(timestamp, user_from_tag, message_text)
                        message_count += 1


def collect_youtube_livechat(video_id, api_key, duration_seconds=None, max_messages=10000):
    """Generator-based YouTube live chat collector.
    
    Polls YouTube Data API v3 liveChatMessages endpoint.
    
    Args:
        video_id: YouTube video ID
        api_key: YouTube Data API key
        duration_seconds: Stop after N seconds (None = unlimited)
        max_messages: Stop after N messages (default 10000)
        
    Yields:
        ChatMessage(timestamp, username, text) tuples
    """
    import urllib.request
    import urllib.parse
    import urllib.error
    
    def fetch_json(url):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    
    # Get live chat ID
    video_url = ("https://www.googleapis.com/youtube/v3/videos?" +
                 urllib.parse.urlencode({
                     "part": "liveStreamingDetails",
                     "id": video_id,
                     "key": api_key
                 }))
    
    try:
        video_data = fetch_json(video_url)
    except urllib.error.HTTPError:
        return  # No data, stop generator
    
    items = video_data.get("items", [])
    if not items:
        return
    
    live_details = items[0].get("liveStreamingDetails", {})
    chat_id = live_details.get("activeLiveChatId")
    
    if not chat_id:
        return
    
    # Poll for messages
    start_time = time.time()
    message_count = 0
    next_page_token = None
    
    while True:
        # Check limits
        if duration_seconds and (time.time() - start_time) > duration_seconds:
            break
        if message_count >= max_messages:
            break
        
        # Build request
        params = {
            "part": "snippet,authorDetails",
            "liveChatId": chat_id,
            "maxResults": 200,
            "key": api_key
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        
        chat_url = ("https://www.googleapis.com/youtube/v3/liveChat/messages?" +
                   urllib.parse.urlencode(params))
        
        try:
            chat_data = fetch_json(chat_url)
        except urllib.error.HTTPError:
            break
        
        # Process messages
        for item in chat_data.get("items", []):
            snippet = item.get("snippet", {})
            author = item.get("authorDetails", {})
            
            # Parse timestamp
            published = snippet.get("publishedAt", "")
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                timestamp = dt.timestamp()
            except (ValueError, AttributeError):
                timestamp = time.time()
            
            # Extract username and message
            username = author.get("displayName") or author.get("channelId") or "unknown"
            
            text_details = snippet.get("textMessageDetails", {})
            message_text = text_details.get("messageText") or snippet.get("displayMessage", "")
            
            if message_text:
                yield ChatMessage(timestamp, username, message_text)
                message_count += 1
                
                if message_count >= max_messages:
                    return
        
        # Pagination and polling delay
        next_page_token = chat_data.get("nextPageToken")
        poll_ms = int(chat_data.get("pollingIntervalMillis", 5000))
        time.sleep(max(1.0, poll_ms / 1000.0))


def create_chat_collector(stream_url, video_id_override=None, env=None):
    """Factory to create appropriate chat collector generator.
    
    Args:
        stream_url: Stream URL (YouTube or Twitch)
        video_id_override: Explicit video ID for YouTube
        env: Environment variables dict (default os.environ)
        
    Returns:
        (collector_fn, platform, error) tuple
        collector_fn is a callable() that returns a generator, or None if unavailable
    """
    environment = env if env is not None else os.environ
    parsed = urlparse(stream_url or "")
    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    
    # YouTube
    if hostname in ("youtube.com", "m.youtube.com", "youtu.be"):
        api_key = environment.get("YOUTUBE_API_KEY", "").strip()
        if not api_key:
            return None, "youtube", "YOUTUBE_API_KEY not set"
        
        vid_id = video_id_override or extract_youtube_video_id(stream_url)
        if not vid_id:
            return None, "youtube", "Could not extract video ID"
        
        # Return a callable that creates the generator
        def collector():
            return collect_youtube_livechat(vid_id, api_key)
        
        return collector, "youtube", None
    
    # Twitch
    if hostname == "twitch.tv":
        path_parts = [p for p in parsed.path.split("/") if p]
        channel = path_parts[0] if path_parts else None
        
        if not channel:
            return None, "twitch", "Could not extract channel name"
        
        bot_user = environment.get("TWITCH_CHAT_USERNAME", "").strip()
        bot_token = environment.get("TWITCH_CHAT_TOKEN", "").strip()
        
        if not bot_user or not bot_token:
            return None, "twitch", "TWITCH_CHAT_USERNAME and TWITCH_CHAT_TOKEN not set"
        
        # Return a callable that creates the generator
        def collector():
            return collect_twitch_irc(channel, bot_user, bot_token)
        
        return collector, "twitch", None
    
    return None, "unknown", f"Unsupported platform: {hostname or 'none'}"
