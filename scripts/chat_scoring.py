#!/usr/bin/env python3
"""Chat activity analysis for stream highlight detection.

Uses rolling z-score spike detection over a trailing baseline to find engagement bursts.
Designed to resist spam by requiring diverse participation.
"""
import re
import math


# Engagement keywords: reactions, clip requests, excitement
ENGAGEMENT_KEYWORDS = {
    "clip", "wow", "omg", "lol", "nice", "hype", "epic", "insane", "crazy"
}

# Twitch emote patterns (case-insensitive substring match)
EMOTE_PATTERNS = ["pog", "kek", "monka", "pepe", "lul"]

# Emoji reactions
REACTION_EMOJI = re.compile(r"[😂🤣💀😱😮🔥👏]")


def has_engagement_markers(text):
    """Check if message contains engagement markers (keywords, emotes, emojis)."""
    lower = text.lower()
    
    # Keywords
    if any(kw in lower for kw in ENGAGEMENT_KEYWORDS):
        return True
    
    # Emotes
    if any(emote in lower for emote in EMOTE_PATTERNS):
        return True
    
    # Emojis
    if REACTION_EMOJI.search(text):
        return True
    
    return False


def analyze_chat_bursts(messages, window_starts, window_duration):
    """Detect chat engagement bursts using rolling z-score spike analysis.
    
    Approach:
    - Compute message rate (unique chatters per window)
    - Use trailing 3-window baseline to detect spikes via z-score
    - Require minimum diversity (chatter-to-message ratio)
    - Boost score for engagement markers
    
    Args:
        messages: List of dicts with t (timestamp), user, text keys
        window_starts: Start times to analyze (seconds)
        window_duration: Window size in seconds
        
    Returns:
        List of dicts with start, burst_score, peak_time, stats
    """
    # Step 1: Compute per-window metrics
    window_metrics = []
    
    for start in window_starts:
        end = start + window_duration
        
        # Filter messages in window
        window_msgs = [m for m in messages if start <= float(m.get("t", -1)) < end]
        
        # Group by user, track unique messages per user
        user_texts = {}
        engagement_count = 0
        sub_buckets = {}  # 10-second sub-buckets for peak detection
        
        for msg in window_msgs:
            user = str(msg.get("user", "")).strip() or "anon"
            text = str(msg.get("text", "")).strip()
            
            if not text:
                continue
            
            # Track unique messages per user (spam resistance)
            user_texts.setdefault(user, set()).add(text.lower())
            
            # Count engagement markers
            if has_engagement_markers(text):
                engagement_count += 1
            
            # Sub-buckets (10s intervals) for peak timing
            bucket = int((float(msg["t"]) - start) / 10.0)
            sub_buckets.setdefault(bucket, set()).add(user)
        
        unique_users = len(user_texts)
        total_messages = len(window_msgs)
        
        # Diversity ratio: unique users / total messages
        # High ratio = many different people talking (good)
        # Low ratio = few people spamming (bad)
        diversity = unique_users / max(1, total_messages)  # 0.8 = diverse, 0.1 = spam
        
        # Engagement density: messages with engagement markers / total
        engagement_density = engagement_count / max(1, total_messages)
        
        # Find peak sub-bucket for timing
        if sub_buckets:
            peak_bucket = max(sub_buckets.items(), key=lambda x: len(x[1]))[0]
            peak_time = start + peak_bucket * 10.0 + 5.0  # Middle of 10s bucket
        else:
            peak_time = start + window_duration / 2
        
        window_metrics.append({
            "start": float(start),
            "unique_users": unique_users,
            "total_messages": total_messages,
            "diversity": diversity,
            "engagement_density": engagement_density,
            "peak_time": float(peak_time),
            "burst_score": 0.0  # Computed in step 2
        })
    
    # Step 2: Compute rolling z-score for spike detection
    # Use trailing 3-window baseline (avoids contamination from current spike)
    baseline_size = 3  # Previous 3 windows as baseline
    
    for i, metrics in enumerate(window_metrics):
        # Baseline: previous 3 windows (or fewer if near start)
        baseline_start = max(0, i - baseline_size)
        baseline_windows = window_metrics[baseline_start:i]
        
        if not baseline_windows:
            # First window: no baseline, use default score
            z_score = 0.0
        else:
            # Compute mean and stddev of baseline unique_users
            baseline_users = [w["unique_users"] for w in baseline_windows]
            mean = sum(baseline_users) / len(baseline_users)
            
            # Standard deviation (with Bessel correction)
            if len(baseline_users) > 1:
                variance = sum((x - mean) ** 2 for x in baseline_users) / (len(baseline_users) - 1)
                stddev = math.sqrt(variance)
            else:
                stddev = 1.0
            
            # Z-score: how many standard deviations above baseline
            stddev = max(0.5, stddev)  # Floor at 0.5 to avoid div-by-zero
            z_score = (metrics["unique_users"] - mean) / stddev
            z_score = max(0.0, z_score)  # Clamp negative (below-baseline not interesting)
        
        # Score components with rationale:
        
        # 1. Spike intensity (z-score): 0-2.0 range
        #    Rationale: 2 std devs above baseline = strong spike
        #    Weight: 1.0 (primary signal)
        spike_component = min(2.0, z_score * 1.0)
        
        # 2. Diversity requirement: 0-1.0 range
        #    Rationale: diversity > 0.3 = healthy, < 0.1 = spam
        #    Weight: 1.5 (essential for spam resistance)
        #    Sigmoid scaling: low diversity heavily penalizes
        diversity_component = min(1.0, metrics["diversity"] / 0.3) * 1.5
        
        # 3. Engagement markers: 0-0.8 range
        #    Rationale: 20% of messages with engagement = strong
        #    Weight: 0.8 (bonus for excited chat)
        engagement_component = min(0.8, metrics["engagement_density"] / 0.2) * 0.8
        
        # Final score: sum of weighted components
        # Max theoretical: 2.0 + 1.5 + 0.8 = 4.3, clamp to 4.0
        burst_score = spike_component + diversity_component + engagement_component
        metrics["burst_score"] = round(min(4.0, burst_score), 2)
    
    return window_metrics


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
