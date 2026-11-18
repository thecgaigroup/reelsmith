#!/usr/bin/env python3
"""Tests for check_sync_drift in review.py.

Tests the audio/video sync drift detection using stream start times and durations.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review import check_sync_drift, check

def make_test_video(out, dur=5, drift_ms=0):
    """Make a test video with optional A/V drift. drift_ms: positive = audio starts earlier (leads video)."""
    # Generate sine wave audio
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}", "-c:a", "aac",
                    str(out / "a.m4a")], capture_output=True, check=True)
    # Generate black video
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=320x240:r=30:duration={dur}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "v.mp4")], capture_output=True, check=True)
    # Mux with optional delay on audio (itsoffset shifts the stream start time)
    delay = drift_ms / 1000.0
    cmd = ["ffmpeg", "-y"]
    if drift_ms != 0:
        cmd += ["-itsoffset", str(delay)]
    cmd += ["-i", str(out / "a.m4a"), "-i", str(out / "v.mp4"), "-c", "copy", "-map", "1:v", "-map", "0:a",
            str(out / "test.mp4")]
    subprocess.run(cmd, capture_output=True, check=True)
    return out / "test.mp4"

def test_no_audio():
    """Video with no audio stream returns empty probes and no error."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:duration=3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")], capture_output=True, check=True)
        r = check_sync_drift(out / "test.mp4")
        assert r["probes"] == [], f"Expected empty probes for no audio"
        assert r["worst_drift_ms"] == 0.0, f"Expected 0 drift for no audio"
        assert r["flagged"] is False, f"Expected no flag for no audio"
        assert r["error"] is None, f"Expected no error for no audio"

def test_no_drift():
    """Video with good sync reports near-zero drift and is not flagged."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=0)
        r = check_sync_drift(v, warn_ms=50)
        assert len(r["probes"]) == 2, f"Expected 2 probes (start, end), got {len(r['probes'])}"
        assert r["worst_drift_ms"] <= 10, f"Expected drift ≤10ms for no offset, got {r['worst_drift_ms']}"
        assert r["flagged"] is False, f"Expected no flag for good sync"
        assert r["error"] is None, f"Expected no error"

def test_small_drift():
    """Small drift under threshold does not flag."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=30)
        r = check_sync_drift(v, warn_ms=50)
        # ffmpeg may not perfectly preserve the exact offset; verify it detects some drift but under threshold
        assert r["worst_drift_ms"] >= 15 and r["worst_drift_ms"] <= 40, \
            f"Expected drift 15-40ms for 30ms offset, got {r['worst_drift_ms']}"
        assert r["flagged"] is False, f"Expected no flag for small drift with 50ms threshold"
        assert r["error"] is None

def test_large_drift():
    """Large drift (>=80ms injected) over threshold flags WARNING."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=80)
        r = check_sync_drift(v, warn_ms=50)
        assert len(r["probes"]) == 2, f"Expected 2 probes"
        # ffmpeg may not perfectly preserve the exact offset due to encoding/frame boundaries
        # but it should detect significant drift (>50ms threshold)
        assert r["worst_drift_ms"] > 50, f"Expected drift >50ms for 80ms offset, got {r['worst_drift_ms']}"
        assert r["flagged"] is True, f"Expected flagged=True for large drift with 50ms threshold, got {r['flagged']}"
        assert r["error"] is None

def test_measurement_failure():
    """Measurement failure (corrupt file) is reported as error, not pass."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Create a corrupt file
        (out / "corrupt.mp4").write_bytes(b"not a video file")
        r = check_sync_drift(out / "corrupt.mp4")
        assert r["error"] is not None, f"Expected error for corrupt file, got {r}"
        assert r["worst_drift_ms"] == 0.0
        assert r["flagged"] is False

def test_returns_structure():
    """Result has the expected structure including error field."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5)
        r = check_sync_drift(v)
        assert "probes" in r and isinstance(r["probes"], list)
        assert "worst_drift_ms" in r and isinstance(r["worst_drift_ms"], (int, float))
        assert "flagged" in r and isinstance(r["flagged"], bool)
        assert "error" in r
        for t, d in r["probes"]:
            assert isinstance(t, (int, float)) and t >= 0
            assert isinstance(d, (int, float))

def test_check_end_to_end():
    """review.py check() completes end-to-end on a video with audio and includes sync drift result."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=3, drift_ms=0)
        rev_out = out / "_review"
        # Run the full check() function
        check(v, rev_out)
        # Verify review.json was created and contains sync_drift
        rev_json = rev_out / "review.json"
        assert rev_json.exists(), f"Expected review.json to be created"
        data = json.loads(rev_json.read_text())
        assert "sync_drift" in data, f"Expected sync_drift in review.json"
        assert "rows" in data
        # Find sync drift row in rows
        sync_row = next((r for r in data["rows"] if r["check"] == "sync drift"), None)
        assert sync_row is not None, f"Expected sync drift row in review.json rows"
        assert sync_row["level"] in ("PASS", "WARN"), f"Expected PASS or WARN, got {sync_row['level']}"

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{len(tests)} tests passed")
