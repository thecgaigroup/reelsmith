#!/usr/bin/env python3
"""Test frame-0 quality checker with real generated clips."""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_frame0_cover import check_frame0_cover


def create_test_clip(output_path, color_hex, duration=1):
    """Create a test video with solid color background.
    
    Args:
        output_path: Path to output video
        color_hex: Hex color (e.g. '#1E293B')
        duration: Duration in seconds
    
    Returns:
        Path to created video or None if failed
    """
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color_hex}:s=1080x1920:d={duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        print(f"Failed to create clip: {result.stderr.decode()}", file=sys.stderr)
        return None
    return output_path


def test_dark_clip_fails():
    """Clip that's too dark (mean < 25) must FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Very dark color: RGB(5, 5, 5) → Y ≈ 20 in limited range
        # Note: Limited-range YUV clamps Y to 16-235, so RGB(0,0,0) → Y≈16-20
        video = create_test_clip(tmpdir / "dark.mp4", "#050505", 1)
        if not video:
            raise AssertionError("Failed to create dark test clip")
        
        result = check_frame0_cover(str(video), min_mean=25, min_stddev=12)
        
        assert not result['passed'], "Dark clip should FAIL (mean < 25)"
        assert result['mean'] is not None and result['mean'] < 25, \
            f"Expected mean < 25, got {result['mean']}"
        
        print(f"✓ Dark clip test passed: mean={result['mean']:.1f} < 25, correctly FAILED")


def test_flat_clip_fails():
    """Clip that's flat (stddev < 12) must FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Solid medium-dark color: RGB(50, 50, 50) → Y ≈ 50, stddev ≈ 0
        video = create_test_clip(tmpdir / "flat.mp4", "#323232", 1)
        if not video:
            raise AssertionError("Failed to create flat test clip")
        
        result = check_frame0_cover(str(video), min_mean=16, min_stddev=12)
        
        assert not result['passed'], "Flat clip should FAIL (stddev < 12)"
        assert result['stddev'] is not None and result['stddev'] < 12, \
            f"Expected stddev < 12, got {result['stddev']}"
        
        print(f"✓ Flat clip test passed: stddev={result['stddev']:.1f} < 12, correctly FAILED")


def test_good_clip_passes():
    """Clip with good luma and contrast must PASS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create clip with text overlay for contrast
        # Dark blue background (30, 41, 59) + white text
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#1E293B:s=1080x1920:d=1",
            "-vf", "drawtext=text='Good Frame':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(tmpdir / "good.mp4")
        ]
        
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise AssertionError("Failed to create good test clip")
        
        video = tmpdir / "good.mp4"
        result = check_frame0_cover(str(video), min_mean=16, min_stddev=12)
        
        assert result['passed'], f"Good clip should PASS, but got errors: {result['errors']}"
        assert result['mean'] is not None and result['mean'] >= 16, \
            f"Expected mean >= 16, got {result['mean']}"
        assert result['stddev'] is not None and result['stddev'] >= 12, \
            f"Expected stddev >= 12, got {result['stddev']}"
        
        print(f"✓ Good clip test passed: mean={result['mean']:.1f} >= 16, stddev={result['stddev']:.1f} >= 12, correctly PASSED")


def test_darker_than_source_fails():
    """Clip >5% darker than source must FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create bright source image: RGB(200, 200, 200) → Y ≈ 200
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#C8C8C8:s=1080x1920:d=1",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create much darker video: RGB(100, 100, 100) → Y ≈ 100 (50% darker)
        video = create_test_clip(tmpdir / "darker.mp4", "#646464", 1)
        if not video:
            raise AssertionError("Failed to create darker test clip")
        
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"), 
                                   min_mean=16, min_stddev=0, max_darkening=5)
        
        assert not result['passed'], "Clip >5% darker than source should FAIL"
        assert 'source_comparison' in result
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None and sc['darkening_pct'] > 5, \
            f"Expected darkening > 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Darker-than-source test passed: {sc['darkening_pct']:.1f}% > 5%, correctly FAILED")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    print("Running frame-0 quality tests with real clips...\n")
    
    test_dark_clip_fails()
    test_flat_clip_fails()
    test_good_clip_passes()
    test_darker_than_source_fails()
    
    print("\n✅ All frame-0 real clip tests passed (0 skipped, 4 assertions)!")
