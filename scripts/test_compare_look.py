"""Tests for compare_look.py with synthetic ffmpeg frames.

Run: python3 -m pytest scripts/test_compare_look.py

Adapted from codepawl/creator-generalist (MIT), commit d3ab529a, read 2026-11-14.
"""

import pathlib
import shutil
import subprocess
import sys

try:
    import pytest
except ImportError:
    print("pytest not found. Install it with: pip install pytest")
    sys.exit(1)


SCRIPT = pathlib.Path(__file__).resolve().parent / "compare_look.py"

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="ffmpeg is not installed"
)


def make_image(path, color, eq_filter=None):
    """Generate a solid-color image using ffmpeg."""
    command = [
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s=320x180",
        "-frames:v", "1"
    ]
    if eq_filter:
        command += ["-vf", eq_filter]
    command.append(str(path))
    subprocess.run(command, check=True, capture_output=True)


def make_video(path, color):
    """Generate a solid-color video using ffmpeg."""
    command = [
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=10:d=3",
        "-pix_fmt", "yuv420p", str(path)
    ]
    subprocess.run(command, check=True, capture_output=True)


def run_compare(*arguments):
    """Run the compare_look.py script and return the result."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )


@pytest.fixture
def style_frame(tmp_path):
    """Create a style frame with a warm orange color."""
    path = tmp_path / "style.png"
    make_image(path, "0xC86E3C")  # Warm orange
    return path


def test_same_look_passes(tmp_path, style_frame):
    same = tmp_path / "same.png"
    make_image(same, "0xC86E3C")
    result = run_compare("--style", style_frame, same)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 of 1 frames inside the look band" in result.stdout


def test_darker_greyer_blue_shifted_frame_fails(tmp_path, style_frame):
    drifted = tmp_path / "drifted.png"
    make_image(drifted, "0x303A4A")  # Dark blue-grey
    result = run_compare("--style", style_frame, drifted)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "darker" in result.stdout
    assert "greyer" in result.stdout
    assert "color cast differs" in result.stdout


def test_video_sampled_at_one_fps_passes(tmp_path, style_frame):
    video = tmp_path / "shot.mp4"
    make_video(video, "0xC86E3C")
    result = run_compare("--style", style_frame, video, "--fps", "1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "@ 0.0 s" in result.stdout
    assert "3 of 3 frames inside the look band" in result.stdout


def test_missing_file_exits_two(tmp_path, style_frame):
    result = run_compare("--style", style_frame, tmp_path / "does-not-exist.png")
    assert result.returncode == 2
    assert "cannot read" in result.stdout


def test_brighter_frame_fails(tmp_path, style_frame):
    bright = tmp_path / "bright.png"
    make_image(bright, "0xFFFFFF")  # White
    result = run_compare("--style", style_frame, bright)
    assert result.returncode == 1
    assert "brighter" in result.stdout


def test_more_saturated_frame_fails(tmp_path, style_frame):
    saturated = tmp_path / "saturated.png"
    make_image(saturated, "0xFF0000")  # Pure red (highly saturated)
    result = run_compare("--style", style_frame, saturated)
    assert result.returncode == 1
    # May fail on brighter, more saturated, or hue shift
    assert "FAIL" in result.stdout


def test_json_report_written(tmp_path, style_frame):
    same = tmp_path / "same.png"
    make_image(same, "0xC86E3C")
    report_path = tmp_path / "report.json"
    result = run_compare("--style", style_frame, same, "--json", report_path)
    assert result.returncode == 0
    assert report_path.exists()
    import json
    report = json.loads(report_path.read_text())
    assert "style" in report
    assert "frames" in report
    assert len(report["frames"]) == 1


def test_multiple_frames_mixed(tmp_path, style_frame):
    good1 = tmp_path / "good1.png"
    make_image(good1, "0xC86E3C")  # Same as style
    bad = tmp_path / "bad.png"
    make_image(bad, "0x000000")  # Black (much darker)
    good2 = tmp_path / "good2.png"
    make_image(good2, "0xC86E3C")  # Same as style
    
    result = run_compare("--style", style_frame, good1, bad, good2)
    assert result.returncode == 1
    assert "2 of 3 frames inside the look band" in result.stdout
    assert "darker" in result.stdout
