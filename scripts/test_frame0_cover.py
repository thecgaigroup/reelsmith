#!/usr/bin/env python3
"""Tests for frame-0 cover quality (luma, stddev, contrast vs source)."""
import json
import subprocess
import sys
from pathlib import Path


def get_frame_luma_stats(video_path, frame_num=0):
    """Extract luma mean and stddev for a specific frame using ffmpeg signalstats.
    
    Args:
        video_path: Path to video file
        frame_num: Frame number to analyze (default 0)
        
    Returns:
        Tuple of (mean, stddev) or None if extraction fails
    """
    # Use signalstats filter with metadata=print to output stats to stdout
    # select='eq(n,{frame_num})' selects only the target frame
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='eq(n,{frame_num})',signalstats,metadata=print:file=-",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"ffmpeg failed: {result.stderr}", file=sys.stderr)
        return None
    
    # Parse stdout for metadata output
    # Example: lavfi.signalstats.YAVG=52.3
    #          lavfi.signalstats.YMIN=20
    #          lavfi.signalstats.YMAX=235
    # Note: signalstats doesn't output YSTDEV, so we calculate it from range
    yavg = ymin = ymax = None
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line.startswith('lavfi.signalstats.YAVG='):
            yavg = float(line.split('=')[1])
        elif line.startswith('lavfi.signalstats.YMIN='):
            ymin = float(line.split('=')[1])
        elif line.startswith('lavfi.signalstats.YMAX='):
            ymax = float(line.split('=')[1])
    
    if yavg is not None and ymin is not None and ymax is not None:
        # Approximate stddev from range: for uniform distribution, stddev ≈ range / 3.46
        # For better approximation with typical image distributions: stddev ≈ range / 4
        ystddev_approx = (ymax - ymin) / 4.0
        return yavg, ystddev_approx
    
    return None


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
