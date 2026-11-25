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
    """Clip that's too dark (mean < 16) must FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Very dark color: RGB(2, 2, 2) in full range → Y ≈ 10 in limited range
        # Use colorspace filter to force full-range input that gets clipped lower
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#020202:s=1080x1920:d=1",
            "-vf", "format=yuv420p",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(tmpdir / "dark.mp4")
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise AssertionError("Failed to create dark test clip")
        
        video = tmpdir / "dark.mp4"
        result = check_frame0_cover(str(video), min_mean=16, min_stddev=12)
        
        assert not result['passed'], "Dark clip should FAIL (mean < 16)"
        assert result['mean'] is not None and result['mean'] < 16, \
            f"Expected mean < 16, got {result['mean']}"
        
        print(f"✓ Dark clip test passed: mean={result['mean']:.1f} < 16, correctly FAILED")


def test_flat_clip_fails():
    """Clip that's flat (stddev < 12) must FAIL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Solid medium-dark color: RGB(50, 50, 50) → Y ≈ 50, stddev ≈ 0
        video = create_test_clip(tmpdir / "flat.mp4", "#323232", 1)
        if not video:
            raise AssertionError("Failed to create flat test clip")
        
        # Use default thresholds (16, 12)
        result = check_frame0_cover(str(video))
        
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
        # Use default thresholds (16, 12)
        result = check_frame0_cover(str(video))
        
        assert result['passed'], f"Good clip should PASS, but got errors: {result['errors']}"
        assert result['mean'] is not None and result['mean'] >= 16, \
            f"Expected mean >= 16, got {result['mean']}"
        assert result['stddev'] is not None and result['stddev'] >= 12, \
            f"Expected stddev >= 12, got {result['stddev']}"
        
        print(f"✓ Good clip test passed: mean={result['mean']:.1f} >= 16, stddev={result['stddev']:.1f} >= 12, correctly PASSED")


def test_darker_than_source_fails():
    """Clip >5% darker than source must FAIL (darkening only)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create textured source: white text on gray background
        # Ensures stddev >= 12 and mean >= 16
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#808080:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create darker video: same text pattern but dimmed ~15%
        # RGB(70, 70, 70) background → Y ≈ 70 (vs source Y ≈ 128) = ~45% darker
        # But we want to target ~10% darker, so use RGB(115, 115, 115) → Y ≈ 115
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#737373:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(tmpdir / "darker.mp4")
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise AssertionError("Failed to create darker test clip")
        
        video = tmpdir / "darker.mp4"
        # Use default thresholds
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"))
        
        # Should fail ONLY on darkening (mean and stddev should pass)
        assert not result['passed'], "Clip >5% darker than source should FAIL"
        assert result['mean'] >= 16, f"Mean should pass (>= 16), got {result['mean']}"
        assert result['stddev'] >= 12, f"Stddev should pass (>= 12), got {result['stddev']}"
        
        assert 'source_comparison' in result
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None and sc['darkening_pct'] > 5, \
            f"Expected darkening > 5%, got {sc['darkening_pct']:.1f}%"
        
        # Verify darkening is the ONLY error
        darkening_errors = [e for e in result['errors'] if 'darker than source' in e]
        assert len(darkening_errors) == 1, f"Should have exactly 1 darkening error, got {len(result['errors'])} total errors"
        
        print(f"✓ Darker-than-source test passed: {sc['darkening_pct']:.1f}% > 5%, "
              f"fails ONLY on darkening (mean={result['mean']:.1f}, stddev={result['stddev']:.1f})")


def test_noisy_clip_stddev():
    """Clip with exact gradient pattern to verify stddev calculation.
    
    Creates uniform ramp spanning limited Y 16-235, which after full-range decode
    becomes 0-255. Expected population stddev: 255/sqrt(12) = 73.61
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create gradient spanning limited-range Y 16-235 across width
        # After full-range decode: uniform 0-255 ramp
        # Population stddev for uniform distribution [0, 255]: 255/sqrt(12) = 73.61
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d=1",
            "-vf", "geq=lum='16+219*X/(W-1)':cb=128:cr=128",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(tmpdir / "gradient.mp4")
        ]
        
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise AssertionError("Failed to create gradient test clip")
        
        video = tmpdir / "gradient.mp4"
        # Use default thresholds
        result = check_frame0_cover(str(video))
        
        # Exact expectations for uniform 0-255 ramp
        expected_mean = 127.5
        expected_stddev = 255 / (12 ** 0.5)  # 73.61
        
        assert result['passed'], f"Gradient clip should PASS, but got errors: {result['errors']}"
        assert result['mean'] is not None, "Mean should not be None"
        assert abs(result['mean'] - expected_mean) <= 1.0, \
            f"Expected mean={expected_mean:.1f} ±1.0, got {result['mean']:.1f}"
        assert result['stddev'] is not None, "Stddev should not be None"
        assert abs(result['stddev'] - expected_stddev) <= 1.0, \
            f"Expected stddev={expected_stddev:.2f} ±1.0, got {result['stddev']:.1f}"
        
        print(f"✓ Gradient clip test passed: mean={result['mean']:.1f} (expected 127.5±1), "
              f"stddev={result['stddev']:.1f} (expected 73.61±1)")


def test_slightly_darker_passes():
    """Clip ~3% darker than source must PASS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create textured source: white text on gray background
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#808080:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create slightly darker video: same text pattern but dimmed ~3%
        # Use RGB(124, 124, 124) → Y ≈ 124 (source Y ≈ 128) = ~3% darker
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#7C7C7C:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(tmpdir / "slightly_darker.mp4")
        ]
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise AssertionError("Failed to create slightly darker test clip")
        
        video = tmpdir / "slightly_darker.mp4"
        # Use default thresholds
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"))
        
        # Should pass all checks
        assert result['passed'], f"Clip ~3% darker than source should PASS, but got errors: {result['errors']}"
        assert result['mean'] >= 16, f"Mean should pass, got {result['mean']}"
        assert result['stddev'] >= 12, f"Stddev should pass, got {result['stddev']}"
        
        assert 'source_comparison' in result
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None and sc['darkening_pct'] <= 5, \
            f"Expected darkening <= 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Slightly-darker test passed: {sc['darkening_pct']:.1f}% <= 5%, correctly PASSED "
              f"(mean={result['mean']:.1f}, stddev={result['stddev']:.1f})")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    print("Running frame-0 quality tests with real clips...\n")
    
    # Verify CLI defaults match spec
    from test_frame0_cover import check_frame0_cover
    import inspect
    sig = inspect.signature(check_frame0_cover)
    assert sig.parameters['min_mean'].default == 16, "Default min_mean must be 16"
    assert sig.parameters['min_stddev'].default == 12, "Default min_stddev must be 12"
    assert sig.parameters['max_darkening'].default == 5, "Default max_darkening must be 5"
    print("✓ CLI defaults verified: min_mean=16, min_stddev=12, max_darkening=5\n")
    
    test_dark_clip_fails()
    test_flat_clip_fails()
    test_good_clip_passes()
    test_darker_than_source_fails()
    test_slightly_darker_passes()
    test_noisy_clip_stddev()
    
    print("\n✅ All frame-0 real clip tests passed (0 skipped, 6 assertions)!")
