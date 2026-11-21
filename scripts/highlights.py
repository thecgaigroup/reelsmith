#!/usr/bin/env python3
"""Highlight detection for long-form videos using transcript + audio energy heuristics.

  highlights.py detect VIDEO --transcript words.json --out highlights.json [--min-clip 10] [--max-clip 60]
              [--top-n 5] [--audio-weight 0.3] [--overlap-threshold 0.5]

Scores segments based on:
1. Speech pacing and punctuation (hooks, questions, exclamations)
2. Audio energy (loud/dynamic moments)
3. Semantic boundaries (sentence/paragraph breaks)

No LLM required ($0). words.json format same as captions.py: [{"text": "word", "start": 1.2, "end": 1.5}, ...]

Output highlights.json: [{"start": 10.5, "end": 25.3, "score": 0.85, "hook": "Why this matters",
                           "reason": "High energy, question hook, strong pacing", "duration": 14.8}, ...]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

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

def main():
    parser = argparse.ArgumentParser(description=__doc__, 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["detect"], help="Action to perform")
    parser.add_argument("video", help="Input video file")
    parser.add_argument("--transcript", required=True, help="Word timings JSON (captions.py format)")
    parser.add_argument("--out", required=True, help="Output highlights JSON")
    parser.add_argument("--min-clip", type=float, default=10, help="Minimum clip duration in seconds")
    parser.add_argument("--max-clip", type=float, default=60, help="Maximum clip duration in seconds")
    parser.add_argument("--top-n", type=int, default=5, help="Number of top highlights to extract")
    parser.add_argument("--audio-weight", type=float, default=0.3, 
                       help="Weight for audio energy in scoring (0-1)")
    parser.add_argument("--overlap-threshold", type=float, default=0.5,
                       help="Maximum overlap ratio to keep both segments (0-1)")
    
    args = parser.parse_args()
    
    if args.action == "detect":
        words = load_words(args.transcript)
        if not words:
            print(f"Error: No words found in {args.transcript}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Detecting highlights in {args.video}...", file=sys.stderr)
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
