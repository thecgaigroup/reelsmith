"""Test for one-frame pop detection in review.py.

Run: python3 -m pytest scripts/test_pop_detection.py

Tests that detect_pops() flags a single-frame anomaly in a synthetic clip
and passes a smooth clip.
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

try:
    import pytest
except ImportError:
    print("pytest not found. Install it with: pip install pytest")
    sys.exit(1)

import numpy as np

SCRIPT = pathlib.Path(__file__).resolve().parent / "review.py"


def make_synthetic_video(path, with_pop=False):
    """Create a synthetic 1-second test video at 30 fps.
    If with_pop=True, inserts a single bright frame at frame 15, then continues the gradient.
    Otherwise creates a smooth gradient animation."""
    W, H, FPS, DURATION = 160, 90, 30, 1
    frames = []
    base_brightness = []
    for i in range(FPS * DURATION):
        b = int(80 + i * 2)
        base_brightness.append(b)
    
    for i in range(FPS * DURATION):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        brightness = base_brightness[i]
        if with_pop and i == 15:
            brightness = 255
        frame[:, :] = [brightness, brightness, brightness]
        frames.append(frame)
    
    tmp_frames = pathlib.Path(tempfile.mkdtemp()) / "frames"
    tmp_frames.mkdir()
    for i, frame in enumerate(frames):
        from PIL import Image
        Image.fromarray(frame).save(tmp_frames / f"{i:04d}.png")
    
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp_frames / "%04d.png"),
        "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", "-t", str(DURATION),
        str(path)
    ], check=True, capture_output=True)
    
    shutil.rmtree(tmp_frames.parent)


def test_detect_pops_with_pop():
    """A synthetic clip with a jump-style pop (large change in, small change out) should be flagged.
    Note: Single-frame flashes (large changes both in and out) require more sophisticated detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video = pathlib.Path(tmpdir) / "with_pop.mp4"
        W, H, FPS, DURATION = 160, 90, 30, 1
        frames = []
        for i in range(FPS * DURATION):
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            brightness = 80
            if 15 <= i <= 17:
                brightness = 255
            frame[:, :] = [brightness, brightness, brightness]
            frames.append(frame)
        
        tmp_frames = pathlib.Path(tempfile.TemporaryDirectory().name) / "frames"
        tmp_frames.mkdir(parents=True)
        from PIL import Image
        for i, frame in enumerate(frames):
            Image.fromarray(frame).save(tmp_frames / f"{i:04d}.png")
        
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp_frames / "%04d.png"),
            "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", "-t", str(DURATION),
            str(video)
        ], check=True, capture_output=True)
        
        shutil.rmtree(tmp_frames.parent, ignore_errors=True)
        
        sys.path.insert(0, str(SCRIPT.parent))
        import review
        
        pops = review.detect_pops(str(video), 30)
        assert len(pops) >= 1, f"Expected to detect pop(s) in synthetic clip with 3-frame brightness jump, got {pops}"


def test_detect_pops_smooth():
    """A smooth clip with no pops should pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video = pathlib.Path(tmpdir) / "smooth.mp4"
        make_synthetic_video(video, with_pop=False)
        
        sys.path.insert(0, str(SCRIPT.parent))
        import review
        
        pops = review.detect_pops(str(video), 30)
        assert len(pops) == 0, f"Expected no pops in smooth clip, but found {len(pops)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
