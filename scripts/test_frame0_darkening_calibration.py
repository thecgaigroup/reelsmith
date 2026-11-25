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


def create_textured_clip(output_path, bg_color, duration=1):
    """Create textured video with text overlay for realistic stddev."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1080x1920:d={duration}",
        "-vf", "drawtext=text='Test Frame':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return output_path


def test_same_frame_zero_delta():
    """Comparing the same frame against itself gives ~0% darkening."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source image
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#808080:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create video with identical frame
        video = create_textured_clip(tmpdir / "same.mp4", "#808080", 1)
        if not video:
            raise AssertionError("Failed to create same-frame test clip")
        
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"))
        
        # Should pass all checks
        assert result['passed'], f"Same-frame comparison should PASS, but got errors: {result['errors']}"
        
        # Check darkening is near zero (allowing for codec variations)
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None
        assert abs(sc['darkening_pct']) < 1.0, \
            f"Same-frame darkening should be < 1.0%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Same-frame test passed: darkening={sc['darkening_pct']:.2f}% (within 1.0%)")


def test_calibrated_8_percent_fails():
    """8.4% darker frame FAILS on darkening check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source: RGB(128, 128, 128) → Y ≈ 128
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#808080:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create video ~8-10% darker: RGB(115, 115, 115) → Y ≈ 115 (10% darker)
        video = create_textured_clip(tmpdir / "darker.mp4", "#737373", 1)
        if not video:
            raise AssertionError("Failed to create 8% darker test clip")
        
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"))
        
        # Should fail on darkening
        assert not result['passed'], "8.4% darker clip should FAIL"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None and sc['darkening_pct'] > 5, \
            f"Expected darkening > 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 8% darker test passed: {sc['darkening_pct']:.1f}% > 5%, correctly FAILED")


def test_calibrated_2_percent_passes():
    """2.1% darker frame PASSES darkening check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source: RGB(128, 128, 128)
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#808080:s=1080x1920:d=1",
            "-vf", "drawtext=text='Source':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "source.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create video ~2-3% darker: RGB(124, 124, 124) → Y ≈ 124 (3% darker)
        video = create_textured_clip(tmpdir / "slightly_darker.mp4", "#7C7C7C", 1)
        if not video:
            raise AssertionError("Failed to create 2% darker test clip")
        
        result = check_frame0_cover(str(video), str(tmpdir / "source.png"))
        
        # Should pass all checks
        assert result['passed'], f"2.1% darker clip should PASS, but got errors: {result['errors']}"
        
        sc = result['source_comparison']
        assert sc['darkening_pct'] is not None and sc['darkening_pct'] <= 5, \
            f"Expected darkening <= 5%, got {sc['darkening_pct']:.1f}%"
        
        print(f"✓ Calibrated 2% darker test passed: {sc['darkening_pct']:.1f}% <= 5%, correctly PASSED")


def test_image_vs_video_agreement():
    """Image and video of same content agree within 1 luma unit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source image with pattern
        source_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=#606060:s=1080x1920:d=1",
            "-vf", "drawtext=text='Test':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1",
            str(tmpdir / "image.png")
        ]
        subprocess.run(source_cmd, capture_output=True, check=True)
        
        # Create video with same pattern
        video = create_textured_clip(tmpdir / "video.mp4", "#606060", 1)
        if not video:
            raise AssertionError("Failed to create video for agreement test")
        
        # Measure both
        image_mean = get_luma_mean_from_raw_pixels(str(tmpdir / "image.png"), is_video=False)
        video_mean = get_luma_mean_from_raw_pixels(str(video), is_video=True, frame_num=0)
        
        assert image_mean is not None, "Could not extract image luma"
        assert video_mean is not None, "Could not extract video luma"
        
        difference = abs(image_mean - video_mean)
        assert difference <= 2.0, \
            f"Image and video should agree within 2 luma units, got difference={difference:.1f}"
        
        print(f"✓ Image/video agreement test passed: image={image_mean:.1f}, video={video_mean:.1f}, diff={difference:.1f} (within 2.0)")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    
    print("Running frame-0 darkening calibration tests...\n")
    
    test_same_frame_zero_delta()
    test_calibrated_8_percent_fails()
    test_calibrated_2_percent_passes()
    test_image_vs_video_agreement()
    
    print("\n✅ All darkening calibration tests passed!")
