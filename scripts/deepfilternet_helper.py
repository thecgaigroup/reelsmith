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

def is_dialogue_allowed(audio_path, metadata=None):
    """Fail-closed: only explicitly dialogue-classified input is allowed.
    
    Args:
        audio_path: path to audio file
        metadata: optional dict with keys like 'is_dialogue', 'stem_type', 'audio_type'
    
    Returns:
        (allowed: bool, reason: str) - allowed is True only if explicitly dialogue
    """
    # Check metadata tags - must be explicitly marked as dialogue
    if metadata:
        if metadata.get("is_dialogue") is True or metadata.get("audio_type", "").lower() == "dialogue":
            # Explicitly allowed
            name_lower = Path(audio_path).stem.lower()
            # Double-check filename doesn't have music/vocal indicators
            if any(pattern in name_lower for pattern in ["vox", "vocal", "lead", "chorus", "backing", "bgm", "stem", "music", "song", "inst"]):
                return False, f"metadata says dialogue but filename has music/vocal indicator"
            return True, None
        
        # Check for explicit music/vocal tags
        if metadata.get("is_vocal") or metadata.get("is_music"):
            return False, "metadata indicates vocal or music"
        stem_type = metadata.get("stem_type", "").lower()
        if stem_type in ("vocals", "music", "instrumental", "accompaniment"):
            return False, f"stem_type is {stem_type}"
    
    # Check filename patterns - refuse anything with music/vocal indicators
    name_lower = Path(audio_path).stem.lower()
    refused_patterns = ["vox", "vocal", "lead", "chorus", "backing", "bgm", "stem", "music", "song", "inst"]
    
    for pattern in refused_patterns:
        if pattern in name_lower:
            return False, f"filename contains '{pattern}' (not explicitly dialogue)"
    
    # Fail closed: unclassified = refused
    return False, "not explicitly classified as dialogue"

def denoise_dialogue(input_path, output_path, metadata=None):
    """Run DeepFilterNet on dialogue audio only. Fail-closed: only explicitly dialogue-classified input allowed.
    
    Args:
        input_path: input audio file (must be 48 kHz wav for deep-filter)
        output_path: output audio file
        metadata: optional metadata dict for dialogue classification
    
    Returns:
        {"success": bool, "error": str|None, "skipped": str|None, "refused": str|None}
    """
    if not is_available():
        return {"success": False, "error": None, "skipped": "deep-filter binary not available", "refused": None}
    
    # Enforce: fail closed - only explicitly dialogue-classified input is allowed
    allowed, reason = is_dialogue_allowed(input_path, metadata)
    if not allowed:
        return {"success": False, "error": None, "skipped": None, 
               "refused": f"refused: {reason} (DeepFilterNet requires explicit dialogue classification)"}
    
    # Check input format (deep-filter requires 48 kHz wav)
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Run deep-filter with --compensate-delay
    # Stage output in private temp dir to avoid overwriting source when input is in output folder
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # deep-filter writes to output_dir with input basename
            r = subprocess.run(["deep-filter", "--compensate-delay", str(input_path), "-o", str(tmpdir_path)],
                              capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return {"success": False, "error": f"deep-filter failed: {r.stderr[:200]}", 
                       "skipped": None, "refused": None}
            
            # Move staged output to final destination
            staged = tmpdir_path / input_path.name
            if not staged.exists():
                return {"success": False, "error": "deep-filter completed but output file not found in temp dir",
                       "skipped": None, "refused": None}
            
            shutil.move(str(staged), str(output_path))
        
        return {"success": True, "error": None, "skipped": None, "refused": None}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "deep-filter timeout (>5 min)", "skipped": None, "refused": None}
    except Exception as e:
        return {"success": False, "error": f"deep-filter exception: {str(e)[:200]}", 
               "skipped": None, "refused": None}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: deepfilternet_helper.py INPUT.wav OUTPUT.wav")
        sys.exit(1)
    
    result = denoise_dialogue(sys.argv[1], sys.argv[2])
    
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
