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
        
        # Transcribe
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, language=language)
        
        # Align (optional, for better word timing)
        try:
            model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, device)
        except Exception:
            pass  # alignment optional
        
        # Extract detected words
        detected_words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                detected_words.append(word.get("word", "").strip().lower())
        
        # Normalize both lists
        official_normalized = [w.strip().lower() for w in official_lyrics if w.strip()]
        detected_normalized = [w for w in detected_words if w]
        
        # Simple sequence match (not edit distance, just presence check)
        matched = 0
        missing = []
        extra = []
        
        official_set = set(official_normalized)
        detected_set = set(detected_normalized)
        
        # Count matches
        matched = len(official_set & detected_set)
        missing = list(official_set - detected_set)
        extra = list(detected_set - official_set)
        
        report_lines = [
            f"WhisperX cross-check (report-only, official lyrics are source of truth):",
            f"  Official tokens: {len(official_normalized)}",
            f"  Detected tokens: {len(detected_normalized)}",
            f"  Matched (unique): {matched}",
            f"  Missing from detected: {len(missing)} ({', '.join(missing[:10])}{'...' if len(missing) > 10 else ''})",
            f"  Extra in detected: {len(extra)} ({', '.join(extra[:10])}{'...' if len(extra) > 10 else ''})",
        ]
        
        details = {
            "official": official_normalized,
            "detected": detected_normalized,
            "matched": list(official_set & detected_set),
            "missing": missing,
            "extra": extra
        }
        
        return {
            "success": True,
            "skipped": None,
            "error": None,
            "matched_count": matched,
            "missing_count": len(missing),
            "extra_count": len(extra),
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
