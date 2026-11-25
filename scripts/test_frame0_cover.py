#!/usr/bin/env python3
"""Tests for frame-0 cover quality (luma, stddev, contrast vs source)."""
import json
import subprocess
import sys
from pathlib import Path


def get_frame_luma_stats(video_path, frame_num=0):
    """Extract luma mean and stddev for a specific frame.
    
    Gets YAVG from signalstats metadata (limited-range 16-235), then decodes 
    frame as raw grayscale (full-range 0-255) and computes true population stddev.
    
    Cross-checks that converted YAVG matches raw pixel mean within 1.0, raising
    AssertionError if disagreement exceeds tolerance.
    
    **Range conversion:** signalstats reports limited-range Y (16-235), while raw
    grayscale pixels are full-range (0-255). Conversion: `(Y_limited - 16) * 255 / 219`.
    
    **Thresholds:** The 16/12/5% thresholds are full-range 0-255 luma values.
    
    Args:
        video_path: Path to video file
        frame_num: Frame number to analyze (default 0)
        
    Returns:
        Tuple of (mean, stddev) or None if extraction fails
        
    Raises:
        AssertionError: If YAVG (converted) disagrees with raw mean by > 1.0
    """
    # Get YAVG from signalstats metadata (limited-range)
    cmd_meta = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='eq(n,{frame_num})',signalstats,metadata=print:file=-",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd_meta, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"ffmpeg signalstats failed: {result.stderr}", file=sys.stderr)
        return None
    
    yavg_limited = None
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line.startswith('lavfi.signalstats.YAVG='):
            yavg_limited = float(line.split('=')[1])
            break
    
    if yavg_limited is None:
        return None
    
    # Decode frame as raw grayscale (full-range) to compute real stddev
    cmd_raw = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='eq(n,{frame_num})'",
        "-frames:v", "1",
        "-f", "rawvideo",
        "-pix_fmt", "gray",
        "-"
    ]
    
    result = subprocess.run(cmd_raw, capture_output=True, check=False)
    if result.returncode != 0:
        print(f"ffmpeg rawvideo failed", file=sys.stderr)
        return None
    
    raw_pixels = result.stdout
    if not raw_pixels:
        return None
    
    # Compute mean and stddev from raw pixels
    try:
        import numpy as np
        pixels = np.frombuffer(raw_pixels, dtype=np.uint8)
        pixel_mean = float(np.mean(pixels))
        pixel_stddev = float(np.std(pixels, ddof=0))  # Population stddev
    except ImportError:
        # Fallback without numpy
        import statistics
        pixels = list(raw_pixels)
        pixel_mean = statistics.mean(pixels)
        pixel_stddev = statistics.pstdev(pixels)
    
    # Convert signalstats YAVG from limited-range (16-235) to full-range (0-255)
    yavg_full = (yavg_limited - 16) * 255 / 219
    
    # Assert YAVG (converted) agrees with raw pixel mean within 1.0
    disagreement = abs(yavg_full - pixel_mean)
    assert disagreement <= 1.0, \
        f"signalstats YAVG={yavg_limited:.1f} (full={yavg_full:.1f}) disagrees with " \
        f"raw pixel mean={pixel_mean:.1f} by {disagreement:.1f} (max 1.0)"
    
    return pixel_mean, pixel_stddev


def get_image_luma_mean(image_path):
    """Get mean luma from an image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Float mean luma value (0-255) or None if extraction fails
    """
    cmd = [
        "ffmpeg", "-i", str(image_path),
        "-vf", "signalstats,metadata=print:file=-",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        return None
    
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line.startswith('lavfi.signalstats.YAVG='):
            return float(line.split('=')[1])
    
    return None


def test_frame0_luma_requirements(video_path, min_mean=16, min_stddev=12):
    """Test that frame 0 meets luma mean and stddev requirements.
    
    Args:
        video_path: Path to video file to test
        min_mean: Minimum luma mean (default 16)
        min_stddev: Minimum luma stddev (default 12)
        
    Returns:
        Tuple of (passed, mean, stddev, errors)
    """
    stats = get_frame_luma_stats(video_path, frame_num=0)
    
    if stats is None:
        return False, None, None, ["Could not extract luma stats from frame 0"]
    
    mean, stddev = stats
    errors = []
    
    if mean < min_mean:
        errors.append(f"Luma mean {mean:.1f} < {min_mean} (too dark)")
    
    if stddev < min_stddev:
        errors.append(f"Luma stddev {stddev:.1f} < {min_stddev} (too flat/low contrast)")
    
    passed = len(errors) == 0
    return passed, mean, stddev, errors


def test_frame0_vs_source_brightness(video_path, source_image_path, max_darkening_pct=5):
    """Test that frame 0 is not more than max_darkening_pct darker than source.
    
    Args:
        video_path: Path to video file
        source_image_path: Path to source hero art image
        max_darkening_pct: Maximum allowed darkening percentage (default 5)
        
    Returns:
        Tuple of (passed, video_mean, source_mean, darkening_pct, error)
    """
    video_stats = get_frame_luma_stats(video_path, frame_num=0)
    source_mean = get_image_luma_mean(source_image_path)
    
    if video_stats is None:
        return False, None, None, None, "Could not extract video frame 0 stats"
    
    if source_mean is None:
        return False, None, None, None, "Could not extract source image stats"
    
    video_mean = video_stats[0]
    
    # Calculate darkening percentage
    darkening_pct = ((source_mean - video_mean) / source_mean) * 100 if source_mean > 0 else 0
    
    if darkening_pct > max_darkening_pct:
        error = f"Frame 0 is {darkening_pct:.1f}% darker than source (max {max_darkening_pct}%)"
        return False, video_mean, source_mean, darkening_pct, error
    
    return True, video_mean, source_mean, darkening_pct, None


def check_frame0_cover(video_path, source_image_path=None, min_mean=16, min_stddev=12, max_darkening=5):
    """Full frame-0 cover check: luma, stddev, and optional source comparison.
    
    Args:
        video_path: Path to video to check
        source_image_path: Optional path to source hero art for comparison
        min_mean: Minimum luma mean (default 16)
        min_stddev: Minimum luma stddev (default 12)
        max_darkening: Maximum darkening vs source % (default 5)
        
    Returns:
        Dict with 'passed', 'mean', 'stddev', 'errors' keys
    """
    passed, mean, stddev, errors = test_frame0_luma_requirements(video_path, min_mean, min_stddev)
    
    result = {
        'passed': passed,
        'mean': mean,
        'stddev': stddev,
        'errors': errors
    }
    
    if source_image_path:
        src_passed, vid_mean, src_mean, dark_pct, src_error = test_frame0_vs_source_brightness(
            video_path, source_image_path, max_darkening
        )
        result['source_comparison'] = {
            'passed': src_passed,
            'video_mean': vid_mean,
            'source_mean': src_mean,
            'darkening_pct': dark_pct,
            'error': src_error
        }
        result['passed'] = result['passed'] and src_passed
        if src_error:
            result['errors'].append(src_error)
    
    return result


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Check frame 0 cover quality")
    ap.add_argument("video", help="Video file to check")
    ap.add_argument("--source", help="Source hero art image (optional)")
    ap.add_argument("--min-mean", type=float, default=16, help="Minimum luma mean (default 16)")
    ap.add_argument("--min-stddev", type=float, default=12, help="Minimum luma stddev (default 12)")
    ap.add_argument("--max-darkening", type=float, default=5, help="Max darkening vs source %% (default 5)")
    args = ap.parse_args()
    
    # Pass thresholds to check_frame0_cover
    result = check_frame0_cover(args.video, args.source, 
                                min_mean=args.min_mean, 
                                min_stddev=args.min_stddev, 
                                max_darkening=args.max_darkening)
    
    print(f"Frame 0 cover check: {'PASS' if result['passed'] else 'FAIL'}")
    if result['mean'] is not None:
        print(f"  Luma mean: {result['mean']:.1f} (>= {args.min_mean})")
    if result['stddev'] is not None:
        print(f"  Luma stddev: {result['stddev']:.1f} (>= {args.min_stddev})")
    
    if 'source_comparison' in result:
        sc = result['source_comparison']
        if sc['darkening_pct'] is not None:
            print(f"  Darkening vs source: {sc['darkening_pct']:.1f}% (<= {args.max_darkening}%)")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
        sys.exit(1)
    
    print("\n✓ All frame 0 requirements met")
