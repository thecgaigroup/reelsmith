#!/usr/bin/env python3
"""PySceneDetect cut-map verifier helper (optional dependency).

Compares planned cut map against detected cuts within a tolerance.
Falls back to ffmpeg scene detection when PySceneDetect is unavailable.
"""
import json, re, subprocess, sys
from pathlib import Path

def is_available():
    """Check if scenedetect (PySceneDetect) is available."""
    try:
        r = subprocess.run(["scenedetect", "--version"], capture_output=True, timeout=2)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def detect_cuts_pyscenedetect(video_path, threshold=27.0):
    """Detect cuts using PySceneDetect. Returns list of frame numbers or error.
    
    Args:
        video_path: path to video file
        threshold: detection threshold (default 27.0 for ContentDetector)
    
    Returns:
        {"success": bool, "cuts": [frame_numbers], "error": str|None, "method": "pyscenedetect"}
    """
    try:
        # Run scenedetect and save to CSV
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            r = subprocess.run([
                "scenedetect", "-i", str(video_path),
                "detect-content", "-t", str(threshold),
                "list-scenes", "-o", tmpdir
            ], capture_output=True, text=True, timeout=120)
            
            if r.returncode != 0:
                return {"success": False, "cuts": [], "error": f"scenedetect failed: {r.stderr[:200]}", 
                       "method": "pyscenedetect"}
            
            # Find the CSV file
            csv_files = list(Path(tmpdir).glob("*-Scenes.csv"))
            if not csv_files:
                return {"success": False, "cuts": [], "error": "no scene CSV generated", 
                       "method": "pyscenedetect"}
            
            # Parse CSV (Start Frame column)
            cuts = []
            for line in csv_files[0].read_text().split("\n")[1:]:  # skip header
                if not line.strip():
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        cuts.append(int(parts[1]))  # Start Frame is column 1
                    except ValueError:
                        pass
            
            return {"success": True, "cuts": cuts, "error": None, "method": "pyscenedetect"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "cuts": [], "error": "scenedetect timeout", "method": "pyscenedetect"}
    except Exception as e:
        return {"success": False, "cuts": [], "error": str(e)[:200], "method": "pyscenedetect"}

def detect_cuts_ffmpeg(video_path, threshold=0.4):
    """Fallback: detect cuts using ffmpeg scene filter.
    
    Returns:
        {"success": bool, "cuts": [frame_numbers], "error": str|None, "method": "ffmpeg"}
    """
    try:
        # Get frame rate first
        r_probe = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate", "-of", "json", str(video_path)
        ], capture_output=True, text=True, timeout=10)
        
        fps_data = json.loads(r_probe.stdout)
        fps_str = fps_data["streams"][0]["r_frame_rate"]
        num, den = fps_str.split("/")
        fps = int(num) / int(den)
        
        # Run ffmpeg scene detection
        r = subprocess.run([
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(video_path),
            "-vf", f"select='gt(scene\\,{threshold})',showinfo", "-f", "null", "-"
        ], capture_output=True, text=True, timeout=120)
        
        # Parse frame numbers from showinfo output
        cuts = []
        for match in re.finditer(r"n:\s*(\d+)", r.stderr):
            cuts.append(int(match.group(1)))
        
        return {"success": True, "cuts": cuts, "error": None, "method": "ffmpeg"}
    
    except Exception as e:
        return {"success": False, "cuts": [], "error": str(e)[:200], "method": "ffmpeg"}

def verify_cut_map(video_path, expected_cuts, tolerance_frames=2):
    """Verify that expected cuts are detected within tolerance.
    
    Args:
        video_path: path to video file
        expected_cuts: list of expected frame numbers
        tolerance_frames: tolerance in frames (default 2)
    
    Returns:
        {"success": bool, "method": str, "matched": int, "missing": [...], 
         "extra": [...], "pass": bool, "report": str}
    """
    # Try PySceneDetect first, fall back to ffmpeg
    if is_available():
        result = detect_cuts_pyscenedetect(video_path)
    else:
        result = detect_cuts_ffmpeg(video_path)
    
    if not result["success"]:
        return {
            "success": False,
            "method": result.get("method", "unknown"),
            "matched": 0,
            "missing": expected_cuts,
            "extra": [],
            "pass": False,
            "report": f"cut detection failed: {result['error']}"
        }
    
    detected_cuts = result["cuts"]
    method = result["method"]
    
    # Match expected cuts to detected cuts within tolerance
    matched = []
    missing = []
    
    for expected in expected_cuts:
        found = False
        for detected in detected_cuts:
            if abs(expected - detected) <= tolerance_frames:
                matched.append((expected, detected))
                found = True
                break
        if not found:
            missing.append(expected)
    
    # Find extra cuts (detected but not expected)
    extra = []
    for detected in detected_cuts:
        found = False
        for expected in expected_cuts:
            if abs(expected - detected) <= tolerance_frames:
                found = True
                break
        if not found:
            extra.append(detected)
    
    # Pass criteria: all expected cuts found, few extras allowed
    pass_check = len(missing) == 0 and len(extra) <= len(expected_cuts) * 0.2
    
    report_lines = [
        f"Cut map verification (method: {method}):",
        f"  Expected cuts: {len(expected_cuts)}",
        f"  Detected cuts: {len(detected_cuts)}",
        f"  Matched (±{tolerance_frames} frames): {len(matched)}",
        f"  Missing: {len(missing)} {missing[:5] if missing else ''}",
        f"  Extra: {len(extra)} {extra[:5] if extra else ''}",
        f"  Result: {'PASS' if pass_check else 'WARN'}"
    ]
    
    return {
        "success": True,
        "method": method,
        "matched": len(matched),
        "missing": missing,
        "extra": extra,
        "pass": pass_check,
        "report": "\n".join(report_lines)
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: pyscenedetect_helper.py VIDEO CUTS.json [--tolerance N]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    cuts_json = sys.argv[2]
    tolerance = 2
    
    if "--tolerance" in sys.argv:
        idx = sys.argv.index("--tolerance")
        tolerance = int(sys.argv[idx + 1])
    
    # Read expected cuts
    expected_cuts = json.loads(Path(cuts_json).read_text())
    
    result = verify_cut_map(video_path, expected_cuts, tolerance)
    
    print(result["report"])
    sys.exit(0 if result["pass"] else 1)
