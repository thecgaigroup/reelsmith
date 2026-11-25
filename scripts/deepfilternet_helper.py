#!/usr/bin/env python3
"""DeepFilterNet dialogue-only denoise helper (optional dependency).

ENFORCED RULE: Never run on song vocals or music stems. This is speech enhancement only.
Skips cleanly when deep-filter binary is not available.
"""
import subprocess, sys
from pathlib import Path

def is_available():
    """Check if deep-filter binary is available."""
    try:
        r = subprocess.run(["deep-filter", "--help"], capture_output=True, timeout=2)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def is_music_or_vocal(audio_path, metadata=None):
    """Detect if input is song vocal or music stem. Returns True if it should be refused.
    
    Args:
        audio_path: path to audio file
        metadata: optional dict with keys like 'is_vocal', 'is_music', 'stem_type'
    
    Returns:
        (is_music_or_vocal: bool, reason: str)
    """
    # Check metadata tags first
    if metadata:
        if metadata.get("is_vocal") or metadata.get("is_music"):
            return True, "metadata indicates vocal or music"
        if metadata.get("stem_type") in ("vocals", "music", "instrumental", "accompaniment"):
            return True, f"stem_type is {metadata['stem_type']}"
    
    # Check filename patterns that indicate music/vocal stems
    name = Path(audio_path).stem.lower()
    music_indicators = ["vocal", "vocals", "stem", "music", "instrumental", "accompaniment", 
                       "melody", "harmony", "singing", "song"]
    
    for indicator in music_indicators:
        if indicator in name:
            return True, f"filename contains '{indicator}'"
    
    return False, None

def denoise_dialogue(input_path, output_path, metadata=None, force=False):
    """Run DeepFilterNet on dialogue audio only. Refuses music/vocal inputs unless force=True.
    
    Args:
        input_path: input audio file (must be 48 kHz wav for deep-filter)
        output_path: output audio file
        metadata: optional metadata dict for music/vocal detection
        force: bypass music/vocal refusal (use with extreme caution)
    
    Returns:
        {"success": bool, "error": str|None, "skipped": str|None, "refused": str|None}
    """
    if not is_available():
        return {"success": False, "error": None, "skipped": "deep-filter binary not available", "refused": None}
    
    # Enforce: never on music or vocals (unless explicit force override for testing)
    if not force:
        is_mus, reason = is_music_or_vocal(input_path, metadata)
        if is_mus:
            return {"success": False, "error": None, "skipped": None, 
                   "refused": f"refused to denoise music/vocal: {reason} (DeepFilterNet is dialogue-only)"}
    
    # Check input format (deep-filter requires 48 kHz wav)
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Run deep-filter with --compensate-delay
    try:
        r = subprocess.run(["deep-filter", "--compensate-delay", str(input_path), "-o", str(output_path.parent)],
                          capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return {"success": False, "error": f"deep-filter failed: {r.stderr[:200]}", 
                   "skipped": None, "refused": None}
        
        # deep-filter writes to output_dir with original name; may need to rename
        expected_out = output_path.parent / input_path.name
        if expected_out.exists() and expected_out != output_path:
            expected_out.rename(output_path)
        
        if not output_path.exists():
            return {"success": False, "error": "deep-filter completed but output file not found",
                   "skipped": None, "refused": None}
        
        return {"success": True, "error": None, "skipped": None, "refused": None}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "deep-filter timeout (>5 min)", "skipped": None, "refused": None}
    except Exception as e:
        return {"success": False, "error": f"deep-filter exception: {str(e)[:200]}", 
               "skipped": None, "refused": None}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: deepfilternet_helper.py INPUT.wav OUTPUT.wav [--force]")
        sys.exit(1)
    
    force = "--force" in sys.argv
    result = denoise_dialogue(sys.argv[1], sys.argv[2], force=force)
    
    if result["success"]:
        print(f"DeepFilterNet: {sys.argv[1]} -> {sys.argv[2]}")
        sys.exit(0)
    elif result["refused"]:
        print(f"REFUSED: {result['refused']}", file=sys.stderr)
        sys.exit(2)
    elif result["skipped"]:
        print(f"SKIPPED: {result['skipped']}", file=sys.stderr)
        sys.exit(3)
    else:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)
