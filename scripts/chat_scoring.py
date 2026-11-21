#!/usr/bin/env python3
"""Chat activity analysis for stream highlight detection.

Analyzes chat message bursts from Twitch IRC or YouTube live chat to identify
high-engagement moments. Designed to resist spam inflation by deweighting repeated
messages from individual users.
"""
import re


# High-engagement indicators: excitement, reactions, clip requests
EXCITEMENT_WORDS = {
    "wow", "amazing", "incredible", "insane", "crazy", "epic", "perfect",
    "nice", "clip", "highlight", "moment", "omg", "lol", "lmao", "hype"
}

EXCITEMENT_EMOTES = {
    "pog", "poggers", "kekw", "omegalul", "hyperclap", "widehappy", 
    "pepehype", "monkas", "monkaw"
}

# Emoji patterns for reactions (excitement, laughter, surprise)
EMOJI_PATTERN = re.compile(r"[😂🤣💀😱😮🔥👏🎉🎊]")


def is_excited_message(text):
    """Detect if a message shows excitement or strong reaction."""
    lower = text.lower()
    
    # Check for excitement words
    if any(word in lower for word in EXCITEMENT_WORDS):
        return True
    
    # Check for common Twitch emotes
    if any(emote in lower for emote in EXCITEMENT_EMOTES):
        return True
    
    # Check for reaction emojis
    if EMOJI_PATTERN.search(text):
        return True
    
    # Check for exclamation marks (but require content too)
    if "!" in text and len(text.split()) >= 2:
        return True
    
    return False


def analyze_chat_bursts(messages, window_starts, window_duration):
    """Analyze chat activity in time windows to find engagement bursts.
    
    Scores windows based on unique participant activity with spam resistance.
    A single user spamming the same message has minimal impact.
    
    Args:
        messages: List of dicts with keys: t (timestamp), user (username), text (message)
        window_starts: List of start times (seconds) to analyze
        window_duration: Window length in seconds
        
    Returns:
        List of dicts with: start, message_count, unique_users, excited_users,
                           unique_messages, peak_time, peak_user_count, burst_score
    """
    results = []
    
    for start_time in window_starts:
        end_time = start_time + window_duration
        
        # Filter messages in this window
        window_msgs = [
            m for m in messages 
            if start_time <= float(m.get("t", -1)) < end_time
        ]
        
        # Group messages by user, tracking unique message texts
        user_messages = {}  # user -> set of unique message texts
        time_buckets = {}   # time_bucket -> (set of users, set of excited users)
        
        for msg in window_msgs:
            user = str(msg.get("user", "")).strip() or "anon"
            text = re.sub(r"\s+", " ", str(msg.get("text", ""))).strip()
            
            if not text:
                continue
            
            # Track unique messages per user
            user_messages.setdefault(user, set()).add(text.lower())
            
            # Track activity in 5-second buckets for peak detection
            bucket_idx = int((float(msg["t"]) - start_time) / 5.0)
            users_set, excited_set = time_buckets.setdefault(
                bucket_idx, (set(), set())
            )
            users_set.add(user)
            if is_excited_message(text):
                excited_set.add(user)
        
        # Compute metrics
        unique_user_count = len(user_messages)
        excited_user_count = sum(
            1 for user, texts in user_messages.items()
            if any(is_excited_message(text) for text in texts)
        )
        
        # Total unique messages (prevents one person from inflating the count)
        unique_message_count = sum(len(texts) for texts in user_messages.values())
        
        # Find peak bucket
        if time_buckets:
            peak_bucket, (peak_users, peak_excited) = max(
                time_buckets.items(),
                key=lambda item: len(item[1][0]) + 2 * len(item[1][1])
            )
            peak_time = start_time + peak_bucket * 5.0 + 2.5
            peak_user_count = len(peak_users)
        else:
            peak_time = start_time + window_duration / 2
            peak_user_count = 0
        
        # Compute burst score using MAD (Median Absolute Deviation) later
        results.append({
            "start": float(start_time),
            "message_count": len(window_msgs),
            "unique_users": unique_user_count,
            "excited_users": excited_user_count,
            "unique_messages": unique_message_count,
            "peak_time": float(peak_time),
            "peak_user_count": peak_user_count,
            "burst_score": 0.0  # Computed after we have all windows
        })
    
    # Compute burst scores using MAD (Median Absolute Deviation)
    # This is robust to outliers and works with small sample sizes
    activity_counts = [
        min(r["unique_messages"], r["unique_users"] * 3) 
        for r in results
    ]
    
    if activity_counts:
        sorted_counts = sorted(activity_counts)
        median = sorted_counts[len(sorted_counts) // 2]
        
        deviations = sorted(abs(count - median) for count in activity_counts)
        mad = max(1.0, deviations[len(deviations) // 2])
        
        for result, activity in zip(results, activity_counts):
            # Deviation from median (in MAD units)
            deviation_score = max(0.0, (activity - median) / mad)
            
            # Participation score (0-1): how many unique users engaged
            participation = min(result["unique_users"], 16) / 16.0
            
            # Excitement score (0-1): how many users showed excitement
            excitement = min(result["excited_users"], 5) / 5.0
            
            # Combined burst score (0-4 range)
            # Weights: deviation=0.55, participation=0.75, excitement=1.25
            score = (
                min(2.5, deviation_score * 0.55) +
                participation * 0.75 +
                excitement * 1.25
            )
            result["burst_score"] = round(min(4.0, score), 2)
    
    return results


def summarize_chat_activity(messages, start_time, duration):
    """Summarize chat activity for a single time window.
    
    Args:
        messages: List of chat messages
        start_time: Window start time in seconds
        duration: Window duration in seconds
        
    Returns:
        Dict with total_messages, unique_users, excited_users
    """
    end_time = start_time + duration
    window_msgs = [
        m for m in messages
        if start_time <= float(m.get("t", -1)) < end_time
    ]
    
    user_messages = {}
    for msg in window_msgs:
        user = str(msg.get("user", "")).strip() or "anon"
        text = str(msg.get("text", "")).strip()
        if text:
            user_messages.setdefault(user, set()).add(text.lower())
    
    excited_users = sum(
        1 for user, texts in user_messages.items()
        if any(is_excited_message(text) for text in texts)
    )
    
    return {
        "total_messages": len(window_msgs),
        "unique_users": len(user_messages),
        "excited_users": excited_users
    }
