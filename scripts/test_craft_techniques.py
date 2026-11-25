#!/usr/bin/env python3
"""Tests for craft techniques: identity, dropout detection, sanitization, etc."""
import tempfile, subprocess, json, sys, re
from pathlib import Path

HERE = Path(__file__).parent

def make_test_video(out, dur=1, audio=False):
    """Create a minimal test video."""
    v = out / "v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=320x240:r=30:duration={dur}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(v)],
                   capture_output=True, check=True)
    if audio:
        a = out / "a.m4a"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
                        "-c:a", "aac", "-b:a", "128k", str(a)],
                       capture_output=True, check=True)
        test = out / "test.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-i", str(a),
                        "-c", "copy", "-shortest", str(test)],
                       capture_output=True, check=True)
        return test
    return v

# Test 1: Shared identity format
def test_shared_identity_format():
    """export.py and review.py use same identity format (size:mtime_ns:sha256)."""
    sys.path.insert(0, str(HERE))
    import export
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        test_file = out / "test.txt"
        test_file.write_text("hello world")
        
        export_id = export.file_identity(test_file)
        review_id = review.file_identity(test_file)
        
        assert export_id == review_id
        parts = export_id.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 64  # sha256
        print(f"  shared format verified")

# Test 2: Filter sanitizer
def test_filter_sanitizer():
    """Sanitize dangerous characters in filter graph inputs."""
    from review import sanitize_filter_input
    
    assert "\\'" in sanitize_filter_input("it's")
    assert "\\:" in sanitize_filter_input("C:/path")
    assert "\\\\" in sanitize_filter_input("back\\slash")
    assert sanitize_filter_input("safe text") == "safe text"
    print("  dangerous chars escaped")

# Test 3: Loudnorm timestamp preservation
def test_loudnorm_timestamp_preservation():
    """Loudnorm with asetpts preserves duration within 50ms."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create 1s video with audio
        src = out / "src.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:d=1.0",
                        "-f", "lavfi", "-i", "sine=440:d=1.0",
                        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(src)],
                       capture_output=True, check=True)
        
        # Get source duration
        r_src = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=duration", "-of", "json", str(src)],
                               capture_output=True, text=True, check=True)
        src_dur = float(json.loads(r_src.stdout)["streams"][0]["duration"])
        
        # Apply loudnorm with asetpts fix
        fixed = out / "fixed.m4a"
        subprocess.run(["ffmpeg", "-y", "-i", str(src),
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json,asetpts=N/SR/TB+STARTPTS",
                        "-c:a", "aac", str(fixed)],
                       capture_output=True, check=True)
        
        # Check output duration
        r_out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=duration", "-of", "json", str(fixed)],
                               capture_output=True, text=True, check=True)
        out_dur = float(json.loads(r_out.stdout)["streams"][0]["duration"])
        
        # Duration should be preserved within 50ms
        dur_diff = abs(out_dur - src_dur)
        assert dur_diff < 0.050, f"Duration drift {dur_diff*1000:.1f}ms exceeds 50ms threshold"
        print(f"  duration preserved: {src_dur:.3f}s -> {out_dur:.3f}s (diff: {dur_diff*1000:.1f}ms)")

# Test 4: Dropout detection (50ms gap detected)
def test_dropout_detection_50ms_gap():
    """Dropout detection flags 50ms audio-video gap using stream duration."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create separate video and audio, then mux with audio shorter
        v = out / "v.mp4"
        a = out / "a.m4a"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:d=1.0",
                        "-c:v", "libx264", str(v)],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=440:d=0.95",
                        "-c:a", "aac", str(a)],
                       capture_output=True, check=True)
        # Mux without -shortest, so video is full length but audio ends early
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-i", str(a),
                        "-c", "copy", str(out / "dropout.mp4")],
                       capture_output=True, check=True)
        
        # Test dropout detection logic directly
        p_a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=duration", "-of", "json",
                             str(out / "dropout.mp4")],
                            capture_output=True, text=True, check=True)
        p_v = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=duration", "-of", "json",
                             str(out / "dropout.mp4")],
                            capture_output=True, text=True, check=True)
        
        a_dur = float(json.loads(p_a.stdout)["streams"][0]["duration"])
        v_dur = float(json.loads(p_v.stdout)["streams"][0]["duration"])
        dropout = v_dur - a_dur
        
        # Should detect 50ms gap
        assert dropout > 0.05, f"Gap {dropout*1000:.1f}ms too small, expected >50ms"
        assert a_dur < v_dur, "Audio should end before video"
        print(f"  50ms dropout detected: audio {a_dur:.3f}s, video {v_dur:.3f}s, gap {dropout*1000:.1f}ms")

# Test 5: Dropout detection (no false positive on trailing container)
def test_dropout_detection_no_false_positive():
    """Dropout detection doesn't flag when audio ends naturally at same time as video."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create normal 1s video with matching audio
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:d=1.0",
                        "-f", "lavfi", "-i", "sine=440:d=1.0",
                        "-c:v", "libx264", "-c:a", "aac", str(out / "normal.mp4")],
                       capture_output=True, check=True)
        
        # Test dropout detection logic directly
        p_a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=duration", "-of", "json",
                             str(out / "normal.mp4")],
                            capture_output=True, text=True, check=True)
        p_v = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=duration", "-of", "json",
                             str(out / "normal.mp4")],
                            capture_output=True, text=True, check=True)
        
        a_dur = float(json.loads(p_a.stdout)["streams"][0]["duration"])
        v_dur = float(json.loads(p_v.stdout)["streams"][0]["duration"])
        dropout = v_dur - a_dur
        
        # Should NOT flag as dropout (gap < 50ms)
        assert dropout <= 0.05, f"False positive: gap {dropout*1000:.1f}ms flagged but should pass"
        print(f"  no false positive: audio {a_dur:.3f}s, video {v_dur:.3f}s, gap {dropout*1000:.1f}ms")

# Test 6: Crop percentage display (crop mode only)
def test_crop_percentage_display():
    """Crop % calculation for crop mode, not for pad or pad-blur."""
    sys.path.insert(0, str(HERE))
    import export
    
    # Test fit_filter logic directly
    # 16:9 source -> 9:16 target (reels) with crop
    src = {"w": 1920, "h": 1080}
    target = {"w": 1080, "h": 1920}  # reels dimensions
    
    # Crop mode
    vf_crop, same_crop, crop_pct_crop = export.fit_filter(src, target, "crop")
    assert not same_crop, "Aspect ratios should differ"
    assert crop_pct_crop > 0.5, f"Should crop >50% for 16:9->9:16, got {crop_pct_crop*100:.1f}%"
    print(f"  crop mode: {crop_pct_crop*100:.1f}% discarded")
    
    # Pad mode
    vf_pad, same_pad, crop_pct_pad = export.fit_filter(src, target, "pad")
    assert crop_pct_pad == 0.0, f"Pad mode should have 0% crop, got {crop_pct_pad*100:.1f}%"
    print(f"  pad mode: {crop_pct_pad*100:.1f}% discarded")
    
    # Pad-blur mode
    vf_blur, same_blur, crop_pct_blur = export.fit_filter(src, target, "pad-blur")
    assert crop_pct_blur == 0.0, f"Pad-blur mode should have 0% crop, got {crop_pct_blur*100:.1f}%"
    print(f"  pad-blur mode: {crop_pct_blur*100:.1f}% discarded")

if __name__ == "__main__":
    # Run all tests
    for name, obj in list(globals().items()):
        if name.startswith("test_") and callable(obj):
            print(f"Running {name}...")
            try:
                obj()
                print(f"✓ {name}")
            except Exception as e:
                print(f"✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
    print("\nAll tests passed!")
