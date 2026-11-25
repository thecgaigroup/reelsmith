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
    """file_identity returns size:mtime_ns string."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3)
        identity = file_identity(v)
        assert ":" in identity, f"Expected size:mtime_ns format, got {identity}"
        size, mtime_ns = identity.split(":")
        assert int(size) > 0, f"Expected nonzero size"
        assert int(mtime_ns) > 0, f"Expected nonzero mtime"
        print(f"  identity: {identity}")

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
