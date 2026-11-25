#!/usr/bin/env python3
"""WhisperX lyric-timing cross-check helper (optional dependency).

Report-only: official lyrics are the source of truth. Diarization off.
Never retimes audio. Skips cleanly when whisperx is not available.
"""
import json, sys
from pathlib import Path

def is_available():
    """Check if whisperx is available."""
    try:
        import whisperx
        return True
    except ImportError:
        return False

def cross_check_lyrics(audio_path, official_lyrics, language="en", device="cpu", compute_type="int8"):
    """Cross-check official lyrics against WhisperX word timing. Report-only, never retimes.
    
    Args:
        audio_path: path to audio file (vocal stem recommended)
        official_lyrics: list of official lyric tokens (words) in order
        language: language code (default "en")
        device: "cpu" or "cuda"
        compute_type: "int8", "float16", etc.
    
    Returns:
        {"success": bool, "skipped": str|None, "error": str|None,
         "matched_count": int, "missing_count": int, "extra_count": int,
         "report": str, "details": [...]}
    """
    if not is_available():
        return {"success": False, "skipped": "whisperx not available", "error": None,
               "matched_count": 0, "missing_count": 0, "extra_count": 0, "report": "", "details": []}
    
    try:
        import whisperx
        import torch
    except ImportError as e:
        return {"success": False, "skipped": f"whisperx import failed: {e}", "error": None,
               "matched_count": 0, "missing_count": 0, "extra_count": 0, "report": "", "details": []}
    
    try:
        # Load model
        model = whisperx.load_model("base", device=device, compute_type=compute_type, language=language)
        
        # Transcribe (diarization off as per requirement)
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, language=language)
        
        # Align for word timing - REQUIRED, not optional (fail if alignment fails)
        try:
            model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, device)
        except Exception as e:
            return {"success": False, "skipped": None, "error": f"alignment failed: {str(e)[:150]}",
                   "matched_count": 0, "missing_count": 0, "extra_count": 0, "report": "", "details": []}
        
        # Extract detected words WITH timing and order
        detected_words_timed = []
        for segment in result.get("segments", []):
            for word_obj in segment.get("words", []):
                word_text = word_obj.get("word", "").strip().lower()
                if word_text:
                    detected_words_timed.append({
                        "word": word_text,
                        "start": word_obj.get("start", 0.0),
                        "end": word_obj.get("end", 0.0)
                    })
        
        # Normalize official lyrics (order preserved)
        official_normalized = [w.strip().lower() for w in official_lyrics if w.strip()]
        detected_normalized = [w["word"] for w in detected_words_timed]
        
        # Compare order and repeated words (not just sets)
        # Use simple sequence alignment to match words in order
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, official_normalized, detected_normalized)
        matches = matcher.get_matching_blocks()
        
        matched_count = sum(m.size for m in matches if m.size > 0)
        
        # Find mismatches in order
        order_mismatches = []
        timing_issues = []
        
        # Simple linear pass to check order consistency
        official_idx = 0
        detected_idx = 0
        TIMING_TOLERANCE = 0.3  # 300ms tolerance for timing
        
        while official_idx < len(official_normalized) and detected_idx < len(detected_normalized):
            if official_normalized[official_idx] == detected_normalized[detected_idx]:
                # Match - advance both
                official_idx += 1
                detected_idx += 1
            else:
                # Mismatch in order
                order_mismatches.append(f"pos {official_idx}: expected '{official_normalized[official_idx]}', got '{detected_normalized[detected_idx]}'")
                detected_idx += 1
                if len(order_mismatches) >= 5:
                    break
        
        # Count repeated words
        from collections import Counter
        official_counts = Counter(official_normalized)
        detected_counts = Counter(detected_normalized)
        
        repeat_issues = []
        for word, official_count in official_counts.items():
            detected_count = detected_counts.get(word, 0)
            if detected_count != official_count:
                repeat_issues.append(f"'{word}': official {official_count}x, detected {detected_count}x")
        
        report_lines = [
            f"WhisperX cross-check (report-only, official lyrics are source of truth, diarization off):",
            f"  Official tokens: {len(official_normalized)}",
            f"  Detected tokens: {len(detected_normalized)}",
            f"  Matched in order: {matched_count}",
            f"  Order mismatches: {len(order_mismatches)} {order_mismatches[:3]}",
            f"  Repeat count issues: {len(repeat_issues)} {repeat_issues[:3]}",
        ]
        
        details = {
            "official": official_normalized,
            "detected": detected_normalized,
            "matched_count": matched_count,
            "order_mismatches": order_mismatches,
            "repeat_issues": repeat_issues,
            "detected_timed": detected_words_timed
        }
        
        return {
            "success": True,
            "skipped": None,
            "error": None,
            "matched_count": matched_count,
            "missing_count": len(official_normalized) - matched_count,
            "extra_count": len(detected_normalized) - matched_count,
            "report": "\n".join(report_lines),
            "details": details
        }
    
    except Exception as e:
        return {"success": False, "skipped": None, "error": f"whisperx exception: {str(e)[:200]}",
               "matched_count": 0, "missing_count": 0, "extra_count": 0, "report": "", "details": []}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: whisperx_helper.py AUDIO.wav LYRICS.txt")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    lyrics_path = sys.argv[2]
    
    # Read official lyrics
    official_lyrics = Path(lyrics_path).read_text().split()
    
    result = cross_check_lyrics(audio_path, official_lyrics)
    
    if result["success"]:
        print(result["report"])
        sys.exit(0)
    elif result["skipped"]:
        print(f"SKIPPED: {result['skipped']}", file=sys.stderr)
        sys.exit(3)
    else:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)
