#!/usr/bin/env python3
"""Highlight detection for long-form videos using transcript + audio energy heuristics.

  highlights.py detect VIDEO --transcript words.json --out highlights.json [--min-clip 10] [--max-clip 60]
              [--top-n 5] [--audio-weight 0.3] [--overlap-threshold 0.5]
  
  # Stream-highlights mode with chat and speech fallback:
  highlights.py detect VIDEO --out highlights.json --mode stream [--chat chat.json] [--speech-fallback]
              [--min-clip 10] [--max-clip 60] [--top-n 5]

Scoring methods:
1. DEFAULT mode: Speech pacing + punctuation + audio energy
2. STREAM mode: Chat bursts (priority 1) > RMS loudness (priority 2) > speech-lexicon (priority 3, optional)

No LLM required ($0). words.json format same as captions.py: [{"text": "word", "start": 1.2, "end": 1.5}, ...]
chat.json format: [{"t": 10.5, "user": "username", "text": "message"}, ...]

Output highlights.json: [{"start": 10.5, "end": 25.3, "score": 0.85, "hook": "Why this matters",
                           "reason": "High energy, question hook, strong pacing", "duration": 14.8}, ...]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load_words(path):
    """Load word timings from captions.py format or hyperframes transcript.json."""
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("words") or data.get("segments") or data.get("captions") or []
    words = []
    for w in data:
        if "startMs" in w:
            s, e = w["startMs"] / 1000, w["endMs"] / 1000
        else:
            s, e = float(w.get("start", 0)), float(w.get("end", 0))
        t = (w.get("text") or w.get("word") or "").strip()
        if t:
            words.append({"text": t, "start": s, "end": max(e, s + 0.05)})
    return words

def extract_audio_energy(video_path, segment_duration=0.5):
    """Extract RMS energy per segment using ffmpeg volumedetect."""
    cmd = [
        "ffmpeg", "-i", str(video_path), "-af",
        f"asplit[a][b];[a]volumedetect[a1];[b]aformat=channel_layouts=mono,aresample=8000,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-[b1]",
        "-map", "[a1]", "-f", "null", "-",
        "-map", "[b1]", "-f", "null", "-"
    ]
    # Simpler approach: use ffmpeg to extract audio, then process with numpy if available
    # For $0 CPU-only, use ffmpeg astats to get RMS levels
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", str(video_path), "-af", "astats=metadata=1:reset=1", 
             "-f", "null", "-"],
            capture_output=True, text=True, stderr=subprocess.STDOUT
        )
        # Parse RMS levels from stderr (this is a simplified approach)
        # In practice, we'd need to extract frame-by-frame RMS
        # For now, return a simple energy profile based on audio stats
        return parse_audio_stats(result.stdout)
    except Exception as e:
        print(f"Warning: Could not extract audio energy: {e}", file=sys.stderr)
        return []

def parse_audio_stats(output):
    """Parse ffmpeg astats output to get RMS energy timeline."""
    # Simplified: return empty for now, will use word-based pacing instead
    # Full implementation would parse frame-by-frame RMS levels
    return []

def compute_audio_energy_simple(video_path, duration):
    """Compute simple audio energy profile using ffmpeg volumedetect on segments."""
    segments = []
    segment_size = 2.0  # 2-second windows
    num_segments = int(duration / segment_size) + 1
    
    for i in range(num_segments):
        start = i * segment_size
        end = min(start + segment_size, duration)
        # Extract segment and measure volume
        try:
            result = subprocess.run([
                "ffmpeg", "-ss", str(start), "-t", str(segment_size),
                "-i", str(video_path), "-af", "volumedetect",
                "-f", "null", "-"
            ], capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            # Parse mean volume from output
            match = re.search(r"mean_volume: ([-\d.]+) dB", result.stdout)
            if match:
                db = float(match.group(1))
                # Convert dB to 0-1 scale (assume -30dB to 0dB range)
                energy = max(0, min(1, (db + 30) / 30))
            else:
                energy = 0.5  # default
            segments.append({"start": start, "end": end, "energy": energy})
        except Exception:
            segments.append({"start": start, "end": end, "energy": 0.5})
    
    return segments

def score_text_content(text):
    """Score text for hook potential based on patterns."""
    score = 0.5  # base score
    
    # Questions are good hooks
    if re.search(r'\?', text):
        score += 0.15
    
    # Exclamations show energy
    if re.search(r'!', text):
        score += 0.1
    
    # Common hook words
    hook_words = r'\b(how|why|what|when|discover|learn|secret|amazing|incredible|never|always|best|worst)\b'
    matches = len(re.findall(hook_words, text.lower()))
    score += min(0.2, matches * 0.05)
    
    # Numbers often indicate value
    if re.search(r'\d+', text):
        score += 0.05
    
    return min(1.0, score)

def extract_hook_text(words, start_idx, max_words=8):
    """Extract hook text from the start of a segment."""
    hook_words = words[start_idx:start_idx + max_words]
    hook = " ".join(w["text"] for w in hook_words)
    # Capitalize first letter
    if hook:
        hook = hook[0].upper() + hook[1:] if len(hook) > 1 else hook.upper()
    # Trim to reasonable length
    if len(hook) > 60:
        hook = hook[:57] + "..."
    return hook

def compute_pacing_score(words, start_time, end_time):
    """Score based on speech pacing (words per second)."""
    segment_words = [w for w in words if start_time <= w["start"] < end_time]
    if not segment_words:
        return 0.3
    
    duration = end_time - start_time
    wps = len(segment_words) / max(0.1, duration)
    
    # Optimal pacing is 2-3 wps (2.5 is ideal per reelsmith scriptwriting)
    # Score peaks at 2.5 wps, drops off for too slow or too fast
    optimal = 2.5
    deviation = abs(wps - optimal) / optimal
    score = max(0.2, 1.0 - deviation)
    
    return min(1.0, score)

def find_sentence_boundaries(words):
    """Find sentence boundaries based on punctuation."""
    boundaries = [0]  # Start with first word
    for i, w in enumerate(words):
        if re.search(r'[.!?]$', w["text"]):
            if i + 1 < len(words):
                boundaries.append(i + 1)
    boundaries.append(len(words))  # End with last word
    return boundaries

def detect_highlights(video_path, words, min_clip=10, max_clip=60, top_n=5, 
                     audio_weight=0.3, overlap_threshold=0.5):
    """Detect highlight segments using transcript and audio energy."""
    
    if not words:
        return []
    
    # Get video duration
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ], capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    # Compute audio energy profile (simplified, $0 CPU-only)
    energy_segments = compute_audio_energy_simple(video_path, duration)
    
    # Find sentence boundaries for natural cuts
    boundaries = find_sentence_boundaries(words)
    
    # Generate candidate segments
    candidates = []
    for i in range(len(boundaries) - 1):
        start_idx = boundaries[i]
        
        # Try different end boundaries
        for j in range(i + 1, len(boundaries)):
            end_idx = boundaries[j]
            
            start_time = words[start_idx]["start"]
            end_time = words[end_idx - 1]["end"]
            clip_duration = end_time - start_time
            
            # Check duration constraints
            if clip_duration < min_clip or clip_duration > max_clip:
                continue
            
            # Extract segment text
            segment_text = " ".join(w["text"] for w in words[start_idx:end_idx])
            
            # Compute scores
            text_score = score_text_content(segment_text)
            pacing_score = compute_pacing_score(words, start_time, end_time)
            
            # Compute audio energy for this segment
            audio_score = 0.5
            relevant_energy = [e for e in energy_segments 
                             if not (e["end"] <= start_time or e["start"] >= end_time)]
            if relevant_energy:
                audio_score = sum(e["energy"] for e in relevant_energy) / len(relevant_energy)
            
            # Combine scores
            combined_score = (
                text_score * 0.4 +
                pacing_score * 0.3 +
                audio_score * audio_weight
            )
            
            # Extract hook
            hook = extract_hook_text(words, start_idx)
            
            # Generate reason
            reasons = []
            if text_score > 0.6:
                reasons.append("strong hook")
            if pacing_score > 0.7:
                reasons.append("good pacing")
            if audio_score > 0.6:
                reasons.append("high energy")
            if re.search(r'\?', segment_text):
                reasons.append("question hook")
            reason = ", ".join(reasons) if reasons else "balanced segment"
            reason = reason[0].upper() + reason[1:]
            
            candidates.append({
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "duration": round(clip_duration, 2),
                "score": round(combined_score, 3),
                "hook": hook,
                "reason": reason,
                "text_score": round(text_score, 3),
                "pacing_score": round(pacing_score, 3),
                "audio_score": round(audio_score, 3)
            })
    
    # Sort by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Remove overlapping segments (keep higher scoring ones)
    final = []
    for cand in candidates:
        # Check if it overlaps with any already selected segment
        overlaps = False
        for selected in final:
            overlap_start = max(cand["start"], selected["start"])
            overlap_end = min(cand["end"], selected["end"])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            min_duration = min(cand["duration"], selected["duration"])
            overlap_ratio = overlap_duration / min_duration if min_duration > 0 else 0
            
            if overlap_ratio > overlap_threshold:
                overlaps = True
                break
        
        if not overlaps:
            final.append(cand)
            if len(final) >= top_n:
                break
    
    # Sort final results by start time
    final.sort(key=lambda x: x["start"])
    
    return final

def detect_highlights_stream_mode(video_path, chat_messages, min_clip=10, max_clip=60, 
                                  top_n=5, speech_fallback=False, overlap_threshold=0.5):
    """Stream-highlights mode: chat bursts > RMS > speech-lexicon.
    
    Priority 1: Chat burst analysis (if chat_messages provided)
    Priority 2: RMS loudness (always available)
    Priority 3: Speech-lexicon via faster-whisper (if speech_fallback=True)
    
    Args:
        video_path: Path to video file
        chat_messages: List of chat messages with 't', 'user', 'text' keys (or None)
        min_clip: Minimum clip duration
        max_clip: Maximum clip duration
        top_n: Number of highlights to return
        speech_fallback: Enable faster-whisper speech-lexicon fallback
        overlap_threshold: Overlap ratio threshold for deduplication
        
    Returns:
        List of highlight dicts
    """
    # Get video duration
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ], capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    # Priority 1: Chat burst analysis
    if chat_messages and len(chat_messages) > 0:
        print(f"Using chat burst analysis ({len(chat_messages)} messages)", file=sys.stderr)
        
        # Import chat_scoring
        sys.path.insert(0, str(HERE))
        from chat_scoring import analyze_chat_bursts
        
        # Generate window starts (every 5 seconds)
        window_starts = list(range(0, int(duration - max_clip + 1), 5))
        
        # Analyze chat bursts
        chat_windows = analyze_chat_bursts(chat_messages, window_starts, max_clip)
        
        # Convert to highlights format, keeping top scorers
        candidates = []
        for window in chat_windows:
            if window["burst_score"] < 0.5:  # Minimum threshold
                continue
            
            # Use peak_time from chat analysis as the hook moment
            start = max(0, window["peak_time"] - 6.0)  # 6s lead-in
            start = min(start, duration - min_clip)
            end = min(start + max_clip, duration)
            
            if end - start < min_clip:
                continue
            
            # Extract hook from window start
            hook = f"Chat burst at {int(window['start'])}s"
            reason = f"Chat: {window['unique_users']} users, engagement={window['engagement_density']:.2f}"
            
            candidates.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "duration": round(end - start, 2),
                "score": round(window["burst_score"], 3),
                "hook": hook,
                "reason": reason,
                "method": "chat-burst"
            })
        
        # If we have good chat signals, use them
        if len(candidates) >= top_n:
            return finalize_highlights(candidates, top_n, overlap_threshold)
        
        print(f"Chat analysis found {len(candidates)} candidates, falling back to RMS", file=sys.stderr)
    
    # Priority 2: RMS loudness analysis (always available)
    print("Using RMS loudness analysis", file=sys.stderr)
    energy_segments = compute_audio_energy_simple(video_path, duration)
    
    # Generate candidate windows
    candidates = []
    for start in range(0, int(duration - min_clip + 1), 5):
        end = min(start + max_clip, duration)
        if end - start < min_clip:
            continue
        
        # Compute RMS energy for this window
        relevant_energy = [e for e in energy_segments 
                          if not (e["end"] <= start or e["start"] >= end)]
        if relevant_energy:
            avg_energy = sum(e["energy"] for e in relevant_energy) / len(relevant_energy)
        else:
            avg_energy = 0.5
        
        # Simple scoring: energy is the main signal
        score = avg_energy
        
        if score < 0.4:  # Minimum threshold
            continue
        
        candidates.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 2),
            "score": round(score, 3),
            "hook": f"High energy at {start}s",
            "reason": f"RMS energy: {avg_energy:.2f}",
            "method": "rms-loudness"
        })
    
    # If we have enough RMS candidates, use them
    if len(candidates) >= top_n or not speech_fallback:
        return finalize_highlights(candidates, top_n, overlap_threshold)
    
    # Priority 3: Speech-lexicon fallback (optional, requires faster-whisper)
    if speech_fallback:
        print("Attempting speech-lexicon fallback (faster-whisper)", file=sys.stderr)
        try:
            from faster_whisper import WhisperModel
            # TODO: Implement speech-lexicon scoring
            # This would transcribe audio and score based on speech patterns
            print("Speech-lexicon not yet implemented, using RMS results", file=sys.stderr)
        except ImportError:
            print("faster-whisper not available, using RMS results", file=sys.stderr)
    
    return finalize_highlights(candidates, top_n, overlap_threshold)


def finalize_highlights(candidates, top_n, overlap_threshold):
    """Sort, deduplicate and return top N highlights."""
    # Sort by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Remove overlapping segments (keep higher scoring ones)
    final = []
    for cand in candidates:
        overlaps = False
        for selected in final:
            overlap_start = max(cand["start"], selected["start"])
            overlap_end = min(cand["end"], selected["end"])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            min_duration = min(cand["duration"], selected["duration"])
            overlap_ratio = overlap_duration / min_duration if min_duration > 0 else 0
            
            if overlap_ratio > overlap_threshold:
                overlaps = True
                break
        
        if not overlaps:
            final.append(cand)
            if len(final) >= top_n:
                break
    
    # Sort final results by start time
    final.sort(key=lambda x: x["start"])
    return final


def load_chat_messages(chat_path):
    """Load chat messages from JSON file.
    
    Supports formats:
    - [{"t": 10.5, "user": "name", "text": "message"}, ...]
    - [{"time": 10.5, "username": "name", "message": "text"}, ...]
    """
    data = json.loads(Path(chat_path).read_text())
    
    normalized = []
    for msg in data:
        # Normalize different formats
        time_val = msg.get("t") or msg.get("time") or msg.get("timestamp")
        user_val = msg.get("user") or msg.get("username") or msg.get("author")
        text_val = msg.get("text") or msg.get("message") or msg.get("content")
        
        if time_val is not None:
            normalized.append({
                "t": float(time_val),
                "user": str(user_val or "unknown"),
                "text": str(text_val or "")
            })
    
    return normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__, 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["detect"], help="Action to perform")
    parser.add_argument("video", help="Input video file")
    parser.add_argument("--transcript", help="Word timings JSON (captions.py format)")
    parser.add_argument("--out", required=True, help="Output highlights JSON")
    parser.add_argument("--mode", choices=["default", "stream"], default="default",
                       help="Detection mode: default (transcript-based) or stream (chat-burst)")
    parser.add_argument("--chat", help="Chat messages JSON for stream mode")
    parser.add_argument("--speech-fallback", action="store_true",
                       help="Enable faster-whisper speech-lexicon fallback (stream mode)")
    parser.add_argument("--min-clip", type=float, default=10, help="Minimum clip duration in seconds")
    parser.add_argument("--max-clip", type=float, default=60, help="Maximum clip duration in seconds")
    parser.add_argument("--top-n", type=int, default=5, help="Number of top highlights to extract")
    parser.add_argument("--audio-weight", type=float, default=0.3, 
                       help="Weight for audio energy in scoring (0-1, default mode only)")
    parser.add_argument("--overlap-threshold", type=float, default=0.5,
                       help="Maximum overlap ratio to keep both segments (0-1)")
    
    args = parser.parse_args()
    
    if args.action == "detect":
        print(f"Detecting highlights in {args.video}...", file=sys.stderr)
        print(f"Mode: {args.mode}", file=sys.stderr)
        
        if args.mode == "stream":
            # Stream mode: chat bursts > RMS > speech-lexicon
            chat_messages = None
            if args.chat:
                chat_messages = load_chat_messages(args.chat)
                print(f"Loaded {len(chat_messages)} chat messages", file=sys.stderr)
            
            highlights = detect_highlights_stream_mode(
                args.video,
                chat_messages,
                min_clip=args.min_clip,
                max_clip=args.max_clip,
                top_n=args.top_n,
                speech_fallback=args.speech_fallback,
                overlap_threshold=args.overlap_threshold
            )
        else:
            # Default mode: transcript-based
            if not args.transcript:
                print("Error: --transcript required for default mode", file=sys.stderr)
                sys.exit(1)
            
            words = load_words(args.transcript)
            if not words:
                print(f"Error: No words found in {args.transcript}", file=sys.stderr)
                sys.exit(1)
            
            print(f"Loaded {len(words)} words from transcript", file=sys.stderr)
            
            highlights = detect_highlights(
                args.video, words,
                min_clip=args.min_clip,
                max_clip=args.max_clip,
                top_n=args.top_n,
                audio_weight=args.audio_weight,
                overlap_threshold=args.overlap_threshold
            )
        
        Path(args.out).write_text(json.dumps(highlights, indent=2))
        print(f"Found {len(highlights)} highlights, saved to {args.out}", file=sys.stderr)
        
        # Print summary
        for i, h in enumerate(highlights, 1):
            print(f"{i}. [{h['start']:.1f}s - {h['end']:.1f}s] "
                  f"score={h['score']:.2f} \"{h['hook']}\"", file=sys.stderr)

if __name__ == "__main__":
    main()
