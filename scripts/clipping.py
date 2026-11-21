#!/usr/bin/env python3
"""Long-form to vertical 9:16 clipping pipeline.

  clipping.py process VIDEO --out OUTPUT_DIR [--min-clip 10] [--max-clip 60] [--top-n 5]

Workflow:
1. Transcribe video (reuses parakeet/WhisperX if available)
2. Detect highlight moments using transcript + audio energy
3. Track faces and generate 9:16 crop windows
4. Export clips with face-tracked crops
5. Generate captions for each clip (shifted to clip timecode)
6. Review each clip (aspect, duration, quality)

Output structure:
  OUTPUT_DIR/
    highlights.json           # Detected highlights with scores
    tracking.json             # Face tracking data
    clip_001/
      video.mp4              # 9:16 clipped video
      captions.srt           # Shifted captions
      captions.ass           # ASS for burn-in
      burned.mp4             # Final with burned captions
      review/                # review.py outputs
    clip_002/
      ...
    summary.json             # Overall summary
"""
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

def run_cmd(cmd, check=True):
    """Run command and return result."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(str(c) for c in cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result

def transcribe_video(video_path, output_path):
    """Transcribe video using captions.py estimate or external tools."""
    print("Checking for existing transcript...", file=sys.stderr)
    
    # Check if transcript already exists
    if output_path.exists():
        print(f"Using existing transcript: {output_path}", file=sys.stderr)
        return
    
    print("Note: Automatic transcription requires parakeet or WhisperX (not yet implemented)", 
          file=sys.stderr)
    print("For now, provide a words.json transcript with --transcript option", file=sys.stderr)
    sys.exit(1)

def extract_clip(video_path, start, end, output_path):
    """Extract clip segment using ffmpeg."""
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(video_path),
        "-c", "copy",
        str(output_path)
    ]
    run_cmd(cmd)

def shift_captions(words, offset):
    """Shift caption timings by offset seconds."""
    shifted = []
    for w in words:
        shifted.append({
            "text": w["text"],
            "start": max(0, w["start"] - offset),
            "end": max(0, w["end"] - offset)
        })
    return shifted

def shift_srt_pysubs2(srt_path, offset_seconds, output_path):
    """Shift SRT file using pysubs2."""
    try:
        import pysubs2
    except ImportError:
        print("Warning: pysubs2 not available, using fallback shift", file=sys.stderr)
        # Fallback: manual shift (simplified)
        return shift_srt_manual(srt_path, offset_seconds, output_path)
    
    subs = pysubs2.load(str(srt_path))
    
    # Shift all events
    offset_ms = int(offset_seconds * 1000)
    subs.shift(ms=offset_ms)
    
    subs.save(str(output_path))

def shift_srt_manual(srt_path, offset_seconds, output_path):
    """Manual SRT shift fallback."""
    import re
    
    content = Path(srt_path).read_text()
    offset_ms = int(offset_seconds * 1000)
    
    def shift_timestamp(match):
        """Shift a timestamp string."""
        h, m, s, ms = match.groups()
        total_ms = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
        total_ms = max(0, total_ms + offset_ms)
        
        new_h = total_ms // 3600000
        new_m = (total_ms % 3600000) // 60000
        new_s = (total_ms % 60000) // 1000
        new_ms = total_ms % 1000
        
        return f"{new_h:02d}:{new_m:02d}:{new_s:02d},{new_ms:03d}"
    
    # Replace timestamps
    pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    shifted = re.sub(pattern, shift_timestamp, content)
    
    Path(output_path).write_text(shifted)

def process_clip(video_path, highlight, clip_dir, words, tracking_data):
    """Process a single clip: extract, crop, captions, review."""
    clip_dir.mkdir(parents=True, exist_ok=True)
    
    start = highlight["start"]
    end = highlight["end"]
    duration = end - start
    
    print(f"\nProcessing clip: {start:.1f}s - {end:.1f}s ({duration:.1f}s)", file=sys.stderr)
    print(f"  Hook: {highlight['hook']}", file=sys.stderr)
    print(f"  Score: {highlight['score']:.2f} ({highlight['reason']})", file=sys.stderr)
    
    # Step 1: Extract raw clip
    raw_clip = clip_dir / "raw.mp4"
    print("  Extracting segment...", file=sys.stderr)
    extract_clip(video_path, start, end, raw_clip)
    
    # Step 2: Apply face-tracked crop
    cropped_clip = clip_dir / "video.mp4"
    print("  Applying face-tracked 9:16 crop...", file=sys.stderr)
    apply_clip_crop(raw_clip, tracking_data, start, end, cropped_clip)
    
    # Step 3: Generate shifted captions
    print("  Generating captions...", file=sys.stderr)
    clip_words = [w for w in words if start <= w["start"] < end]
    shifted_words = shift_captions(clip_words, start)
    
    words_json = clip_dir / "words.json"
    words_json.write_text(json.dumps(shifted_words, indent=2))
    
    # Build captions
    captions_cmd = [
        "python3", str(HERE / "captions.py"), "build",
        "--words", str(words_json),
        "-o", str(clip_dir / "captions"),
        "--profile", "social",
        "--aspect", "9:16"
    ]
    run_cmd(captions_cmd)
    
    # Step 4: Burn captions
    if (clip_dir / "captions.ass").exists():
        print("  Burning captions...", file=sys.stderr)
        burned_clip = clip_dir / "burned.mp4"
        burn_cmd = [
            "python3", str(HERE / "captions.py"), "burn",
            str(cropped_clip),
            str(clip_dir / "captions.ass"),
            "-o", str(burned_clip)
        ]
        run_cmd(burn_cmd)
    
    # Step 5: Review
    review_dir = clip_dir / "review"
    print("  Running review checks...", file=sys.stderr)
    final_clip = clip_dir / "burned.mp4" if (clip_dir / "burned.mp4").exists() else cropped_clip
    
    review_cmd = [
        "python3", str(HERE / "review.py"), "check",
        str(final_clip),
        "--out", str(review_dir),
        "--preset", "reels",
        "--expect-seconds", str(int(duration))
    ]
    run_cmd(review_cmd)
    
    print(f"  ✓ Clip complete: {final_clip}", file=sys.stderr)
    
    return {
        "clip_dir": str(clip_dir),
        "highlight": highlight,
        "video": str(final_clip),
        "captions_srt": str(clip_dir / "captions.srt") if (clip_dir / "captions.srt").exists() else None,
        "review_dir": str(review_dir)
    }

def apply_clip_crop(input_video, tracking_data, start_time, end_time, output_video):
    """Apply crop for a specific time segment."""
    crop_windows = tracking_data.get("crop_windows", [])
    fps = tracking_data["fps"]
    
    # Find crop window for the middle of the segment
    mid_time = (start_time + end_time) / 2
    mid_frame = int(mid_time * fps)
    
    # Find nearest crop window
    crop_window = None
    for cw in crop_windows:
        if cw["frame"] >= mid_frame:
            crop_window = cw
            break
    
    if not crop_window and crop_windows:
        crop_window = crop_windows[-1]
    
    if not crop_window:
        print("Warning: No crop window found, using center crop", file=sys.stderr)
        # Get video dimensions and compute center crop
        info_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
                   "-show_entries", "stream=width,height", "-of", "json", str(input_video)]
        result = run_cmd(info_cmd, check=True)
        info = json.loads(result.stdout)
        w = info["streams"][0]["width"]
        h = info["streams"][0]["height"]
        
        # Compute 9:16 crop
        crop_h = h
        crop_w = int(crop_h * 9 / 16)
        if crop_w > w:
            crop_w = w
            crop_h = int(crop_w * 16 / 9)
        
        x = (w - crop_w) // 2
        y = (h - crop_h) // 2
        
        crop_filter = f"crop={crop_w}:{crop_h}:{x}:{y}"
    else:
        x, y, w, h = crop_window["x"], crop_window["y"], crop_window["w"], crop_window["h"]
        crop_filter = f"crop={w}:{h}:{x}:{y}"
    
    # Apply crop and scale to 1080x1920 (vertical 9:16 format)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_video),
        "-vf", f"{crop_filter},scale=1080:1920",
        "-c:a", "copy",
        str(output_video)
    ]
    run_cmd(cmd)

def process_video(video_path, output_dir, transcript_path=None, 
                 min_clip=10, max_clip=60, top_n=5):
    """Main processing pipeline."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing {video_path}", file=sys.stderr)
    print(f"Output directory: {output_dir}", file=sys.stderr)
    
    # Step 1: Transcribe or load transcript
    if transcript_path and Path(transcript_path).exists():
        words_json = output_dir / "transcript.json"
        shutil.copy(transcript_path, words_json)
        print(f"Using provided transcript: {transcript_path}", file=sys.stderr)
    else:
        words_json = output_dir / "transcript.json"
        transcribe_video(video_path, words_json)
    
    # Load words
    words_data = json.loads(words_json.read_text())
    if isinstance(words_data, dict):
        words = words_data.get("words", [])
    else:
        words = words_data
    
    print(f"Loaded {len(words)} words from transcript", file=sys.stderr)
    
    # Step 2: Detect highlights
    print("\nDetecting highlights...", file=sys.stderr)
    highlights_json = output_dir / "highlights.json"
    highlights_cmd = [
        "python3", str(HERE / "highlights.py"), "detect",
        str(video_path),
        "--transcript", str(words_json),
        "--out", str(highlights_json),
        "--min-clip", str(min_clip),
        "--max-clip", str(max_clip),
        "--top-n", str(top_n)
    ]
    run_cmd(highlights_cmd)
    
    highlights = json.loads(highlights_json.read_text())
    print(f"Found {len(highlights)} highlights", file=sys.stderr)
    
    # Step 3: Face tracking
    print("\nPerforming face tracking...", file=sys.stderr)
    tracking_json = output_dir / "tracking.json"
    facetrack_cmd = [
        "python3", str(HERE / "facetrack.py"), "detect",
        str(video_path),
        "--out", str(tracking_json),
        "--aspect", "9:16"
    ]
    run_cmd(facetrack_cmd)
    
    tracking_data = json.loads(tracking_json.read_text())
    
    # Step 4: Process each clip
    print(f"\nProcessing {len(highlights)} clips...", file=sys.stderr)
    results = []
    
    for i, highlight in enumerate(highlights, 1):
        clip_dir = output_dir / f"clip_{i:03d}"
        try:
            result = process_clip(video_path, highlight, clip_dir, words, tracking_data)
            results.append(result)
        except Exception as e:
            print(f"Error processing clip {i}: {e}", file=sys.stderr)
            results.append({
                "clip_dir": str(clip_dir),
                "highlight": highlight,
                "error": str(e)
            })
    
    # Step 5: Generate summary
    summary = {
        "source_video": str(video_path),
        "highlights_count": len(highlights),
        "clips_processed": len([r for r in results if "error" not in r]),
        "clips_failed": len([r for r in results if "error" in r]),
        "tracks_found": len(tracking_data.get("tracks", [])),
        "clips": results
    }
    
    summary_json = output_dir / "summary.json"
    summary_json.write_text(json.dumps(summary, indent=2))
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Processing complete!", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Highlights: {summary['highlights_count']}", file=sys.stderr)
    print(f"Clips processed: {summary['clips_processed']}", file=sys.stderr)
    print(f"Clips failed: {summary['clips_failed']}", file=sys.stderr)
    print(f"Face tracks: {summary['tracks_found']}", file=sys.stderr)
    print(f"\nOutput: {output_dir}", file=sys.stderr)
    print(f"Summary: {summary_json}", file=sys.stderr)
    
    return summary

def fetch_stream_url(url, rights_confirmed=False):
    """Fetch stream URL using yt-dlp (lazy import, optional dependency).
    
    Args:
        url: Stream URL (YouTube, Twitch, etc.)
        rights_confirmed: User must confirm rights to use content
        
    Returns:
        Local file path after download
        
    Raises:
        SystemExit: If rights not confirmed (exits before any import or fetch)
    """
    # CRITICAL: Check rights BEFORE any import or network operation
    if not rights_confirmed:
        print("ERROR: --rights-confirmed is required for URL input", file=sys.stderr)
        print("You must have the rights to record, edit, and use this content.", file=sys.stderr)
        raise SystemExit(1)
    
    try:
        import yt_dlp
    except ImportError:
        print("ERROR: yt-dlp not available", file=sys.stderr)
        print("Install with: pip install -r requirements-stream.txt", file=sys.stderr)
        sys.exit(1)
    
    print(f"Downloading stream from {url}...", file=sys.stderr)
    
    # Use yt-dlp to download
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': '/tmp/stream_download_%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)
    
    print(f"Downloaded to: {downloaded_file}", file=sys.stderr)
    return downloaded_file


def process_stream_highlights(video_source, output_dir, chat_json=None, 
                              min_clip=10, max_clip=30, top_n=5, 
                              chunk_duration=90, rights_confirmed=False,
                              profanity_mask=True):
    """Process stream in chunks for highlight detection.
    
    Stream-highlights mode:
    - Processes video in 90-second chunks
    - Uses chat burst analysis (if chat_json provided)
    - Falls back to RMS loudness analysis
    - 6-second lead-in before peaks
    - stream-pop captions with profanity masking
    - Facecam-aware crop (YuNet/YOLOX if available)
    
    Args:
        video_source: Local file path or URL
        output_dir: Output directory
        chat_json: Path to chat messages JSON (optional)
        min_clip: Minimum clip duration
        max_clip: Maximum clip duration
        top_n: Highlights per chunk
        chunk_duration: Chunk size in seconds (default 90)
        rights_confirmed: Rights confirmation flag (required for URLs)
        profanity_mask: Enable profanity masking in captions
        
    Returns:
        Summary dict
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle URL input
    if video_source.startswith(("http://", "https://")):
        video_path = fetch_stream_url(video_source, rights_confirmed)
    else:
        video_path = video_source
    
    print(f"Processing stream: {video_path}", file=sys.stderr)
    print(f"Mode: stream-highlights (chunk={chunk_duration}s)", file=sys.stderr)
    
    # Load chat messages if provided
    chat_messages = None
    if chat_json:
        sys.path.insert(0, str(HERE))
        from highlights import load_chat_messages
        chat_messages = load_chat_messages(chat_json)
        print(f"Loaded {len(chat_messages)} chat messages", file=sys.stderr)
    
    # Run highlights detection in stream mode
    highlights_json = output_dir / "highlights.json"
    highlights_cmd = [
        "python3", str(HERE / "highlights.py"), "detect",
        str(video_path),
        "--out", str(highlights_json),
        "--mode", "stream",
        "--min-clip", str(min_clip),
        "--max-clip", str(max_clip),
        "--top-n", str(top_n),
    ]
    
    if chat_json:
        highlights_cmd.extend(["--chat", str(chat_json)])
    
    run_cmd(highlights_cmd)
    
    highlights = json.loads(highlights_json.read_text())
    print(f"Found {len(highlights)} highlights in stream mode", file=sys.stderr)
    
    # Face tracking (try YuNet first, fall back to Haar)
    print("\nPerforming face tracking...", file=sys.stderr)
    tracking_json = output_dir / "tracking.json"
    facetrack_cmd = [
        "python3", str(HERE / "facetrack.py"), "detect",
        str(video_path),
        "--out", str(tracking_json),
        "--detector", "yunet",  # Will fall back to haar if unavailable
        "--aspect", "9:16"
    ]
    run_cmd(facetrack_cmd)
    
    tracking_data = json.loads(tracking_json.read_text())
    print(f"Tracking complete (detector: {tracking_data.get('detector_used', 'unknown')})", 
          file=sys.stderr)
    
    # Generate transcript for captions (use faster-whisper if available, else skip)
    words_json = output_dir / "transcript.json"
    if not words_json.exists():
        try:
            print("\nGenerating transcript for captions...", file=sys.stderr)
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(video_path))
            
            words = []
            for segment in segments:
                for word in segment.words:
                    words.append({"text": word.word.strip(), "start": word.start, "end": word.end})
            
            words_json.write_text(json.dumps(words, indent=2))
            print(f"Transcript generated: {len(words)} words", file=sys.stderr)
        except ImportError:
            print("faster-whisper not available, skipping captions", file=sys.stderr)
            words = []
        except Exception as e:
            print(f"Transcription failed: {e}, skipping captions", file=sys.stderr)
            words = []
    else:
        words = json.loads(words_json.read_text())
    
    # Process each clip with stream-pop captions
    print(f"\nProcessing {len(highlights)} clips with captions...", file=sys.stderr)
    results = []
    
    for i, highlight in enumerate(highlights, 1):
        clip_dir = output_dir / f"clip_{i:03d}"
        clip_dir.mkdir(parents=True, exist_ok=True)
        
        start = highlight["start"]
        end = highlight["end"]
        
        # Extract clip
        raw_clip = clip_dir / "raw.mp4"
        extract_clip(video_path, start, end, raw_clip)
        
        # Apply crop
        cropped_clip = clip_dir / "video.mp4"
        apply_clip_crop(raw_clip, tracking_data, start, end, cropped_clip)
        
        # Generate and burn captions
        if words:
            clip_words = [w for w in words if start <= w["start"] < end]
            shifted_words = shift_captions(clip_words, start)
            
            if shifted_words:
                clip_words_json = clip_dir / "words.json"
                clip_words_json.write_text(json.dumps(shifted_words, indent=2))
                
                # Build captions with profanity masking
                if profanity_mask:
                    from profanity_mask import mask_profanity_in_words
                    shifted_words = mask_profanity_in_words(shifted_words, enabled=True)
                    clip_words_json.write_text(json.dumps(shifted_words, indent=2))
                
                captions_cmd = [
                    "python3", str(HERE / "captions.py"), "build",
                    "--words", str(clip_words_json),
                    "-o", str(clip_dir / "captions"),
                    "--profile", "social",
                    "--aspect", "9:16"
                ]
                run_cmd(captions_cmd)
                
                # Burn captions
                if (clip_dir / "captions.ass").exists():
                    burned_clip = clip_dir / "burned.mp4"
                    burn_cmd = [
                        "python3", str(HERE / "captions.py"), "burn",
                        str(cropped_clip),
                        str(clip_dir / "captions.ass"),
                        "-o", str(burned_clip)
                    ]
                    run_cmd(burn_cmd)
                    # Replace video.mp4 with burned version
                    burned_clip.replace(cropped_clip)
        
        results.append({
            "clip_dir": str(clip_dir),
            "highlight": highlight,
            "video": str(cropped_clip),
            "method": highlight.get("method", "stream")
        })
    
    summary = {
        "source_video": str(video_path),
        "mode": "stream-highlights",
        "chunk_duration": chunk_duration,
        "highlights_count": len(highlights),
        "clips_processed": len(results),
        "clips_failed": 0,
        "chat_messages": len(chat_messages) if chat_messages else 0,
        "clips": results
    }
    
    summary_json = output_dir / "summary.json"
    summary_json.write_text(json.dumps(summary, indent=2))
    
    print(f"\n{'='*60}", file=sys.stderr)
    print("Stream-highlights processing complete!", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Highlights: {summary['highlights_count']}", file=sys.stderr)
    print(f"Clips: {summary['clips_processed']}", file=sys.stderr)
    print(f"Output: {output_dir}", file=sys.stderr)
    
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["process"], help="Action to perform")
    parser.add_argument("video", help="Input video file or URL")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--mode", choices=["default", "stream-highlights"], default="default",
                       help="Processing mode: default or stream-highlights")
    parser.add_argument("--transcript", help="Pre-existing transcript JSON (words.json format)")
    parser.add_argument("--chat", help="Chat messages JSON for stream mode")
    parser.add_argument("--rights-confirmed", action="store_true",
                       help="Confirm you have rights to use this content (required for URLs)")
    parser.add_argument("--chunk-duration", type=int, default=90,
                       help="Chunk duration for stream mode (seconds, default: 90)")
    parser.add_argument("--profanity-mask", action="store_true", default=True,
                       help="Mask profanity in captions (default: enabled)")
    parser.add_argument("--min-clip", type=float, default=10, 
                       help="Minimum clip duration in seconds")
    parser.add_argument("--max-clip", type=float, default=60,
                       help="Maximum clip duration in seconds (30 recommended for stream mode)")
    parser.add_argument("--top-n", type=int, default=5,
                       help="Number of top highlights to extract")
    
    args = parser.parse_args()
    
    if args.action == "process":
        if args.mode == "stream-highlights":
            # Stream-highlights mode
            if args.video.startswith(("http://", "https://")) and not args.rights_confirmed:
                print("ERROR: --rights-confirmed required for URL input", file=sys.stderr)
                print("Confirm you have rights to record, edit, and use this content.", file=sys.stderr)
                sys.exit(1)
            
            summary = process_stream_highlights(
                args.video,
                args.out,
                chat_json=args.chat,
                min_clip=args.min_clip,
                max_clip=args.max_clip,
                top_n=args.top_n,
                chunk_duration=args.chunk_duration,
                rights_confirmed=args.rights_confirmed,
                profanity_mask=args.profanity_mask
            )
        else:
            # Default mode (existing)
            summary = process_video(
                args.video,
                args.out,
                transcript_path=args.transcript,
                min_clip=args.min_clip,
                max_clip=args.max_clip,
                top_n=args.top_n
            )
        
        # Exit with error if any clips failed
        if summary.get("clips_failed", 0) > 0:
            sys.exit(1)

if __name__ == "__main__":
    main()
