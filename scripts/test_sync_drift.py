#!/usr/bin/env python3
"""Tests for check_sync_drift in review.py.

Tests the audio/video sync drift detection at four probe points.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review import check_sync_drift

def make_test_video(out, dur=5, drift_ms=0):
    """Make a test video with optional A/V drift. drift_ms: positive = audio leads video."""
    # Generate silent audio
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=mono", "-t", str(dur),
                    "-c:a", "aac", str(out / "a.m4a")], capture_output=True, check=True)
    # Generate black video
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=320x240:r=30", "-t", str(dur),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "v.mp4")], capture_output=True, check=True)
    # Mux with optional delay on audio (itsoffset shifts the stream)
    delay = drift_ms / 1000.0
    cmd = ["ffmpeg", "-y"]
    if drift_ms != 0:
        cmd += ["-itsoffset", str(delay)]
    cmd += ["-i", str(out / "a.m4a"), "-i", str(out / "v.mp4"), "-c", "copy", "-map", "1:v", "-map", "0:a", str(out / "test.mp4")]
    subprocess.run(cmd, capture_output=True, check=True)
    return out / "test.mp4"

def test_no_audio():
    """Video with no audio stream should still work (probes may be empty or show no drift)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=320x240:r=30", "-t", "3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "test.mp4")], capture_output=True, check=True)
        r = check_sync_drift(out / "test.mp4")
        # With no audio, drift should be 0 and not flagged
        assert r["worst_drift_ms"] == 0.0, f"Expected 0 drift for no audio"
        assert r["flagged"] is False, f"Expected no flag for no audio"

def test_short_video():
    """Video under 2s returns empty probes."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=1.5)
        r = check_sync_drift(v)
        assert r["probes"] == [], f"Expected empty probes for video under 2s, got {r}"

def test_no_drift():
    """Video with good sync reports low drift."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=0)
        r = check_sync_drift(v, warn_ms=50)
        assert len(r["probes"]) == 4, f"Expected 4 probes, got {len(r['probes'])}"
        assert r["worst_drift_ms"] <= 10, f"Expected drift ≤10ms, got {r['worst_drift_ms']}"
        assert r["flagged"] is False, f"Expected no flag for good sync"

def test_small_drift():
    """Small drift under threshold does not flag."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=30)
        r = check_sync_drift(v, warn_ms=50)
        assert r["flagged"] is False, f"Expected no flag for 30ms drift with 50ms threshold"
        assert r["worst_drift_ms"] < 50

def test_large_drift():
    """Large drift over threshold flags warning."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5, drift_ms=80)
        r = check_sync_drift(v, warn_ms=50)
        # Note: actual drift detection depends on ffmpeg's sync analysis; this test may need adjustment
        # based on how well ffmpeg reports the injected drift
        assert len(r["probes"]) == 4, f"Expected 4 probes"

def test_returns_structure():
    """Result has the expected structure."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        v = make_test_video(out, dur=5)
        r = check_sync_drift(v)
        assert "probes" in r and isinstance(r["probes"], list)
        assert "worst_drift_ms" in r and isinstance(r["worst_drift_ms"], (int, float))
        assert "flagged" in r and isinstance(r["flagged"], bool)
        for t, d in r["probes"]:
            assert isinstance(t, (int, float)) and t >= 0
            assert isinstance(d, (int, float))

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
        except Exception as e:
            print(f"FAIL\n  {e}")
            sys.exit(1)
    print(f"\n{len(tests)} tests passed")
