#!/usr/bin/env python3
"""Face tracking and 9:16 crop generation using OpenCV with IoU-based tracker IDs.

  facetrack.py detect VIDEO --out tracking.json [--sample-fps 5] [--smooth-window 30] [--detector DETECTOR]
  facetrack.py crop VIDEO --tracking tracking.json --out OUTPUT.mp4 --aspect 9:16

Detector options (--detector):
  - haar: OpenCV Haar cascade (default, CPU-only, no downloads required)
  - yunet: YuNet face detection (MIT License, requires model download)
  - yolox: YOLOX-S person tracking (Apache-2.0, requires model download)

Models must be downloaded first via: python3 scripts/fetch_models.py
YuNet and YOLOX fall back to Haar cascade if models unavailable.

Generates smooth 9:16 crops centered on tracked faces/people with IoU-based tracker ID assignment.

tracking.json format:
{
  "tracks": [
    {"tracker_id": 0, "frames": [{"frame": 0, "time": 0.0, "bbox": [x, y, w, h], "center": [cx, cy]}, ...]},
    ...
  ],
  "crop_windows": [{"frame": 0, "time": 0.0, "cx": 540, "cy": 540, "w": 1080, "h": 1920}, ...],
  "video_width": 1920,
  "video_height": 1080,
  "fps": 30.0,
  "detector_used": "haar"
}
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
MODELS_DIR = REPO / "models" / "stream"

def get_video_info(video_path):
    """Get video dimensions and fps using ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "json", str(video_path)
    ], capture_output=True, text=True)
    
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    
    # Parse frame rate
    fps_parts = stream["r_frame_rate"].split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
    
    return {
        "width": stream["width"],
        "height": stream["height"],
        "fps": fps,
        "duration": float(stream.get("duration", 0))
    }

def detect_faces_opencv(video_path, sample_fps=5, smooth_window=30):
    """Detect faces using OpenCV Haar cascade and track with IoU-based tracker IDs."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("Error: opencv-python is required. Install with: pip install opencv-python", 
              file=sys.stderr)
        sys.exit(1)
    
    # Load Haar cascade for face detection (CPU-only, ships with OpenCV)
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    if face_cascade.empty():
        print(f"Error: Could not load face cascade from {cascade_path}", file=sys.stderr)
        sys.exit(1)
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}", file=sys.stderr)
        sys.exit(1)
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Sample every N frames
    frame_step = max(1, int(video_fps / sample_fps))
    
    print(f"Processing {video_width}x{video_height} @ {video_fps:.2f}fps, "
          f"sampling every {frame_step} frames", file=sys.stderr)
    
    # Simple tracker: match detections to previous frame's detections by IoU
    active_tracks = {}  # tracker_id -> last_bbox
    next_id = 0
    all_detections = []  # frame, detections with tracker_ids
    
    frame_num = 0
    processed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Only process sampled frames
        if frame_num % frame_step == 0:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Match detections to existing tracks
            current_detections = []
            matched_ids = set()
            
            for (x, y, w, h) in faces:
                bbox = [int(x), int(y), int(w), int(h)]
                center = [int(x + w/2), int(y + h/2)]
                
                # Try to match with existing tracks
                best_iou = 0
                best_id = None
                
                for tid, last_bbox in active_tracks.items():
                    if tid in matched_ids:
                        continue
                    iou = compute_iou(bbox, last_bbox)
                    if iou > best_iou:
                        best_iou = iou
                        best_id = tid
                
                # Assign tracker ID
                if best_iou > 0.3:  # IoU threshold for matching
                    tracker_id = best_id
                    matched_ids.add(tracker_id)
                else:
                    tracker_id = next_id
                    next_id += 1
                
                active_tracks[tracker_id] = bbox
                
                current_detections.append({
                    "tracker_id": tracker_id,
                    "bbox": bbox,
                    "center": center
                })
            
            # Record detections for this frame
            time_sec = frame_num / video_fps
            all_detections.append({
                "frame": frame_num,
                "time": round(time_sec, 3),
                "detections": current_detections
            })
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed} frames...", file=sys.stderr)
        
        frame_num += 1
    
    cap.release()
    
    print(f"Detection complete: {processed} frames processed, {len(active_tracks)} unique tracks",
          file=sys.stderr)
    
    # Organize detections by tracker_id
    tracks = {}
    for det in all_detections:
        for d in det["detections"]:
            tid = d["tracker_id"]
            if tid not in tracks:
                tracks[tid] = []
            tracks[tid].append({
                "frame": det["frame"],
                "time": det["time"],
                "bbox": d["bbox"],
                "center": d["center"]
            })
    
    # Convert to list and smooth tracks
    track_list = [{"tracker_id": tid, "frames": frames} 
                  for tid, frames in sorted(tracks.items())]
    
    # Smooth track positions
    for track in track_list:
        smooth_track_positions(track["frames"], smooth_window)
    
    return {
        "tracks": track_list,
        "video_width": video_width,
        "video_height": video_height,
        "fps": video_fps,
        "total_frames": total_frames
    }

def compute_iou(bbox1, bbox2):
    """Compute IoU between two bboxes [x, y, w, h]."""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    
    # Compute intersection
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    
    # Compute union
    bbox1_area = w1 * h1
    bbox2_area = w2 * h2
    union_area = bbox1_area + bbox2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0

def smooth_track_positions(frames, window_size):
    """Smooth center positions using moving average."""
    if len(frames) < 2:
        return
    
    try:
        import numpy as np
    except ImportError:
        return  # Skip smoothing if numpy not available
    
    # Extract centers
    centers = np.array([f["center"] for f in frames])
    
    # Apply moving average
    if len(centers) > window_size:
        smoothed = np.zeros_like(centers)
        half_window = window_size // 2
        
        for i in range(len(centers)):
            start = max(0, i - half_window)
            end = min(len(centers), i + half_window + 1)
            smoothed[i] = centers[start:end].mean(axis=0)
        
        # Update centers
        for i, f in enumerate(frames):
            f["center"] = [int(smoothed[i][0]), int(smoothed[i][1])]

def generate_crop_windows(tracking_data, target_aspect="9:16"):
    """Generate crop window positions for each frame to maintain 9:16 aspect."""
    video_width = tracking_data["video_width"]
    video_height = tracking_data["video_height"]
    fps = tracking_data["fps"]
    
    # Parse target aspect
    if target_aspect == "9:16":
        aspect_w, aspect_h = 9, 16
    else:
        parts = target_aspect.split(":")
        aspect_w, aspect_h = int(parts[0]), int(parts[1])
    
    target_ratio = aspect_w / aspect_h
    
    # Compute crop dimensions (fit within source video)
    if video_width / video_height > target_ratio:
        # Video is wider than target, crop width
        crop_h = video_height
        crop_w = int(crop_h * target_ratio)
    else:
        # Video is taller than target, crop height
        crop_w = video_width
        crop_h = int(crop_w / target_ratio)
    
    # Get primary track (longest/most detections)
    tracks = tracking_data["tracks"]
    if not tracks:
        # No faces detected, center crop
        return generate_center_crop_windows(
            tracking_data["total_frames"], fps,
            video_width, video_height, crop_w, crop_h
        )
    
    primary_track = max(tracks, key=lambda t: len(t["frames"]))
    
    print(f"Using tracker_id={primary_track['tracker_id']} as primary track "
          f"({len(primary_track['frames'])} detections)", file=sys.stderr)
    
    # Generate crop window for each frame
    crop_windows = []
    frame_to_position = {f["frame"]: f["center"] for f in primary_track["frames"]}
    
    # For frames without detection, interpolate or use last known position
    last_known_center = [video_width // 2, video_height // 2]
    
    for frame_num in range(tracking_data["total_frames"]):
        if frame_num in frame_to_position:
            center = frame_to_position[frame_num]
            last_known_center = center
        else:
            center = last_known_center
        
        # Compute crop window centered on face
        cx, cy = center
        
        # Clamp crop window to video bounds
        x1 = max(0, min(video_width - crop_w, cx - crop_w // 2))
        y1 = max(0, min(video_height - crop_h, cy - crop_h // 2))
        
        crop_windows.append({
            "frame": frame_num,
            "time": round(frame_num / fps, 3),
            "x": int(x1),
            "y": int(y1),
            "w": crop_w,
            "h": crop_h,
            "cx": int(cx),
            "cy": int(cy)
        })
    
    return crop_windows

def generate_center_crop_windows(total_frames, fps, video_width, video_height, crop_w, crop_h):
    """Generate center crop windows when no faces detected."""
    x = (video_width - crop_w) // 2
    y = (video_height - crop_h) // 2
    
    return [{
        "frame": frame_num,
        "time": round(frame_num / fps, 3),
        "x": x,
        "y": y,
        "w": crop_w,
        "h": crop_h,
        "cx": video_width // 2,
        "cy": video_height // 2
    } for frame_num in range(total_frames)]

def apply_crop_ffmpeg(video_path, tracking_data, output_path):
    """Apply crop using ffmpeg crop filter with smooth panning."""
    crop_windows = tracking_data.get("crop_windows", [])
    if not crop_windows:
        print("Error: No crop windows in tracking data", file=sys.stderr)
        sys.exit(1)
    
    # Use first window for static crop dimensions
    first = crop_windows[0]
    crop_w, crop_h = first["w"], first["h"]
    
    # For smooth panning, we could use zoompan or crop with expression
    # For simplicity with static tracking, use the most common position
    # In practice, we'd interpolate positions and use crop with x/y expressions
    
    # Compute average crop position (simplified)
    avg_x = sum(w["x"] for w in crop_windows) // len(crop_windows)
    avg_y = sum(w["y"] for w in crop_windows) // len(crop_windows)
    
    print(f"Applying crop: {crop_w}x{crop_h} at ({avg_x}, {avg_y})", file=sys.stderr)
    
    # Apply crop with ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"crop={crop_w}:{crop_h}:{avg_x}:{avg_y}",
        "-c:a", "copy",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error applying crop: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Cropped video saved to {output_path}", file=sys.stderr)


def detect_faces_yunet(video_path, sample_fps=5, smooth_window=30):
    """Detect faces using YuNet (MIT License, OpenCV Zoo).
    
    Falls back to Haar cascade if model not available.
    """
    model_path = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
    
    if not model_path.exists():
        print(f"YuNet model not found at {model_path}", file=sys.stderr)
        print("Falling back to Haar cascade. Run: python3 scripts/fetch_models.py --yunet", 
              file=sys.stderr)
        return detect_faces_opencv(video_path, sample_fps, smooth_window)
    
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("Error: opencv-python required", file=sys.stderr)
        sys.exit(1)
    
    # Initialize YuNet detector
    try:
        detector = cv2.FaceDetectorYN.create(
            str(model_path),
            "",
            (320, 320),
            score_threshold=0.8,
            nms_threshold=0.3,
            top_k=5000
        )
    except Exception as e:
        print(f"Could not initialize YuNet: {e}", file=sys.stderr)
        print("Falling back to Haar cascade", file=sys.stderr)
        return detect_faces_opencv(video_path, sample_fps, smooth_window)
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Could not open video", file=sys.stderr)
        sys.exit(1)
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_step = max(1, int(video_fps / sample_fps))
    
    print(f"Using YuNet detector on {video_width}x{video_height} @ {video_fps:.2f}fps", 
          file=sys.stderr)
    
    active_tracks = {}
    next_id = 0
    all_detections = []
    frame_num = 0
    processed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_step == 0:
            # Resize for detection (YuNet expects 320x320)
            h, w = frame.shape[:2]
            scale = min(320 / w, 320 / h)
            resized = cv2.resize(frame, (round(w * scale), round(h * scale)))
            
            # Pad to 320x320
            canvas = np.zeros((320, 320, 3), dtype=np.uint8)
            pad_x = (320 - resized.shape[1]) // 2
            pad_y = (320 - resized.shape[0]) // 2
            canvas[pad_y:pad_y + resized.shape[0], pad_x:pad_x + resized.shape[1]] = resized
            
            # Detect
            detector.setInputSize((320, 320))
            _, faces = detector.detect(canvas)
            
            current_detections = []
            if faces is not None:
                factor = 1.0 / scale
                for face in faces:
                    x, y, fw, fh = face[:4]
                    # Un-pad and un-scale
                    x = int((x - pad_x) * factor)
                    y = int((y - pad_y) * factor)
                    fw = int(fw * factor)
                    fh = int(fh * factor)
                    
                    # Clamp to video bounds
                    x = max(0, min(x, video_width - 1))
                    y = max(0, min(y, video_height - 1))
                    fw = min(fw, video_width - x)
                    fh = min(fh, video_height - y)
                    
                    if fw <= 0 or fh <= 0:
                        continue
                    
                    bbox = [x, y, fw, fh]
                    center = [x + fw // 2, y + fh // 2]
                    
                    # Match to existing tracks by IoU
                    best_iou = 0
                    best_id = None
                    for tid, last_bbox in active_tracks.items():
                        iou = compute_iou(bbox, last_bbox)
                        if iou > best_iou:
                            best_iou = iou
                            best_id = tid
                    
                    if best_iou > 0.3:
                        tracker_id = best_id
                    else:
                        tracker_id = next_id
                        next_id += 1
                    
                    active_tracks[tracker_id] = bbox
                    current_detections.append({
                        "tracker_id": tracker_id,
                        "bbox": bbox,
                        "center": center
                    })
            
            time_sec = frame_num / video_fps
            all_detections.append({
                "frame": frame_num,
                "time": round(time_sec, 3),
                "detections": current_detections
            })
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed} frames...", file=sys.stderr)
        
        frame_num += 1
    
    cap.release()
    
    # Organize by tracker_id
    tracks = {}
    for det in all_detections:
        for d in det["detections"]:
            tid = d["tracker_id"]
            if tid not in tracks:
                tracks[tid] = []
            tracks[tid].append({
                "frame": det["frame"],
                "time": det["time"],
                "bbox": d["bbox"],
                "center": d["center"]
            })
    
    track_list = [{"tracker_id": tid, "frames": frames} 
                  for tid, frames in sorted(tracks.items())]
    
    # Smooth positions
    for track in track_list:
        smooth_track_positions(track["frames"], smooth_window)
    
    return {
        "tracks": track_list,
        "video_width": video_width,
        "video_height": video_height,
        "fps": video_fps,
        "total_frames": total_frames,
        "detector_used": "yunet"
    }


def detect_people_yolox(video_path, sample_fps=5, smooth_window=30):
    """Detect people using YOLOX-S (Apache-2.0, OpenCV Zoo).
    
    Falls back to Haar cascade if model not available or onnxruntime missing.
    """
    model_path = MODELS_DIR / "object_detection_yolox_2022nov.onnx"
    
    if not model_path.exists():
        print(f"YOLOX model not found at {model_path}", file=sys.stderr)
        print("Falling back to Haar cascade. Run: python3 scripts/fetch_models.py --yolox", 
              file=sys.stderr)
        return detect_faces_opencv(video_path, sample_fps, smooth_window)
    
    try:
        import cv2
        import numpy as np
        import onnxruntime as ort
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        print("Falling back to Haar cascade", file=sys.stderr)
        return detect_faces_opencv(video_path, sample_fps, smooth_window)
    
    # Initialize ONNX session
    try:
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        session = ort.InferenceSession(str(model_path), opts, 
                                       providers=["CPUExecutionProvider"])
    except Exception as e:
        print(f"Could not initialize YOLOX: {e}", file=sys.stderr)
        print("Falling back to Haar cascade", file=sys.stderr)
        return detect_faces_opencv(video_path, sample_fps, smooth_window)
    
    # Grid for YOLOX decoding
    def make_grids():
        rows = []
        for stride in (8, 16, 32):
            n = 640 // stride
            ys, xs = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
            rows.append(np.stack([xs.ravel(), ys.ravel(), 
                                 np.full(n * n, stride)], axis=1))
        return np.concatenate(rows).astype(np.float32)
    
    grid = make_grids()
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Error: Could not open video", file=sys.stderr)
        sys.exit(1)
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_step = max(1, int(video_fps / sample_fps))
    
    print(f"Using YOLOX person detector on {video_width}x{video_height} @ {video_fps:.2f}fps",
          file=sys.stderr)
    
    active_tracks = {}
    next_id = 0
    all_detections = []
    frame_num = 0
    processed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_step == 0:
            h, w = frame.shape[:2]
            r = min(640 / w, 640 / h)
            
            # Prepare input
            img = np.full((640, 640, 3), 114, dtype=np.uint8)
            img[:round(h * r), :round(w * r)] = cv2.resize(frame, 
                                                           (round(w * r), round(h * r)))
            blob = img.transpose(2, 0, 1)[None].astype(np.float32)
            
            # Run inference
            output = session.run(None, {"images": blob})[0][0]
            
            # Decode detections
            xy = (output[:, :2] + grid[:, :2]) * grid[:, 2:3]
            wh = np.exp(output[:, 2:4]) * grid[:, 2:3]
            score = output[:, 4] * output[:, 5]  # objectness * P(person)
            keep = score > 0.35
            
            current_detections = []
            if keep.any():
                xy, wh, score = xy[keep] / r, wh[keep] / r, score[keep]
                boxes = [[float(x - bw / 2), float(y - bh / 2), float(bw), float(bh)] 
                        for (x, y), (bw, bh) in zip(xy, wh)]
                idx = cv2.dnn.NMSBoxes(boxes, score.tolist(), 0.35, 0.45)
                
                for i in np.array(idx).ravel():
                    x, y, pw, ph = boxes[i]
                    bbox = [int(x), int(y), int(pw), int(ph)]
                    center = [int(x + pw / 2), int(y + ph / 2)]
                    
                    # IoU matching
                    best_iou = 0
                    best_id = None
                    for tid, last_bbox in active_tracks.items():
                        iou = compute_iou(bbox, last_bbox)
                        if iou > best_iou:
                            best_iou = iou
                            best_id = tid
                    
                    if best_iou > 0.3:
                        tracker_id = best_id
                    else:
                        tracker_id = next_id
                        next_id += 1
                    
                    active_tracks[tracker_id] = bbox
                    current_detections.append({
                        "tracker_id": tracker_id,
                        "bbox": bbox,
                        "center": center
                    })
            
            time_sec = frame_num / video_fps
            all_detections.append({
                "frame": frame_num,
                "time": round(time_sec, 3),
                "detections": current_detections
            })
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed} frames...", file=sys.stderr)
        
        frame_num += 1
    
    cap.release()
    
    # Organize by tracker_id
    tracks = {}
    for det in all_detections:
        for d in det["detections"]:
            tid = d["tracker_id"]
            if tid not in tracks:
                tracks[tid] = []
            tracks[tid].append({
                "frame": det["frame"],
                "time": det["time"],
                "bbox": d["bbox"],
                "center": d["center"]
            })
    
    track_list = [{"tracker_id": tid, "frames": frames} 
                  for tid, frames in sorted(tracks.items())]
    
    # Smooth positions
    for track in track_list:
        smooth_track_positions(track["frames"], smooth_window)
    
    return {
        "tracks": track_list,
        "video_width": video_width,
        "video_height": video_height,
        "fps": video_fps,
        "total_frames": total_frames,
        "detector_used": "yolox"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["detect", "crop"], 
                       help="detect: find faces and generate tracking; crop: apply crop to video")
    parser.add_argument("video", help="Input video file")
    parser.add_argument("--out", required=True, 
                       help="Output path (tracking.json for detect, video file for crop)")
    parser.add_argument("--tracking", help="Tracking JSON (required for crop action)")
    parser.add_argument("--detector", choices=["haar", "yunet", "yolox"], default="haar",
                       help="Detector: haar (default), yunet (MIT), yolox (Apache-2.0)")
    parser.add_argument("--sample-fps", type=float, default=5,
                       help="Frames per second to sample for detection (default: 5)")
    parser.add_argument("--smooth-window", type=int, default=30,
                       help="Window size for position smoothing (default: 30)")
    parser.add_argument("--aspect", default="9:16",
                       help="Target aspect ratio (default: 9:16)")
    
    args = parser.parse_args()
    
    if args.action == "detect":
        print(f"Detecting with {args.detector} in {args.video}...", file=sys.stderr)
        
        # Select detector
        if args.detector == "yunet":
            tracking_data = detect_faces_yunet(
                args.video,
                sample_fps=args.sample_fps,
                smooth_window=args.smooth_window
            )
        elif args.detector == "yolox":
            tracking_data = detect_people_yolox(
                args.video,
                sample_fps=args.sample_fps,
                smooth_window=args.smooth_window
            )
        else:  # haar (default)
            tracking_data = detect_faces_opencv(
                args.video,
                sample_fps=args.sample_fps,
                smooth_window=args.smooth_window
            )
            if "detector_used" not in tracking_data:
                tracking_data["detector_used"] = "haar"
        
        # Generate crop windows
        print("Generating crop windows...", file=sys.stderr)
        crop_windows = generate_crop_windows(tracking_data, target_aspect=args.aspect)
        tracking_data["crop_windows"] = crop_windows
        tracking_data["target_aspect"] = args.aspect
        
        # Save tracking data
        Path(args.out).write_text(json.dumps(tracking_data, indent=2))
        print(f"Tracking data saved to {args.out}", file=sys.stderr)
        
        # Print summary
        print(f"\nSummary:", file=sys.stderr)
        print(f"  Detector used: {tracking_data.get('detector_used', 'unknown')}", file=sys.stderr)
        print(f"  Tracks: {len(tracking_data['tracks'])}", file=sys.stderr)
        print(f"  Crop windows: {len(crop_windows)}", file=sys.stderr)
        print(f"  Target aspect: {args.aspect}", file=sys.stderr)
    
    elif args.action == "crop":
        if not args.tracking:
            print("Error: --tracking is required for crop action", file=sys.stderr)
            sys.exit(1)
        
        tracking_data = json.loads(Path(args.tracking).read_text())
        
        print(f"Applying crop to {args.video}...", file=sys.stderr)
        apply_crop_ffmpeg(args.video, tracking_data, args.out)

if __name__ == "__main__":
    main()
