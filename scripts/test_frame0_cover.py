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
    # Use signalstats filter with metadata mode to get Y (luma) stats
    # select='eq(n,{frame_num})' selects only the target frame
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='eq(n,{frame_num})',signalstats=stat=tout+vrep+brng:out=brng",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"ffmpeg failed: {result.stderr}", file=sys.stderr)
        return None
    
    # Parse stderr for signalstats output
    # Example: [Parsed_signalstats_1 @ ...] YMIN:16 YLOW:16 YAVG:52.3 YHIGH:235 YMAX:235 YDIF:219 YSTDEV:51.2
    for line in result.stderr.split('\n'):
        if 'signalstats' in line and 'YAVG:' in line and 'YSTDEV:' in line:
            # Extract YAVG and YSTDEV
            parts = line.split()
            yavg = ystdev = None
            for part in parts:
                if part.startswith('YAVG:'):
                    yavg = float(part.split(':')[1])
                elif part.startswith('YSTDEV:'):
                    ystdev = float(part.split(':')[1])
            
            if yavg is not None and ystdev is not None:
                return yavg, ystdev
    
    # Fallback: use ffprobe with signalstats
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "frame=pkt_pts_time",
        "-of", "json",
        str(video_path)
    ]
    # This is a simplified fallback - in practice we'd need frame metadata
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
        "-vf", "signalstats=stat=tout+vrep+brng",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        return None
    
    for line in result.stderr.split('\n'):
        if 'signalstats' in line and 'YAVG:' in line:
            parts = line.split()
            for part in parts:
                if part.startswith('YAVG:'):
                    return float(part.split(':')[1])
    
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


def check_frame0_cover(video_path, source_image_path=None):
    """Full frame-0 cover check: luma, stddev, and optional source comparison.
    
    Args:
        video_path: Path to video to check
        source_image_path: Optional path to source hero art for comparison
        
    Returns:
        Dict with 'passed', 'mean', 'stddev', 'errors' keys
    """
    passed, mean, stddev, errors = test_frame0_luma_requirements(video_path)
    
    result = {
        'passed': passed,
        'mean': mean,
        'stddev': stddev,
        'errors': errors
    }
    
    if source_image_path:
        src_passed, vid_mean, src_mean, dark_pct, src_error = test_frame0_vs_source_brightness(
            video_path, source_image_path
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
    
    result = check_frame0_cover(args.video, args.source)
    
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
