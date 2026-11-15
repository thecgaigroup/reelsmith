"""Test for one-frame pop detection in review.py.

Run: python3 -m unittest scripts.test_pop_detection -v

Tests that detect_pops() correctly identifies single-frame anomalies while
ignoring smooth clips, hard cuts, and multi-frame changes.
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import review


def make_clip(brightness_values):
    """Create a test video from a list of brightness values, one per frame.
    Returns path to the created video file in a temp directory that caller must clean up."""
    W, H, FPS = 160, 90, 30
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    frames_dir = tmpdir / "frames"
    frames_dir.mkdir()
    
    for i, brightness in enumerate(brightness_values):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:, :] = [brightness, brightness, brightness]
        Image.fromarray(frame).save(frames_dir / f"{i:04d}.png")
    
    video = tmpdir / "test.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "%04d.png"),
        "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p",
        "-frames:v", str(len(brightness_values)), str(video)
    ], check=True, capture_output=True)
    
    shutil.rmtree(frames_dir)
    return video, tmpdir


class TestPopDetection(unittest.TestCase):
    
    def test_smooth_clip_no_pops(self):
        """A smooth clip with gradual changes gives no pops."""
        brightness = [80 + i * 2 for i in range(30)]
        video, tmpdir = make_clip(brightness)
        try:
            pops = review.detect_pops(str(video), 30)
            self.assertEqual(pops, [], f"Expected no pops in smooth clip, got {pops}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_single_bright_frame_is_pop(self):
        """A clip with exactly one bright frame at i=15 gives exactly [15]."""
        brightness = [80] * 30
        brightness[15] = 255
        video, tmpdir = make_clip(brightness)
        try:
            pops = review.detect_pops(str(video), 30)
            pop_frames = [f for f, _ in pops]
            self.assertEqual(pop_frames, [15], 
                           f"Expected pop at frame 15, got {pop_frames}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_hard_cut_no_pops(self):
        """A hard cut (80 until frame 14, then 200 from 15 onward) gives no pops."""
        brightness = [80] * 15 + [200] * 15
        video, tmpdir = make_clip(brightness)
        try:
            pops = review.detect_pops(str(video), 30)
            self.assertEqual(pops, [], 
                           f"Expected no pops at a held cut, got {pops}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_three_frame_plateau_no_pops(self):
        """A 3-frame plateau (frames 15-17 at 255) gives no pops."""
        brightness = [80] * 30
        brightness[15] = 255
        brightness[16] = 255
        brightness[17] = 255
        video, tmpdir = make_clip(brightness)
        try:
            pops = review.detect_pops(str(video), 30)
            self.assertEqual(pops, [], 
                           f"Expected no pops in 3-frame plateau, got {pops}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
