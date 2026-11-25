#!/usr/bin/env python3
"""Calibration tests for frame-0 darkening measurement accuracy."""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_frame0_cover import check_frame0_cover, get_luma_mean_from_raw_pixels


def create_test_clip(output_path, color_hex, duration=1):
    """Create a test video with solid color background."""
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


def create_textured_clip(output_path, bg_color, duration=1, brightness_scale=1.0):
    """Create textured video with text overlay for realistic stddev.
    
    Args:
        output_path: Where to save the video
        bg_color: Background color hex
        duration: Video duration in seconds
        brightness_scale: Multiply luma by this factor (via lutyuv filter)
    """
    vf = "drawtext=text='Test Frame':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"
    
    if brightness_scale != 1.0:
        # Scale luma while preserving chroma
        vf += f",lutyuv=y='val*{brightness_scale}'"
    
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1080x1920:d={duration}",
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return output_path


def create_textured_image(output_path, bg_color):
    """Create textured image that goes through yuv420p like video.
    
    Ensures image and video paths are identical for same-frame comparisons.
    """
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1080x1920:d=1",
        "-vf", "drawtext=text='Test Frame':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2,format=yuv420p",
        "-frames:v", "1",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return output_path


def test_same_frame_zero_delta():
    """Comparing the same frame against itself gives ~0% darkening.
    
    Both image and video go through yuv420p to ensure identical conversion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source image (goes through yuv420p like video)
        source = create_textured_image(tmpdir / "source.png", "#808080")
        if not source:
            raise AssertionError("Failed to create source image")
        
        # Create video with identical content and conversion
        video = create_textured_clip(tmpdir / "same.mp4", "#808080", 1)
        if not video:
            raise AssertionError("Failed to create same-frame test clip")
        
        result = check_frame0_cover(str(video), str(source))
        
        # Should pass all checks
        assert result['passed'], f"Same-frame comparison should PASS, but got errors: {result['errors']}"
        
        # Check darkening is near zero
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None
        assert abs(sc['darkening_pct']) < 0.5, \
            f"Same-frame darkening should be < 0.5%, got {sc['darkening_pct']:.2f}%"
        
        print(f"✓ Same-frame test passed: darkening={sc['darkening_pct']:.2f}% (within 0.5%)")


def test_calibrated_7_8_percent_fails():
    """Measured 7.8% ± 0.5% darker frame FAILS on darkening check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source (through yuv420p)
        source = create_textured_image(tmpdir / "source.png", "#808080")
        if not source:
            raise AssertionError("Failed to create source image")
        
        # Create video ~7.8% darker via brightness scaling (calibrated for 1080x1920)
        video = create_textured_clip(tmpdir / "darker_7.mp4", "#808080", 1, brightness_scale=0.9286)
        if not video:
            raise AssertionError("Failed to create 7.8% darker test clip")
        
        result = check_frame0_cover(str(video), str(source))
        
        # Should fail on darkening
        assert not result['passed'], "7.8% darker clip should FAIL"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None, "Darkening percentage should be measured"
        
        # Verify measured darkening is within calibration band (±0.5% for quantization)
        assert 7.3 <= sc['darkening_pct'] <= 8.3, \
            f"Measured darkening should be 7.8% ± 0.5%, got {sc['darkening_pct']:.1f}%"
        
        # Verify it fails the check
        assert sc['darkening_pct'] > 5, \
            f"Expected darkening > 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 7.8% darker test passed: measured={sc['darkening_pct']:.1f}% (7.8±0.5), correctly FAILED")


def test_calibrated_2_4_percent_passes():
    """Measured 2.4% ± 0.5% darker frame PASSES darkening check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source (through yuv420p)
        source = create_textured_image(tmpdir / "source.png", "#7F7F7F")
        if not source:
            raise AssertionError("Failed to create source image")
        
        # Create video ~2.4% darker via brightness scaling (calibrated for 1080x1920)
        video = create_textured_clip(tmpdir / "slightly_darker.mp4", "#7F7F7F", 1, brightness_scale=0.979)
        if not video:
            raise AssertionError("Failed to create 2.4% darker test clip")
        
        result = check_frame0_cover(str(video), str(source))
        
        # Should pass all checks
        assert result['passed'], f"2.4% darker clip should PASS, but got errors: {result['errors']}"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None, "Darkening percentage should be measured"
        
        # Verify measured darkening is within calibration band (±0.5% for quantization)
        assert 1.9 <= sc['darkening_pct'] <= 2.9, \
            f"Measured darkening should be 2.4% ± 0.5%, got {sc['darkening_pct']:.1f}%"
        
        # Verify it passes the check
        assert sc['darkening_pct'] <= 5, \
            f"Expected darkening <= 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 2.4% darker test passed: measured={sc['darkening_pct']:.1f}% (2.4±0.5), correctly PASSED")


def test_calibrated_6_2_percent_fails():
    """Measured 6.2% ± 0.5% darker frame FAILS (boundary test)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source (through yuv420p)
        source = create_textured_image(tmpdir / "source.png", "#808080")
        if not source:
            raise AssertionError("Failed to create source image")
        
        # Create video ~6.2% darker via brightness scaling (calibrated for 1080x1920)
        video = create_textured_clip(tmpdir / "darker_6.mp4", "#808080", 1, brightness_scale=0.945)
        if not video:
            raise AssertionError("Failed to create 6.2% darker test clip")
        
        result = check_frame0_cover(str(video), str(source))
        
        # Should fail on darkening
        assert not result['passed'], "6.2% darker clip should FAIL"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None, "Darkening percentage should be measured"
        
        # Verify measured darkening is within calibration band (±0.5% for quantization)
        assert 5.7 <= sc['darkening_pct'] <= 6.7, \
            f"Measured darkening should be 6.2% ± 0.5%, got {sc['darkening_pct']:.1f}%"
        
        # Verify it fails the check
        assert sc['darkening_pct'] > 5, \
            f"Expected darkening > 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 6.2% darker test passed: measured={sc['darkening_pct']:.1f}% (6.2±0.5), correctly FAILED")


def test_calibrated_3_9_percent_passes():
    """Measured 3.9% ± 0.5% darker frame PASSES (boundary test)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source (through yuv420p)
        source = create_textured_image(tmpdir / "source.png", "#808080")
        if not source:
            raise AssertionError("Failed to create source image")
        
        # Create video ~3.9% darker via brightness scaling (calibrated for 1080x1920)
        video = create_textured_clip(tmpdir / "darker_4.mp4", "#808080", 1, brightness_scale=0.970)
        if not video:
            raise AssertionError("Failed to create 3.9% darker test clip")
        
        result = check_frame0_cover(str(video), str(source))
        
        # Should pass all checks
        assert result['passed'], f"3.9% darker clip should PASS, but got errors: {result['errors']}"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None, "Darkening percentage should be measured"
        
        # Verify measured darkening is within calibration band (±0.5% for quantization)
        assert 3.4 <= sc['darkening_pct'] <= 4.4, \
            f"Measured darkening should be 3.9% ± 0.5%, got {sc['darkening_pct']:.1f}%"
        
        # Verify it passes the check
        assert sc['darkening_pct'] <= 5, \
            f"Expected darkening <= 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 3.9% darker test passed: measured={sc['darkening_pct']:.1f}% (3.9±0.5), correctly PASSED")


def test_image_vs_video_agreement():
    """Image and video of same content agree within 1 luma unit.
    
    Both go through identical yuv420p conversion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create image (through yuv420p)
        image = create_textured_image(tmpdir / "image.png", "#606060")
        if not image:
            raise AssertionError("Failed to create image")
        
        # Create video with same pattern and conversion
        video = create_textured_clip(tmpdir / "video.mp4", "#606060", 1)
        if not video:
            raise AssertionError("Failed to create video for agreement test")
        
        # Measure both
        image_mean = get_luma_mean_from_raw_pixels(str(image), is_video=False)
        video_mean = get_luma_mean_from_raw_pixels(str(video), is_video=True, frame_num=0)
        
        assert image_mean is not None, "Could not extract image luma"
        assert video_mean is not None, "Could not extract video luma"
        
        difference = abs(image_mean - video_mean)
        assert difference <= 1.0, \
            f"Image and video should agree within 1.0 luma unit, got difference={difference:.1f}"
        
        print(f"✓ Image/video agreement test passed: image={image_mean:.1f}, video={video_mean:.1f}, diff={difference:.1f} (within 1.0)")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    print("Running frame-0 darkening calibration tests...\n")
    
    test_same_frame_zero_delta()
    test_calibrated_7_8_percent_fails()
    test_calibrated_2_4_percent_passes()
    test_calibrated_6_2_percent_fails()
    test_calibrated_3_9_percent_passes()
    test_image_vs_video_agreement()
    
    print("\n✅ All darkening calibration tests passed!")
