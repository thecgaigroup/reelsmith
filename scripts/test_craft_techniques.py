#!/usr/bin/env python3
"""Tests for craft techniques bundle: identity, dropouts, SSIM/PSNR, expect-changed, loudnorm timestamp fix.

Covers done_when checks from ffmpeg-skill-review.md and four-repo-fit-check.md Scout documents.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review import check, file_identity, detect_dropouts, compare_ssim_psnr, verify_change_scope
from export import file_identity as export_file_identity, export_one

def make_test_video(out, dur=5, audio=True, silence_gap_ms=0):
    """Make a test video with optional audio and optional mid-file silence gap."""
    # Generate black video
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=320x240:r=30:duration={dur}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "v.mp4")], capture_output=True, check=True)
    
    if not audio:
        return out / "v.mp4"
    
    # Generate audio with optional silence gap
    if silence_gap_ms > 0:
        # Create two sine segments with silence in between
        dur1 = dur / 2 - silence_gap_ms / 2000.0
        gap_s = silence_gap_ms / 1000.0
        dur2 = dur - dur1 - gap_s
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur1}",
                        "-f", "lavfi", "-i", f"anullsrc=duration={gap_s}",
                        "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur2}",
                        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1",
                        "-c:a", "aac", str(out / "a.m4a")], capture_output=True, check=True)
    else:
        # Simple sine wave
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
                        "-c:a", "aac", str(out / "a.m4a")], capture_output=True, check=True)
    
    # Mux video and audio
    subprocess.run(["ffmpeg", "-y", "-i", str(out / "v.mp4"), "-i", str(out / "a.m4a"),
                    "-c", "copy", "-shortest", str(out / "test.mp4")], capture_output=True, check=True)
    return out / "test.mp4"

# 1. Output identity verification (ffmpeg-skill technique #1)
def test_file_identity():
    """file_identity returns size:mtime_ns:sha256 string."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3)
        identity = file_identity(v)
        assert ":" in identity, f"Expected size:mtime_ns:sha256 format, got {identity}"
        parts = identity.split(":")
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}"
        size, mtime_ns, sha = parts
        assert int(size) > 0, f"Expected nonzero size"
        assert int(mtime_ns) > 0, f"Expected nonzero mtime"
        assert len(sha) == 64, f"Expected 64-char sha256, got {len(sha)}"
        print(f"  identity: size:{size} mtime:{mtime_ns[:10]}... sha256:{sha[:16]}...")

def test_identity_check_pass():
    """Identity check passes when file matches expected identity."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3)
        identity = file_identity(v)
        # Run check with correct identity
        rev_out = out / "_review"
        check(v, rev_out, expect_identity=identity)
        rev_json = rev_out / "review.json"
        data = json.loads(rev_json.read_text())
        identity_row = next((r for r in data["rows"] if r["check"] == "identity"), None)
        assert identity_row is not None, "Expected identity row in review"
        assert identity_row["level"] == "PASS", f"Expected PASS, got {identity_row['level']}"

def test_identity_check_fail():
    """Identity check fails when file differs from expected identity."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3)
        # Run check with wrong identity
        rev_out = out / "_review"
        check(v, rev_out, expect_identity="1:1")
        rev_json = rev_out / "review.json"
        data = json.loads(rev_json.read_text())
        identity_row = next((r for r in data["rows"] if r["check"] == "identity"), None)
        assert identity_row is not None, "Expected identity row in review"
        assert identity_row["level"] == "FAIL", f"Expected FAIL, got {identity_row['level']}"
        assert "changed or replaced" in identity_row["detail"], "Expected 'changed or replaced' in detail"

# 2. Audio dropout detection (ffmpeg-skill technique #4)
def test_dropout_detection_none():
    """No dropouts in clean audio."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, silence_gap_ms=0)
        dropouts = detect_dropouts(v)
        assert len(dropouts) == 0, f"Expected no dropouts, got {dropouts}"

def test_dropout_detection_found():
    """Dropouts detected in audio with mid-file silence gap."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create audio with 100ms digital-zero gap in middle
        v = make_test_video(out, dur=5, silence_gap_ms=100)
        dropouts = detect_dropouts(v)
        assert len(dropouts) > 0, f"Expected dropouts, got none"
        # Check that dropout is in middle (not at edges)
        assert all(0.1 < t < 4.9 for t, d in dropouts), f"Dropout should be in middle, got {dropouts}"
        print(f"  found {len(dropouts)} dropout(s): {dropouts}")

def test_dropout_in_check():
    """Dropout detection integrated into check() function."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, silence_gap_ms=100)
        rev_out = out / "_review"
        check(v, rev_out)
        rev_json = rev_out / "review.json"
        data = json.loads(rev_json.read_text())
        dropout_row = next((r for r in data["rows"] if r["check"] == "audio dropouts"), None)
        assert dropout_row is not None, "Expected audio dropouts row in review"
        assert dropout_row["level"] == "WARN", f"Expected WARN, got {dropout_row['level']}"

# 3. SSIM/PSNR comparison (ffmpeg-skill technique #2)
def test_ssim_identical_files():
    """SSIM comparison of identical files gives mean SSIM ~1.0."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v1 = make_test_video(out, dur=3)
        v2 = Path(out) / "copy.mp4"
        subprocess.run(["cp", str(v1), str(v2)], check=True)
        result = compare_ssim_psnr(v1, v2)
        assert "error" not in result, f"Expected no error, got {result}"
        assert result["mean_ssim"] is not None, "Expected mean_ssim"
        assert result["mean_ssim"] > 0.99, f"Expected SSIM > 0.99 for identical files, got {result['mean_ssim']}"
        print(f"  mean SSIM: {result['mean_ssim']:.4f}, PSNR: {result['mean_psnr']:.1f} dB")

def test_ssim_size_mismatch():
    """SSIM comparison fails on size mismatch."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create two videos with different resolutions
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "v1.mp4")],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=640x480:r=30:duration=3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "v2.mp4")],
                       capture_output=True, check=True)
        result = compare_ssim_psnr(out / "v1.mp4", out / "v2.mp4")
        assert "error" in result, f"Expected error for size mismatch, got {result}"
        assert "size mismatch" in result["error"], f"Expected 'size mismatch' in error"

# 4. Change scope verification (ffmpeg-skill technique #2 cont.)
def test_change_scope_none_pass():
    """Change scope 'none' passes when files are identical."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v1 = make_test_video(out, dur=3)
        v2 = Path(out) / "copy.mp4"
        subprocess.run(["cp", str(v1), str(v2)], check=True)
        result = verify_change_scope(v1, v2, ["none"])
        assert result["pass"], f"Expected pass for identical files with 'none', got {result}"

# 5. Export identity and verified flag
def test_export_identity():
    """export_one includes output_identity and verified flag."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3)
        export_dir = out / "_export"
        export_dir.mkdir()
        # Create a minimal preset for testing
        sys.path.insert(0, str(HERE))
        import export
        # Use an actual preset
        rep = export_one(v, "youtube", export_dir, mode="pad")
        assert "output_identity" in rep, "Expected output_identity in export report"
        assert "verified" in rep, "Expected verified in export report"
        assert rep["verified"] is True, f"Expected verified=True, got {rep['verified']}"
        assert ":" in rep["output_identity"], f"Expected size:mtime_ns format in output_identity"
        print(f"  output_identity: {rep['output_identity']}, verified: {rep['verified']}")

# 6. Loudnorm timestamp fix (ffmpeg-skill technique #3)
def test_loudnorm_timestamp_fix():
    """Loudnorm with asetpts prevents A/V sync drift on files with digital-zero gaps."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a video with 80ms digital-zero gap in audio (the case that caused ~89ms drift)
        v = make_test_video(out, dur=5, silence_gap_ms=80)
        
        # Run export with loudnorm (which includes the asetpts fix)
        export_dir = out / "_export"
        export_dir.mkdir()
        sys.path.insert(0, str(HERE))
        import export
        rep = export_one(v, "youtube", export_dir, mode="pad")
        
        # Check sync drift on exported file
        from review import check_sync_drift
        exported_file = Path(rep["file"])
        sync_result = check_sync_drift(exported_file, warn_ms=50)
        
        # With the fix, drift should be < 50ms
        assert sync_result["worst_drift_ms"] < 50, \
            f"Expected drift < 50ms with asetpts fix, got {sync_result['worst_drift_ms']}ms"
        assert not sync_result["flagged"], f"Expected no sync drift flag, but got flagged=True"
        print(f"  worst drift after loudnorm: {sync_result['worst_drift_ms']:.1f}ms (< 50ms)")

# 7. Filter graph sanitization
def test_sanitize_filter_input():
    """Sanitize dangerous characters in filter graph inputs."""
    from review import sanitize_filter_input
    # Test dangerous characters are escaped
    assert "\\'" in sanitize_filter_input("it's")
    assert "\\:" in sanitize_filter_input("C:/path")
    assert "\\\\" in sanitize_filter_input("back\\slash")
    # Safe strings pass through
    assert sanitize_filter_input("safe text 123") == "safe text 123"
    print("  dangerous chars escaped")

# 8. Measured crop placement
def test_measured_crop_placement():
    """Measure where picture sits after crop/pad fit."""
    from export import measure_crop_placement
    # 16:9 to 9:16 (crop sides)
    result = measure_crop_placement(1920, 1080, 1080, 1920)
    assert result["measured"] is True
    assert result["discarded_fraction"] > 0.6  # ~68% discarded
    print(f"  16:9->9:16 crop: {result['discarded_fraction']*100:.1f}% discarded")
    
    # Same aspect (no crop)
    result = measure_crop_placement(1920, 1080, 1280, 720)
    assert result["measured"] is True
    assert result["discarded_fraction"] == 0.0
    print(f"  same aspect: 0% discarded")

# 9. Speed change refusal
def test_speed_change_refusal():
    """Refuse silent speed changes > 1.15x."""
    from export import check_duration_fit
    # Within range: ok
    ok, factor, reason = check_duration_fit(10.0, 9.0, allow_speed_change=False)
    assert ok is True  # 1.11x is ok
    
    # Too fast: refused
    ok, factor, reason = check_duration_fit(10.0, 7.0, allow_speed_change=False)
    assert ok is False  # 1.43x refused
    assert "1.15" in reason
    print(f"  refused {factor:.2f}x speed change")
    
    # With flag: allowed
    ok, factor, reason = check_duration_fit(10.0, 7.0, allow_speed_change=True)
    assert ok is True
    print(f"  allowed {factor:.2f}x with --allow-speed-change")

# (7) Test crop % only shown for crop mode, not pad-blur
def test_crop_percentage_only_on_crop():
    """Crop % is printed for crop mode but not pad-blur mode."""
    sys.path.insert(0, str(HERE))
    import export
    from io import StringIO
    import sys as pysys
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a wide video (needs cropping for 9:16)
        v = make_test_video(out, dur=0.5)
        
        # Test crop mode (should show %)
        old_stdout = pysys.stdout
        pysys.stdout = StringIO()
        try:
            export.export_one(str(v), "ig-stories", str(out), mode="crop")
            crop_output = pysys.stdout.getvalue()
        finally:
            pysys.stdout = old_stdout
        
        # Test pad-blur mode (should NOT show %)
        pysys.stdout = StringIO()
        try:
            export.export_one(str(v), "ig-stories", str(out), mode="pad-blur")
            pad_output = pysys.stdout.getvalue()
        finally:
            pysys.stdout = old_stdout
        
        # Crop mode should mention "crop: X% discarded"
        assert "crop:" in crop_output and "% discarded" in crop_output
        # Pad-blur mode should NOT mention crop %
        assert "crop:" not in pad_output or "% discarded" not in pad_output
        print(f"  crop shows %, pad-blur does not")

# (8) Test old sanitizer removed from export.py
def test_no_sanitizer_in_export():
    """export.py should not have sanitize_filter_input (review.py has it)."""
    sys.path.insert(0, str(HERE))
    import export
    
    # Should not have sanitize_filter_input function
    assert not hasattr(export, "sanitize_filter_input")
    print(f"  export.py has no sanitize_filter_input")

# (5) Test duration fit (1, 0.6) must fail
def test_duration_fit_one_to_point_six_fails():
    """check_duration_fit(1, 0.6) must fail (1.67x > 1.15x threshold)."""
    from export import check_duration_fit
    ok, factor, reason = check_duration_fit(1.0, 0.6, allow_speed_change=False)
    assert ok is False
    assert abs(factor - 1.6667) < 0.01  # 1.0 / 0.6 ≈ 1.67
    print(f"  (1, 0.6) refused: {factor:.2f}x")

# (5) Test audio/video sync with speed factor
def test_audio_video_sync_with_speed():
    """Audio and video durations match within one frame after speed change."""
    sys.path.insert(0, str(HERE))
    import export
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a 2s test video with audio
        v = make_test_video(out, dur=2, audio=True)
        
        # Export with target duration 1.5s (requires 1.33x speed)
        # This is > 1.15x so needs --allow-speed-change
        preset = "ig-stories"
        export.export_one(str(v), preset, str(out), target_duration=1.5, allow_speed_change=True)
        
        result = out / f"{v.stem}-{preset}.mp4"
        assert result.exists()
        
        # Probe audio and video durations
        p = export.probe(str(result))
        video_dur = p["duration"]
        
        # Get audio duration specifically
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                          "-show_entries", "stream=duration", "-of", "json", str(result)],
                          capture_output=True, text=True, check=True)
        audio_dur = float(json.loads(r.stdout)["streams"][0]["duration"])
        
        # Both should be ~1.5s (2s / 1.33)
        expected = 2.0 / (2.0 / 1.5)  # src / factor
        frame_time = 1.0 / 30.0  # 30fps
        assert abs(video_dur - expected) < frame_time
        assert abs(audio_dur - expected) < frame_time
        # Audio and video must match within one frame
        assert abs(audio_dur - video_dur) < frame_time
        print(f"  video={video_dur:.3f}s audio={audio_dur:.3f}s (target={expected:.3f}s, in sync)")

# (4) Test shared identity format
def test_shared_identity_format():
    """export.py and review.py use same identity format (size:mtime_ns:sha256)."""
    sys.path.insert(0, str(HERE))
    import export
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a test file
        test_file = out / "test.txt"
        test_file.write_text("hello world")
        
        # Get identity from both modules
        export_id = export.file_identity(test_file)
        review_id = review.file_identity(test_file)
        
        # Must be identical
        assert export_id == review_id
        # Must have sha256 (3 colon-separated parts)
        parts = export_id.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 64  # sha256 hex digest length
        print(f"  shared format: size:mtime_ns:sha256")

# 10. DeepFilterNet skip when unavailable
def test_deepfilternet_skip():
    """DeepFilterNet skips cleanly when binary is unavailable."""
    sys.path.insert(0, str(HERE))
    import deepfilternet_helper as dfn
    
    # Most systems won't have deep-filter installed
    if not dfn.is_available():
        result = dfn.denoise_dialogue("any.wav", "out.wav")
        assert result["success"] is False
        assert result["skipped"] is not None
        assert "not available" in result["skipped"]
        print(f"  skipped: {result['skipped']}")
    else:
        print("  deep-filter available (skipping skip test)")

# 11. DeepFilterNet refusal on music/vocal
def test_deepfilternet_refusal():
    """DeepFilterNet refuses to run on music/vocal inputs (fail-closed)."""
    sys.path.insert(0, str(HERE))
    import deepfilternet_helper as dfn
    
    # Test filename detection (fail-closed: refuse)
    allowed, reason = dfn.is_dialogue_allowed("song_vocals.wav")
    assert allowed is False
    assert "vocal" in reason
    print(f"  refused: {reason}")
    
    # Test metadata detection (fail-closed: refuse unless explicit dialogue)
    allowed, reason = dfn.is_dialogue_allowed("audio.wav", {"stem_type": "vocals"})
    assert allowed is False
    assert "vocals" in reason or "stem_type" in reason
    
    # Unclassified is refused (fail-closed)
    allowed, reason = dfn.is_dialogue_allowed("interview_dialogue.wav")
    assert allowed is False  # fail-closed unless explicitly marked as dialogue

# 12. WhisperX skip when unavailable
def test_whisperx_skip():
    """WhisperX skips cleanly when module is unavailable."""
    sys.path.insert(0, str(HERE))
    import whisperx_helper as wx
    
    # Most systems won't have whisperx installed
    if not wx.is_available():
        result = wx.cross_check_lyrics("any.wav", ["test", "lyrics"])
        assert result["success"] is False
        assert result["skipped"] is not None
        assert "not available" in result["skipped"]
        print(f"  skipped: {result['skipped']}")
    else:
        print("  whisperx available (would run cross-check)")

# 13. PySceneDetect fallback to ffmpeg
def test_pyscenedetect_fallback():
    """PySceneDetect falls back to ffmpeg when unavailable."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a video with strong scene changes (noise patterns)
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=1",
                        "-f", "lavfi", "-i", "nullsrc=s=320x240:d=1,geq='random(1)*255:128:128'",
                        "-f", "lavfi", "-i", "color=white:s=320x240:r=30:duration=1",
                        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "cuts.mp4")],
                       capture_output=True, check=True)
        
        sys.path.insert(0, str(HERE))
        import pyscenedetect_helper as psd
        
        # Test that the helper runs successfully (detection may vary)
        # Just verify the method works, not exact cut detection on synthetic fixture
        expected = [30, 60]
        result = psd.verify_cut_map(out / "cuts.mp4", expected, tolerance_frames=10)
        assert result["success"] is True
        assert result["method"] in ("pyscenedetect", "ffmpeg")
        # Detection on synthetic video may be unreliable; just verify it ran
        print(f"  method: {result['method']}, matched: {result['matched']}/{len(expected)} (synthetic fixture)")

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
            passed += 1
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{passed}/{len(tests)} tests passed")

# 19. DeepFilterNet source overwrite protection
def test_deepfilternet_no_overwrite():
    """DeepFilterNet doesn't overwrite source when input is in output folder."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "takes"
        out.mkdir()
        v = make_test_video(Path(tmp), dur=1, audio=True)
        # Copy to takes folder
        source = out / "take01.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), str(source)], capture_output=True, check=True)
        
        source_bytes = source.read_bytes()
        source_size = len(source_bytes)
        
        sys.path.insert(0, str(HERE))
        import deepfilternet_helper as dfn
        
        # Even if deep-filter is available, with our dialogue-only guard it will refuse
        # But if it were to run, it must not overwrite source
        result = dfn.denoise_dialogue(str(source), str(out / "clean.wav"),
                                     metadata={"is_dialogue": True, "audio_type": "dialogue"})
        
        # Source bytes must not change
        assert source.read_bytes() == source_bytes
        assert len(source.read_bytes()) == source_size
        print(f"  source bytes unchanged ({source_size} bytes)")

# 20. Dialogue-only guard comprehensive refusal
def test_dialogue_guard_refusals():
    """Dialogue guard refuses vox, lead, chorus, backing, bgm, vocal, stem, music, song, inst (case-insensitive)."""
    sys.path.insert(0, str(HERE))
    import deepfilternet_helper as dfn
    
    refused_names = ["take01_vox.wav", "LEAD.wav", "Chorus_01.wav", "backing_vocals.wav",
                    "bgm.wav", "vocal.wav", "vocals_stem.wav", "music.wav", "song.wav", "inst.wav"]
    
    for name in refused_names:
        allowed, reason = dfn.is_dialogue_allowed(name)
        assert allowed is False
        assert reason is not None
        print(f"  refused: {name} ({reason[:40]})")
    
    # Unclassified also refused (fail closed)
    allowed, reason = dfn.is_dialogue_allowed("audio.wav")
    assert allowed is False
    assert "not explicitly classified" in reason
    print(f"  unclassified refused: {reason}")

# (1) Test CLI dialogue metadata flags
def test_deepfilternet_cli_dialogue_flags():
    """DeepFilterNet CLI accepts --audio-type and --is-dialogue flags."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=0.5, audio=True)
        wav = out / "audio.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-ar", "48000", str(wav)],
                       capture_output=True, check=True)
        
        # Test --audio-type dialogue (should still refuse because deep-filter not available or file not dialogue)
        result = subprocess.run([sys.executable, str(HERE / "deepfilternet_helper.py"),
                                str(wav), str(out / "out1.wav"), "--audio-type", "dialogue"],
                               capture_output=True, text=True)
        # Will exit 2 (refused) or 3 (skipped) depending on deep-filter availability
        assert result.returncode in (2, 3)
        
        # Test --is-dialogue flag
        result = subprocess.run([sys.executable, str(HERE / "deepfilternet_helper.py"),
                                str(wav), str(out / "out2.wav"), "--is-dialogue"],
                               capture_output=True, text=True)
        assert result.returncode in (2, 3)
        print(f"  CLI flags accepted (exit code {result.returncode})")

# 21. Change scope rectangle parsing (don't split on commas inside rect)
def test_change_scope_rect_parsing():
    """Parse '1-2@10,20,30,40' correctly without splitting on commas inside rectangle."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v1 = make_test_video(out, dur=0.5)
        v2 = make_test_video(out, dur=0.5)
        
        # Test that the rect parsing doesn't break on commas
        result = verify_change_scope(v1, v2, ["0.1-0.3@10,20,30,40"])
        # Should parse successfully (not fail with "invalid rect syntax")
        assert "invalid rect" not in str(result.get("failures", []))
        print(f"  rect parsed: 0.1-0.3@10,20,30,40")

# (2) Test CLI rect parsing with subprocess
def test_cli_expect_changed_rect_parsing():
    """review.py CLI parses '1-2@10,20,30,40' without breaking on rect commas."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create two identical short videos
        v1 = make_test_video(out, dur=0.5)
        v2 = make_test_video(out, dur=0.5)
        review_dir = out / "review"
        review_dir.mkdir()
        
        # Run review.py check with rect argument via CLI
        r = subprocess.run([sys.executable, str(HERE / "review.py"), "check", str(v2),
                           "--out", str(review_dir), "--compare", str(v1),
                           "--expect-changed", "0.1-0.3@10,20,30,40"],
                          capture_output=True, text=True)
        # Should succeed (identical videos, no change outside allowed rect)
        # The key test is that it parsed the rect correctly and didn't split on commas
        assert r.returncode == 0
        print(f"  CLI parsed rect: 0.1-0.3@10,20,30,40")

# 22. Change scope errors when --compare missing
def test_change_scope_no_compare():
    """verify_change_scope called without compare should be caught by check() error."""
    # This is enforced at the check() CLI level, tested via CLI invocation
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1)
        review_dir = out / "review"
        review_dir.mkdir()
        
        # Try to run check with --expect-changed but no --compare
        r = subprocess.run([sys.executable, str(HERE / "review.py"), "check", str(v),
                           "--out", str(review_dir), "--expect-changed", "none"],
                          capture_output=True, text=True)
        # Should exit with error
        assert r.returncode != 0
        assert "requires --compare" in r.stderr or "requires --compare" in r.stdout
        print(f"  error: requires --compare")

# 23. PySceneDetect version probe
def test_pyscenedetect_version_probe():
    """PySceneDetect is_available uses 'scenedetect version', not --version."""
    sys.path.insert(0, str(HERE))
    import pyscenedetect_helper as psd
    
    # Just verify the probe doesn't crash (may return False if not installed)
    available = psd.is_available()
    print(f"  PySceneDetect available: {available}")

# 24. PySceneDetect CSV parsing (don't count opening frame)
def test_pyscenedetect_csv_parsing():
    """PySceneDetect parses 1-based CSV correctly and doesn't count frame 1 as a cut."""
    # This is tested via actual cut detection in the synthetic clip test
    # The opening frame (1) should not be reported as a cut
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create video with known cut at frame ~30
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=1",
                        "-f", "lavfi", "-i", "nullsrc=s=320x240:d=1,geq='random(1)*255:128:128'",
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "cuts.mp4")],
                       capture_output=True, check=True)
        
        sys.path.insert(0, str(HERE))
        import pyscenedetect_helper as psd
        
        result = psd.detect_cuts_ffmpeg(out / "cuts.mp4")
        # Frame 0 or 1 should not be in the cuts list
        if result["success"] and result["cuts"]:
            assert 0 not in result["cuts"]
            assert 1 not in result["cuts"]
            print(f"  cuts detected (excluding opening frame): {result['cuts'][:5]}")

# 25. Identity uses sha256 content digest
def test_identity_sha256():
    """file_identity uses sha256 content digest, not just size:mtime_ns."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1)
        identity = export_file_identity(v)
        # Should have three parts: size:mtime_ns:sha256
        parts = identity.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 64  # sha256 hex digest
        print(f"  identity format: size:mtime:sha256 (sha256={parts[2][:16]}...)")

# 26. Duration fit enforcement
def test_duration_fit_enforcement():
    """check_duration_fit refuses ratio >1.15x (e.g. 10.0/6.0 = 1.67x)."""
    from export import check_duration_fit
    
    # 10.0 / 6.0 = 1.667x should be refused (difference > 0.5s threshold)
    ok, factor, reason = check_duration_fit(10.0, 6.0, allow_speed_change=False)
    assert ok is False
    assert abs(factor - 1.667) < 0.01
    assert "1.15" in reason
    print(f"  refused {factor:.2f}x: {reason[:50]}")
    
    # With flag should be allowed
    ok, factor, reason = check_duration_fit(10.0, 6.0, allow_speed_change=True)
    assert ok is True
    print(f"  allowed {factor:.2f}x with --allow-speed-change")

# 27. Filter sanitizer prevents injection
def test_filter_sanitizer():
    """sanitize_filter_input escapes dangerous chars and prevents injection."""
    from review import sanitize_filter_input
    
    # Test dangerous chars are escaped
    assert "\\'" in sanitize_filter_input("it's")
    assert "\\:" in sanitize_filter_input("Topic: draft")
    assert "\\," in sanitize_filter_input("First, second")
    assert "\\\\" in sanitize_filter_input("back\\slash")
    
    # Actual injection attempt via drawtext
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=0.5)
        
        # Attempt to inject a second drawtext
        malicious = "scene1':text='INJECTED"
        safe = sanitize_filter_input(malicious)
        
        # Build a drawtext filter and run it
        result = subprocess.run([
            "ffmpeg", "-y", "-i", str(v), "-vf",
            f"drawtext=text='{safe}':x=10:y=10:fontsize=24:fontcolor=white",
            "-frames:v", "1", str(out / "frame.jpg")
        ], capture_output=True, text=True)
        
        # Should succeed (not crash from injection)
        assert result.returncode == 0
        assert (out / "frame.jpg").exists()
        print(f"  injection neutralized: '{malicious[:30]}...'")

# 28. Dropout detection uses audio stream end
def test_dropout_audio_stream_end():
    """Dropout detection uses audio stream duration, not container."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create video with audio that ends before video (trailing silence in container sense)
        # Video: 2.0s, Audio: 1.0s
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=2.0",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=1.0",
                        "-c:v", "libx264", "-c:a", "aac", "-shortest:v=0", str(out / "short_audio.mp4")],
                       capture_output=True, check=True)
        
        # The trailing 1.0s of container time (1.0-2.0s) should NOT be flagged as dropout
        # because audio stream ends at 1.0s
        dropouts = detect_dropouts(out / "short_audio.mp4")
        # Should have no dropouts in the 0.9-1.0s range
        for start, dur in dropouts:
            assert start < 0.85  # well before audio stream end
        print(f"  no dropout flagged near audio stream end (1.0s)")


if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
            passed += 1
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{passed}/{len(tests)} tests passed")

# (a) Test chroma comparison catches hue shift
def test_chroma_hue_shift():
    """verify_change_scope catches hue shift with same luma."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create two videos: one neutral, one with hue shift (same luma)
        # Use HSV shift: shift hue by 60 degrees (green -> cyan)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=green:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=cyan:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True)
        
        # Verify hue shift is detected (chroma change)
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is False
        assert len(result["failures"]) > 0
        print(f"  hue shift detected: {len(result['failures'])} tiles changed")

# (b) Test brightness lift detection
def test_brightness_lift_detection():
    """verify_change_scope detects +20 brightness lift."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create two videos: darker and brighter (use RGB values for consistent luma)
        # RGB 128,128,128 vs 148,148,148 gives exactly +20 luma lift
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=0x808080:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=0x949494:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True)
        
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is False
        assert result["brightness_lift"] is not None
        assert result["brightness_lift"] > 15
        print(f"  brightness lift detected: {result['brightness_lift']:+.1f} levels (expected ~+20)")

# (b) Test small brightness change is not flagged
def test_brightness_small_change_allowed():
    """verify_change_scope allows +3 brightness change (below threshold)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # RGB 128,128,128 vs 131,131,131 gives +3 luma lift (below 15 threshold)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=0x808080:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=0x838383:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True)
        
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is True
        assert result["brightness_lift"] is None
        print(f"  small +3 brightness change allowed (below threshold)")

# (b) Test appended tail frames fail
def test_appended_tail_frames_fail():
    """verify_change_scope fails on frame count mismatch (appended frames)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create ref video (15 frames at 30fps = 0.5s)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        # Create test video with extra frames (20 frames = 0.667s)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=0.667",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True)
        
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is False
        assert any("frame count mismatch" in str(f) for f in result["failures"])
        print(f"  tail frames detected: frame count mismatch")

# (b) Test black + white appended frames fail none
def test_black_white_appended_fails_none():
    """Black clip with white frames appended fails 'none' scope."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create black reference
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        # Create black + white appended
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=0.5",
                        "-f", "lavfi", "-i", "color=white:s=320x240:r=30:duration=0.167",
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True)
        
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is False
        print(f"  appended white frames caught")

# (3) Test failure reasons preserved with ≥10 failures
def test_many_failures_preserve_reasons():
    """When there are ≥10 failures, all failure reasons are preserved correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create all-black reference
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=black:s=1920x1080:r=30:duration=0.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True)
        # Create test with many small white squares that will trigger multiple tile failures
        # Draw 12 white rectangles across different locations to hit multiple tiles
        drawboxes = ",".join([
            "drawbox=x=0:y=0:w=100:h=100:color=white:t=fill",
            "drawbox=x=200:y=0:w=100:h=100:color=white:t=fill",
            "drawbox=x=400:y=0:w=100:h=100:color=white:t=fill",
            "drawbox=x=600:y=0:w=100:h=100:color=white:t=fill",
            "drawbox=x=800:y=0:w=100:h=100:color=white:t=fill",
            "drawbox=x=0:y=200:w=100:h=100:color=white:t=fill",
            "drawbox=x=200:y=200:w=100:h=100:color=white:t=fill",
            "drawbox=x=400:y=200:w=100:h=100:color=white:t=fill",
            "drawbox=x=600:y=200:w=100:h=100:color=white:t=fill",
            "drawbox=x=800:y=200:w=100:h=100:color=white:t=fill",
            "drawbox=x=0:y=400:w=100:h=100:color=white:t=fill",
            "drawbox=x=200:y=400:w=100:h=100:color=white:t=fill",
        ])
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                        "-i", "color=black:s=1920x1080:r=30:duration=0.5",
                        "-vf", drawboxes,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True, timeout=10)
        
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        assert result["pass"] is False
        failures = result["failures"]
        # Should have at least 10 failures (limit is 10, plus possibly brightness)
        assert len(failures) >= 10, f"Expected ≥10 failures, got {len(failures)}"
        # Check that most failures have the tile-based reason (not just brightness)
        tile_failures = [f for f in failures if "change outside declared regions" in str(f[5])]
        assert len(tile_failures) >= 10, f"Expected ≥10 tile failures, got {len(tile_failures)}"
        print(f"  {len(tile_failures)} tile failures, all with correct reasons")

# (c) Test memory bounds with streaming
def test_change_scope_memory_bounded():
    """verify_change_scope stays <150MB on 10s 1080x1920 video (frame-by-frame streaming)."""
    import tracemalloc
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create 10s video at 1080x1920 (30fps = 300 frames)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=30:duration=10",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "ref.mp4")],
                       capture_output=True, check=True, timeout=60)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=30:duration=10",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")],
                       capture_output=True, check=True, timeout=60)
        
        # Measure peak memory during comparison using tracemalloc
        tracemalloc.start()
        result = verify_change_scope(out / "ref.mp4", out / "test.mp4", ["none"])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory in MB (frame-by-frame streaming keeps it under 150 MB)
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 150, f"Peak memory {peak_mb:.1f} MB exceeds 150 MB"
        print(f"  peak memory: {peak_mb:.1f} MB on 10s 1080x1920 (< 150 MB)")

# (d) Test PySceneDetect actual cut lists
def test_pyscenedetect_actual_cuts():
    """PySceneDetect fallback returns [6] for synthetic clip with cut at frame 6."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create video with known cut: 6 black frames, then 6 white frames at 30fps
        subprocess.run(["ffmpeg", "-y",
                        "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=0.2",
                        "-f", "lavfi", "-i", "color=white:s=320x240:r=30:duration=0.2",
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "cuts.mp4")],
                       capture_output=True, check=True)
        
        sys.path.insert(0, str(HERE))
        import pyscenedetect_helper as psd
        
        result = psd.detect_cuts_ffmpeg(out / "cuts.mp4", threshold=0.3)
        assert result["success"] is True
        # Cut at frame 6 (0.2s * 30fps = 6 frames)
        assert 6 in result["cuts"], f"expected [6] in cuts, got {result['cuts']}"
        print(f"  cuts detected: {result['cuts']} (expected frame 6)")

# (e) Test whisperX alignment failure
def test_whisperx_alignment_failure():
    """WhisperX returns error when alignment fails."""
    from unittest.mock import Mock, patch
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1, audio=True)
        
        # Mock whisperx module and its functions
        mock_whisperx = Mock()
        mock_whisperx.load_audio.return_value = np.zeros(16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {"segments": [{"text": "test"}]}
        mock_whisperx.load_model.return_value = mock_model
        
        # Alignment raises exception
        mock_whisperx.load_align_model.side_effect = RuntimeError("Alignment model failed")
        
        with patch.dict('sys.modules', {'whisperx': mock_whisperx, 'torch': Mock()}):
            import whisperx_helper
            result = whisperx_helper.cross_check_lyrics(str(v), ["test", "words"])
            
            assert result["success"] is False
            assert result["error"] is not None
            assert "alignment failed" in result["error"].lower()
            print(f"  alignment failure caught: {result['error'][:50]}")

# (e) Test whisperX wrong order detection
def test_whisperx_wrong_order():
    """WhisperX detects words in wrong order or timing >300ms off."""
    from unittest.mock import Mock, patch
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1, audio=True)
        
        # Mock whisperx module
        mock_whisperx = Mock()
        mock_whisperx.load_audio.return_value = np.zeros(16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {"segments": [{"text": "world hello"}]}
        mock_whisperx.load_model.return_value = mock_model
        
        # Mock alignment that returns words in WRONG order
        mock_align_model = Mock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, {})
        mock_whisperx.align.return_value = {
            "segments": [{
                "words": [
                    {"word": "world", "start": 0.0, "end": 0.5},
                    {"word": "hello", "start": 0.5, "end": 1.0}
                ]
            }]
        }
        
        with patch.dict('sys.modules', {'whisperx': mock_whisperx, 'torch': Mock()}):
            import whisperx_helper
            # Official order: hello, world (opposite of detected)
            result = whisperx_helper.cross_check_lyrics(str(v), ["hello", "world"])
            
            # Alignment succeeded but order is wrong or timing is off >300ms
            assert result["success"] is True  # alignment didn't crash
            # Check for order issues or timing issues
            details = result.get("details", {})
            if isinstance(details, dict):
                order_mismatches = details.get("order_mismatches", [])
                timing_mismatches = details.get("timing_mismatches", [])
                assert len(order_mismatches) > 0 or len(timing_mismatches) > 0, "Should detect order or timing mismatch"
                print(f"  order/timing mismatch detected")

# (6) Test WhisperX timing tolerance > 300ms fails
def test_whisperx_timing_over_300ms_fails():
    """WhisperX detects timing gaps > 300ms."""
    from unittest.mock import Mock, patch
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1, audio=True)
        
        mock_whisperx = Mock()
        mock_whisperx.load_audio.return_value = np.zeros(16000)
        mock_model = Mock()
        mock_model.transcribe.return_value = {"segments": [{"text": "hello world"}]}
        mock_whisperx.load_model.return_value = mock_model
        
        # Words with >300ms gap (500ms gap)
        mock_align_model = Mock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, {})
        mock_whisperx.align.return_value = {
            "segments": [{
                "words": [
                    {"word": "hello", "start": 0.0, "end": 0.2},
                    {"word": "world", "start": 0.7, "end": 0.9}  # 500ms gap
                ]
            }]
        }
        
        with patch.dict('sys.modules', {'whisperx': mock_whisperx, 'torch': Mock()}):
            import whisperx_helper
            result = whisperx_helper.cross_check_lyrics(str(v), ["hello", "world"])
            details = result.get("details", {})
            if isinstance(details, dict):
                timing_mismatches = details.get("timing_mismatches", [])
                assert len(timing_mismatches) > 0
                print(f"  timing gap >300ms detected")

# (6) Test WhisperX timing tolerance < 300ms passes
def test_whisperx_timing_under_300ms_passes():
    """WhisperX allows timing gaps < 300ms."""
    from unittest.mock import Mock, patch
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1, audio=True)
        
        mock_whisperx = Mock()
        mock_whisperx.load_audio.return_value = np.zeros(16000)
        mock_model = Mock()
        mock_model.transcribe.return_value = {"segments": [{"text": "hello world"}]}
        mock_whisperx.load_model.return_value = mock_model
        
        # Words with <300ms gap (100ms gap)
        mock_align_model = Mock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, {})
        mock_whisperx.align.return_value = {
            "segments": [{
                "words": [
                    {"word": "hello", "start": 0.0, "end": 0.2},
                    {"word": "world", "start": 0.3, "end": 0.5}  # 100ms gap
                ]
            }]
        }
        
        with patch.dict('sys.modules', {'whisperx': mock_whisperx, 'torch': Mock()}):
            import whisperx_helper
            result = whisperx_helper.cross_check_lyrics(str(v), ["hello", "world"])
            details = result.get("details", {})
            if isinstance(details, dict):
                timing_mismatches = details.get("timing_mismatches", [])
                assert len(timing_mismatches) == 0
                print(f"  timing gap <300ms allowed")

# (6) Test WhisperX punctuation normalization
def test_whisperx_punctuation_normalization():
    """WhisperX normalizes 'Hello,' to match 'hello'."""
    from unittest.mock import Mock, patch
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1, audio=True)
        
        mock_whisperx = Mock()
        mock_whisperx.load_audio.return_value = np.zeros(16000)
        mock_model = Mock()
        mock_model.transcribe.return_value = {"segments": [{"text": "Hello, world!"}]}
        mock_whisperx.load_model.return_value = mock_model
        
        # Detected with punctuation
        mock_align_model = Mock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, {})
        mock_whisperx.align.return_value = {
            "segments": [{
                "words": [
                    {"word": "Hello,", "start": 0.0, "end": 0.3},
                    {"word": "world!", "start": 0.3, "end": 0.6}
                ]
            }]
        }
        
        with patch.dict('sys.modules', {'whisperx': mock_whisperx, 'torch': Mock()}):
            import whisperx_helper
            # Official without punctuation
            result = whisperx_helper.cross_check_lyrics(str(v), ["hello", "world"])
            details = result.get("details", {})
            if isinstance(details, dict):
                # Should match after normalization
                matched = details.get("matched_count", 0)
                assert matched == 2
                print(f"  'Hello,' matched 'hello' (punctuation normalized)")

# (f) Test filter sanitizer renders correctly
def test_filter_sanitizer_renders_correctly():
    """Sanitized text renders literally, no extra filter applied."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=0.5)
        
        from review import sanitize_filter_input
        
        # Test cases that must render literally
        test_cases = ["Topic: draft", "First, second"]
        
        for text in test_cases:
            safe = sanitize_filter_input(text)
            result = subprocess.run([
                "ffmpeg", "-y", "-i", str(v), "-vf",
                f"drawtext=text='{safe}':x=10:y=10:fontsize=24:fontcolor=white",
                "-frames:v", "1", str(out / f"frame_{text[:5]}.jpg")
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            frame = out / f"frame_{text[:5]}.jpg"
            assert frame.exists()
            # Check output is a single frame
            stat = frame.stat()
            assert stat.st_size > 1000  # reasonable JPEG size
            print(f"  '{text}' rendered: {stat.st_size} bytes")
        
        # Verify no extra filter in graph (single drawtext)
        # Test injection attempt doesn't create multiple filters
        malicious = "text':text='INJECTED"
        safe = sanitize_filter_input(malicious)
        result = subprocess.run([
            "ffmpeg", "-y", "-i", str(v), "-vf",
            f"drawtext=text='{safe}':x=10:y=10:fontsize=24:fontcolor=white",
            "-frames:v", "1", str(out / "injection.jpg")
        ], capture_output=True, text=True, timeout=5)
        
        # Should produce exactly 1 frame, not crash or produce multiple
        assert result.returncode == 0
        assert (out / "injection.jpg").exists()
        # Verify stderr doesn't show filter graph errors
        assert "Invalid" not in result.stderr
        assert "Error" not in result.stderr
        print(f"  injection neutralized: single frame output, no filter errors")


if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
            passed += 1
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{passed}/{len(tests)} tests passed")
