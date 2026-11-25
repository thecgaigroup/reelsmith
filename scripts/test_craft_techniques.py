#!/usr/bin/env python3
"""Tests for craft techniques: dropout detection, sanitization, loudnorm, etc.
All tests use real code paths (review.check, master_audio, etc)."""
import tempfile, subprocess, json, sys, re
from pathlib import Path

HERE = Path(__file__).parent

def make_test_video(out, dur=1, audio=False, audio_dur=None):
    """Create a minimal test video."""
    v = out / "v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=1080x1920:r=30:duration={dur}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(v)],
                   capture_output=True, check=True)
    if audio:
        a_dur = audio_dur if audio_dur is not None else dur
        a = out / "a.m4a"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={a_dur}",
                        "-c:a", "aac", "-b:a", "128k", str(a)],
                       capture_output=True, check=True)
        test = out / "test.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-i", str(a),
                        "-c", "copy", str(test)],
                       capture_output=True, check=True)
        return test
    return v

# Test 1: Filter sanitizer in scene drawtext
def test_filter_sanitizer_scene_drawtext():
    """Scene ids with dangerous chars render through real review drawtext without ffmpeg error."""
    sys.path.insert(0, str(HERE))
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create test video
        video = make_test_video(out, dur=2.0, audio=True)
        
        # Create job with scene id containing dangerous characters
        job_file = out / "job.json"
        job = {
            "scenes": [
                {"id": "Chapter: recap", "start": 0.0, "dur": 1.0},
                {"id": "Scene's \"outro\"", "start": 1.0, "dur": 1.0}
            ],
            "total_seconds": 2.0
        }
        job_file.write_text(json.dumps(job))
        
        # Resolve a real font file (required, no skip)
        font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if not Path(font).exists():
            # Try fc-match
            fc_result = subprocess.run(["fc-match", "-f", "%{file}", "sans"],
                                      capture_output=True, text=True)
            if fc_result.returncode == 0 and fc_result.stdout.strip():
                font = fc_result.stdout.strip()
            else:
                font = None
        
        if font is None or not Path(font).exists():
            raise AssertionError("No font file found (tried DejaVu and fc-match sans). Cannot test drawtext.")
        
        print(f"  using font: {font}")
        
        # Test that drawtext runs without error on dangerous scene ids
        # Extract one frame WITH label
        review_dir = out / "review"
        review_dir.mkdir()
        
        # Run scene_frames with the sanitizer
        review.scene_frames(video, job, review_dir, font, vertical=True)
        
        # Verify scenes.jpg was created (proves drawtext ran)
        scenes_jpg = review_dir / "scenes.jpg"
        assert scenes_jpg.exists(), "scenes.jpg not created - drawtext may not have run"
        
        # Also test individual frame with dangerous chars to verify ffmpeg exit code
        test_out = out / "test_frame.jpg"
        scene_text = review.sanitize_filter_input("1 Chapter: recap")
        lab = f",drawtext=fontfile='{font}':text='{scene_text}':x=8:y=h-th-8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7"
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", str(video),
                           "-frames:v", "1", "-vf", f"scale=270:-2{lab}", str(test_out)],
                          capture_output=True, text=True)
        
        assert r.returncode == 0, f"ffmpeg failed with sanitized text: {r.stderr}"
        assert test_out.exists(), "Output frame not created"
        
        print(f"  scene ids with : and \" rendered without error")

# Test 2: Dropout detection via real review.check (50ms gap)
def test_dropout_detection_real_check_50ms():
    """Real review.check detects 50ms audio dropout."""
    sys.path.insert(0, str(HERE))
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create video with audio ending 50ms early
        video = make_test_video(out, dur=1.0, audio=True, audio_dur=0.95)
        
        # Run real review.check
        review_dir = out / "review"
        review_dir.mkdir()
        result = review.check(video, review_dir, preset="reels")
        
        # Check for dropout warning in results
        dropout_check = next((r for r in result["rows"] if "dropout" in r["check"]), None)
        assert dropout_check is not None, "Dropout check not found in results"
        assert dropout_check["level"] == "WARN", f"Expected WARN, got {dropout_check['level']}"
        assert "audio ends" in dropout_check["detail"] or "before video" in dropout_check["detail"], \
            f"Detail doesn't mention audio ending early: {dropout_check['detail']}"
        print(f"  50ms dropout detected via review.check")

# Test 3: Dropout detection no false positive
def test_dropout_detection_no_false_positive():
    """Real review.check doesn't flag when audio matches video duration."""
    sys.path.insert(0, str(HERE))
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create normal video
        video = make_test_video(out, dur=1.0, audio=True)
        
        # Run real review.check
        review_dir = out / "review"
        review_dir.mkdir()
        result = review.check(video, review_dir, preset="reels")
        
        # Check dropout is PASS
        dropout_check = next((r for r in result["rows"] if "dropout" in r["check"]), None)
        assert dropout_check is not None, "Dropout check not found"
        assert dropout_check["level"] == "PASS", f"False positive: {dropout_check}"
        print(f"  no false positive on normal video")

# Test 4: Interior silent hole detection
def test_interior_silent_hole_detection():
    """Detect silent gaps in the middle of audio, not just at the end."""
    sys.path.insert(0, str(HERE))
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create audio with silent gap in middle: 0.5s tone, 2.5s silence, 0.5s tone
        a1 = out / "a1.wav"
        a2 = out / "a2.wav"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=440:d=0.5",
                        "-c:a", "pcm_s16le", str(a1)],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=440:d=0.5",
                        "-c:a", "pcm_s16le", str(a2)],
                       capture_output=True, check=True)
        
        # Concat with silence in middle
        audio_file = out / "audio.m4a"
        subprocess.run(["ffmpeg", "-y",
                        "-i", str(a1), "-f", "lavfi", "-i", "anullsrc=r=48000:d=2.5",
                        "-i", str(a2),
                        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1",
                        "-c:a", "aac", str(audio_file)],
                       capture_output=True, check=True)
        
        # Create video
        v = out / "v.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=30:d=3.5",
                        "-c:v", "libx264", str(v)],
                       capture_output=True, check=True)
        
        # Mux
        video = out / "test.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-i", str(audio_file),
                        "-c", "copy", str(video)],
                       capture_output=True, check=True)
        
        # Run review.check
        review_dir = out / "review"
        review_dir.mkdir()
        result = review.check(video, review_dir, preset="reels")
        
        # Check for interior silence warning
        silence_check = next((r for r in result["rows"] if "silence" in r["check"]), None)
        assert silence_check is not None, "Silence check not found"
        assert silence_check["level"] == "WARN", f"Expected WARN for 2.5s hole, got {silence_check['level']}"
        print(f"  interior 2.5s silent hole detected")

# Test 5: Loudnorm timestamp preservation via real master_audio
def test_loudnorm_real_master_audio():
    """Real master_audio preserves duration within 50ms with asetpts fix."""
    sys.path.insert(0, str(HERE))
    import export
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create 1s test audio
        src = out / "src.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=440:d=1.0",
                        "-c:a", "aac", str(src)],
                       capture_output=True, check=True)
        
        # Get source duration
        r_src = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=duration", "-of", "json", str(src)],
                               capture_output=True, text=True, check=True)
        src_dur = float(json.loads(r_src.stdout)["streams"][0]["duration"])
        
        # Run real master_audio
        output = out / "mastered.m4a"
        export.master_audio(src, output, lufs=-14.0)
        
        # Check output duration
        r_out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=duration", "-of", "json", str(output)],
                               capture_output=True, text=True, check=True)
        out_dur = float(json.loads(r_out.stdout)["streams"][0]["duration"])
        
        # Duration should be preserved within 50ms
        dur_diff = abs(out_dur - src_dur)
        assert dur_diff < 0.050, f"Duration drift {dur_diff*1000:.1f}ms exceeds 50ms threshold"
        print(f"  duration preserved via real master_audio: {src_dur:.3f}s -> {out_dur:.3f}s (diff: {dur_diff*1000:.1f}ms)")

# Test 6: Crop percentage display
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
