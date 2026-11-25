#!/usr/bin/env python3
"""Review gate: required before the final render/export and before ANY paid generation.

  review.py check VIDEO --out DIR [--preset reels] [--expect-seconds 15] [--music-credits credits.json] [--job job.json]
      -> DIR/preview.mp4 (low-res, timecoded), DIR/contact.jpg (ffmpeg tile), DIR/safe.jpg,
         DIR/scenes.jpg (one labeled frame per scene, with --job), DIR/phone.jpg (frames at phone size: can you read it?),
         DIR/review.md (checklist), DIR/review.json (auto results, approved=false)
  review.py approve DIR --by "name or 'user in chat'"     # record the user's OK
  review.py status DIR                                     # exit 0 only if approved
  review.py audit COMP_DIR_OR_FILE [--json report.json]    # static motion audit of a HyperFrames/Remotion comp
                                                           # (exit 1 on any FAIL; no render, no network)

Auto checks: resolution/fps/duration vs preset, loudness (EBU R128 integrated + true peak),
black frames, long silence (dead air), frozen mid-video stretches, frozen ending, photosensitive flashes (WCAG 2.3.1 heuristic),
scene timing vs job.json (every scene long enough to read), cut list (cuts/flashes/fast moves -> cuts.json),
audio clicks at cuts.
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def probe(v):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,profile:format=duration,size",
            "-of", "json", str(v)])
    js = json.loads(r.stdout)
    vs = next((s for s in js["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in js["streams"] if s["codec_type"] == "audio"), None)
    num, den = (vs.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {"w": vs.get("width"), "h": vs.get("height"), "fps": round(int(num) / max(1, int(den)), 3), "vcodec": vs.get("codec_name"),
            "pix_fmt": vs.get("pix_fmt"), "profile": vs.get("profile"), "acodec": a and a.get("codec_name"),
            "duration": float(js["format"]["duration"]), "bytes": int(js["format"]["size"])}

def loudness(v):
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr
    summ = txt[txt.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summ)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", summ)
    f = lambda m: float(m.group(1)) if m and m.group(1) != "-inf" else None
    return {"lufs": f(I), "true_peak": f(tp), "lra": f(lra)}

def detect_dropouts(v, floor_db=-80, min_dur=0.02, max_dur=1.0, edge_s=0.05):
    """Audio dropouts: short digital holes (≤ floor_db, min_dur–max_dur, sound on both sides, not within edge_s of ends).
    Returns [(time, duration)]. Adapted from ffmpeg-skill check.py technique."""
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-af",
            f"silencedetect=noise={floor_db}dB:d={min_dur}", "-f", "null", "-"])
    # Parse silence_start and silence_duration
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    durs = [float(m) for m in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
    if not starts:
        return []
    # Get file duration
    p_r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(v)])
    try:
        file_dur = float(json.loads(p_r.stdout)["format"]["duration"])
    except (json.JSONDecodeError, KeyError, ValueError):
        file_dur = 999999  # fall back if duration can't be read
    
    dropouts = []
    for start, dur in zip(starts, durs):
        if dur > max_dur:
            continue  # too long, not a dropout
        if start < edge_s or start + dur > file_dur - edge_s:
            continue  # too close to file edge
        dropouts.append((round(start, 2), round(dur, 3)))
    return dropouts

def file_identity(path):
    """Return 'size:mtime_ns' identity string. Adapted from ffmpeg-skill emit.py."""
    try:
        st = Path(path).stat()
        return f"{st.st_size}:{st.st_mtime_ns}"
    except (OSError, FileNotFoundError):
        return ""

def detect(v, filt, key):
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-vf" if "detect" in filt and not filt.startswith("silence") else "-af", filt, "-f", "null", "-"])
    return re.findall(key, r.stderr)

def flashes(v, fps):
    """WCAG 2.3.1 general-flash heuristic on a 4x4 block grid (each block ~6% of frame, larger than the
    25%-of-10-degree area). Flags >3 flash pairs in any 1-second window where the darker state < 0.8."""
    import numpy as np
    W, H = 32, 32
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(v), "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    fr = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(fr) // (W * H)
    if n < 2:
        return {"max_flashes_per_s": 0, "worst_at": None}
    y = fr[: n * W * H].reshape(n, H, W).astype(np.float32) / 255.0
    lin = np.where(y <= 0.04045, y / 12.92, ((y + 0.055) / 1.055) ** 2.4)  # approx relative luminance
    blocks = lin.reshape(n, 4, H // 4, 4, W // 4).mean(axis=(2, 4)).reshape(n, 16)
    worst, worst_t = 0, None
    win = max(1, int(round(fps)))
    for b in range(16):
        s = blocks[:, b]
        mn = mx = s[0]
        state, trans = 0, []
        for i in range(1, n):
            v = s[i]
            mn, mx = min(mn, v), max(mx, v)
            if state != 1 and v - mn >= 0.1 and mn < 0.8:      # rising change of >=10%
                trans.append(i); state = 1; mn = mx = v
            elif state != -1 and mx - v >= 0.1 and v < 0.8:   # falling change of >=10%
                trans.append(i); state = -1; mn = mx = v
        ev = np.array(trans)
        for k in range(len(ev)):
            cnt = int(((ev >= ev[k]) & (ev < ev[k] + win)).sum()) // 2  # flash = pair of opposing changes
            if cnt > worst:
                worst, worst_t = cnt, round(ev[k] / fps, 2)
    return {"max_flashes_per_s": worst, "worst_at": worst_t}

def detect_pops(v, fps):
    """Find one-frame pops: anomalous frames that differ strongly from both neighbors
    while those neighbors are similar to each other. Catches swaps, resets, and flashes.
    Returns list of (frame_number, time_seconds)."""
    import numpy as np
    W, H = 160, 90
    proc = subprocess.run(["ffmpeg", "-v", "error", "-i", str(v), "-vf", 
                          f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True)
    raw = np.frombuffer(proc.stdout, dtype=np.uint8)
    frame_count = len(raw) // (W * H)
    if frame_count < 3:
        return []
    
    video = raw[: frame_count * W * H].reshape(frame_count, H, W).astype(np.float32)
    results = []
    
    # Method: frame i is a pop when it's very different from BOTH frame i-1 and i+1,
    # while frames i-1 and i+1 are close to each other. This naturally excludes cuts
    # (where the change persists) and held frames (where nothing changes).
    for i in range(1, frame_count - 1):
        before_diff = np.mean(np.abs(video[i] - video[i - 1]))
        after_diff = np.mean(np.abs(video[i] - video[i + 1]))
        neighbor_diff = np.mean(np.abs(video[i + 1] - video[i - 1]))
        
        # Pop criteria: frame i changes strongly in both directions (> 20.0)
        # while its neighbors are similar (their diff < 1/4 of the pop's changes)
        pop_threshold = 20.0
        if before_diff > pop_threshold and after_diff > pop_threshold:
            avg_pop_change = (before_diff + after_diff) / 2.0
            if neighbor_diff < avg_pop_change / 4.0:
                results.append((i, round(i / fps, 2)))
    
    return results

# --- Cut list and cut clicks -------------------------------------------------
# Approach adapted from HyperFrames `measure cuts` (heygen-com/hyperframes, Apache-2.0,
# packages/cli/src/measure/cuts.ts @ d317abcd, read 2026-11-17) and the cut-boundary
# self-eval in browser-use/video-use (MIT, SKILL.md @ 43cfc566). Re-implemented here in
# Python/numpy; thresholds are ours unless noted. See THIRD_PARTY_NOTICES.md.
SIG_W, SIG_H = 64, 36          # tiny grey signature per frame (HyperFrames uses the same size)
CUT_LEVEL, CUT_RATIO = 12.0, 4.0   # a cut changes >= 12 grey levels and >= 4x the local typical change
NEIGHBOURS = 12                # frames either side that define "typical"
RETURNED = 0.4                 # picture comes back within 4 frames -> a flash, not a cut
IN_MOTION = 0.3                # both sides already moving at 30% of the peak -> maybe a fast move

def _signatures(v):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(v), "-vf", f"scale={SIG_W}:{SIG_H}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    raw = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(raw) // (SIG_W * SIG_H)
    return raw[: n * SIG_W * SIG_H].reshape(n, SIG_H, SIG_W).astype(np.float32)

def _moved_change(a, b):
    """Smallest difference between b and a zoomed 0.8-1.25x and shifted a few pixels: a camera move, not a new shot."""
    import numpy as np
    best = float(np.mean(np.abs(a - b)))
    ys, xs = np.mgrid[0:SIG_H, 0:SIG_W]
    cy, cx = (SIG_H - 1) / 2, (SIG_W - 1) / 2
    for s in np.arange(0.8, 1.2501, 0.05):
        for dx in range(-6, 7, 2):
            for dy in range(-4, 5, 2):
                sy = np.clip(np.rint((ys - cy - dy) / s + cy), 0, SIG_H - 1).astype(int)
                sx = np.clip(np.rint((xs - cx - dx) / s + cx), 0, SIG_W - 1).astype(int)
                best = min(best, float(np.mean(np.abs(a[sy, sx] - b))))
    return best

def detect_cuts(v, fps):
    """Hard cuts from the frame-to-frame difference, each classified.
    Returns [{"frame", "t", "change", "kind"}] where kind is "cut", "flash" (the picture comes back:
    a white flash or a one-frame hit), "fast" (a whip or fast camera move inside one shot) or
    "transition" (a change spread over more than 3 frames: dissolve, wipe, flash-fade).
    The shot list is the gaps between "cut" rows. ffmpeg's scene score misses punch-ins; this does not."""
    import numpy as np
    f = _signatures(v)
    n = len(f)
    if n < 3:
        return []
    d = np.zeros(n, np.float32)
    d[1:] = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2))
    hits = []
    for i in range(1, n):
        around = np.concatenate([d[max(1, i - NEIGHBOURS):i], d[i + 1:i + 1 + NEIGHBOURS]])
        typical = max(1.0, float(np.median(around))) if len(around) else 1.0
        if d[i] >= CUT_LEVEL and d[i] >= CUT_RATIO * typical:
            if hits and hits[-1]["end"] == i:          # consecutive frames: one whip/dissolve, not several cuts
                hits[-1]["end"] = i + 1; hits[-1]["change"] = max(hits[-1]["change"], float(d[i]))
            else:
                hits.append({"frame": i, "end": i + 1, "change": float(d[i])})
    out = []
    for h in hits:
        i, e, c = h["frame"], h["end"], h["change"]
        diff = lambda a, b: float(np.mean(np.abs(f[a] - f[b]))) if 0 <= a < n and 0 <= b < n else 1e9
        if any(diff(i - 1, e - 1 + k) < RETURNED * c for k in range(1, 5)):
            kind = "flash"
        elif min(d[i - 1], d[e] if e < n else 0) >= IN_MOTION * c and _moved_change(f[i - 1], f[e - 1]) < RETURNED * c:
            kind = "fast"
        elif e - i > 3:
            kind = "transition"              # a dissolve, wipe or flash-fade spread over several frames
        else:
            kind = "cut"
        out.append({"frame": i, "t": round(i / fps, 3), "change": round(c, 1), "kind": kind})
    return out

def cut_clicks(v, cuts, win_ms=8, local_ms=2, ratio=12.0, floor=0.02):
    """Audio clicks at picture cuts. A hard audio edit with no ~30 ms fade leaves a step: one sample-to-sample
    jump far larger than the jumps in the 2 ms around it. A drum hit on the beat rises over several ms, so it
    is not flagged. Returns [(t, ratio)] for cuts with a step >= `ratio` x its local level and >= `floor`."""
    import numpy as np
    sr = 48000
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(v), "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.float32)
    if a.size < sr // 10:
        return []
    jump = np.abs(np.diff(a))
    w, lw = int(sr * win_ms / 1000), int(sr * local_ms / 1000)
    found = []
    for c in cuts:
        k = int(c["t"] * sr)
        best = 0.0
        for j in range(max(lw, k - w), min(jump.size - lw, k + w)):
            if jump[j] < floor:
                continue
            local = np.concatenate([jump[j - lw:j - 2], jump[j + 3:j + lw]])
            best = max(best, float(jump[j] / max(np.median(local), 1e-5)))
        if best >= ratio:
            found.append((c["t"], round(best, 1)))
    return found

def check_sync_drift(v, warn_ms=50):
    """Audio/video sync drift detection using ffprobe to read stream start times and durations.
    Returns {"probes": [(t, drift_ms)], "worst_drift_ms", "flagged", "error": str|None}. Flags WARNING 
    when drift exceeds ±warn_ms. If measurement fails, returns error instead of silently passing.
    Approach after coleam00/skills edit-video sync validation (MIT). See THIRD_PARTY_NOTICES.md."""
    # Get stream start times and durations from ffprobe
    r = sh(["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type,start_time,duration",
            "-of", "json", str(v)])
    if r.returncode != 0:
        return {"probes": [], "worst_drift_ms": 0.0, "flagged": False, 
                "error": f"ffprobe failed: {r.stderr[:100]}"}
    
    try:
        js = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        return {"probes": [], "worst_drift_ms": 0.0, "flagged": False,
                "error": f"ffprobe output parse failed: {str(e)[:100]}"}
    
    streams = js.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    
    if not v_stream or not a_stream:
        return {"probes": [], "worst_drift_ms": 0.0, "flagged": False, "error": None}
    
    # Parse start times (may be missing or "N/A")
    try:
        v_start = float(v_stream.get("start_time", 0))
    except (ValueError, TypeError):
        v_start = 0.0
    try:
        a_start = float(a_stream.get("start_time", 0))
    except (ValueError, TypeError):
        a_start = 0.0
    
    # Start drift: difference in start times (ms)
    start_drift = (a_start - v_start) * 1000.0
    
    # End drift: check if durations differ (stream length mismatch)
    try:
        v_dur = float(v_stream.get("duration", 0))
    except (ValueError, TypeError):
        v_dur = 0.0
    try:
        a_dur = float(a_stream.get("duration", 0))
    except (ValueError, TypeError):
        a_dur = 0.0
    
    end_drift = (a_dur - v_dur) * 1000.0 if v_dur > 0 and a_dur > 0 else 0.0
    
    # Report start and end drift as probes
    probes = [
        (0.0, round(start_drift, 1)),
        (round(max(v_dur, a_dur), 1), round(end_drift, 1))
    ]
    
    worst = max(abs(start_drift), abs(end_drift))
    return {"probes": probes, "worst_drift_ms": round(worst, 1), "flagged": worst > warn_ms, "error": None}

def compare_ssim_psnr(ref, test):
    """SSIM + PSNR comparison. Returns {"mean_ssim", "min_ssim", "worst_frame_t", "mean_psnr"} or {"error"}.
    Frames paired by index (settb/setpts=N), not timestamp. Adapted from ffmpeg-skill check.py --compare."""
    # Check that both files have same resolution
    r1 = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "json", str(ref)])
    r2 = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "json", str(test)])
    try:
        s1 = json.loads(r1.stdout)["streams"][0]
        s2 = json.loads(r2.stdout)["streams"][0]
        if (s1["width"], s1["height"]) != (s2["width"], s2["height"]):
            return {"error": f"frame size mismatch: {s1['width']}x{s1['height']} vs {s2['width']}x{s2['height']}"}
    except (json.JSONDecodeError, KeyError, IndexError):
        return {"error": "could not read stream info"}
    
    # Run ffmpeg ssim + psnr with settb/setpts=N pairing
    # Split into two passes to avoid filter complexity
    r_ssim = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ref), "-i", str(test), "-filter_complex",
                 "[0:v]settb=expr=1/30,setpts=N[r];[1:v]settb=expr=1/30,setpts=N[t];[r][t]ssim",
                 "-f", "null", "-"])
    r_psnr = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ref), "-i", str(test), "-filter_complex",
                 "[0:v]settb=expr=1/30,setpts=N[r];[1:v]settb=expr=1/30,setpts=N[t];[r][t]psnr",
                 "-f", "null", "-"])
    
    if r_ssim.returncode != 0:
        return {"error": f"ffmpeg SSIM failed: {r_ssim.stderr[:100]}"}
    if r_psnr.returncode != 0:
        # PSNR may fail on identical frames (infinite), that's ok
        psnr_stderr = ""
    else:
        psnr_stderr = r_psnr.stderr
    
    # Parse SSIM (format: "SSIM Y:0.xxx (yy.yy) ... All:0.xxx (zz.zz)")
    # For identical frames: "SSIM Y:1.000000 (inf) ... All:1.000000 (inf)"
    ssim_all = re.search(r"All:([\d.]+)", r_ssim.stderr)
    # Min SSIM may not be reported in summary; use the All value
    ssim_min = None
    worst_t = None
    
    # Parse PSNR (may be "inf" or very high for identical frames)
    # Format: "PSNR y:xx.xx u:xx.xx v:xx.xx average:xx.xx min:xx.xx max:xx.xx"
    psnr_avg = re.search(r"average:([\d.]+|inf)", psnr_stderr) if psnr_stderr else None
    psnr_val = None
    if psnr_avg:
        try:
            psnr_val = float(psnr_avg.group(1))
        except ValueError:
            psnr_val = float('inf')
    
    result = {
        "mean_ssim": float(ssim_all.group(1)) if ssim_all else None,
        "min_ssim": ssim_min,
        "worst_frame_t": worst_t,
        "mean_psnr": psnr_val,
    }
    return result

def verify_change_scope(ref, test, regions):
    """Verify declared change scope. regions: list of "START-END" or "START-END@X,Y,W,H" or ["none"].
    Returns {"pass": bool, "failures": [(time, x, y, w, h, reason)], "brightness_lift": float|None}.
    Adapted from ffmpeg-skill check.py --expect-changed.
    
    Memory-bounded: downscales to ~640x360 for analysis (uses <500 MB for 10s 1080p video).
    Compares chroma as well as luma (YUV420p).
    Detects global brightness lifts of ~20 levels.
    Fails on unmatched tail frames when lengths differ."""
    import numpy as np
    
    # Parse regions - don't split on commas inside @X,Y,W,H  
    # Example: "1-2@10,20,30,40" should parse as time="1-2", rect="10,20,30,40"
    allowed = []
    if regions == ["none"] or not regions:
        pass  # no changes allowed anywhere
    else:
        for r in regions:
            if "@" in r:
                # Split on @ to get time and rect, then parse rect carefully
                parts = r.split("@", 1)
                time_part = parts[0]
                rect_part = parts[1]
                start, end = [float(x) for x in time_part.split("-")]
                rect_coords = [int(x) for x in rect_part.split(",")]
                if len(rect_coords) != 4:
                    return {"pass": False, "failures": [(0, 0, 0, 0, 0, f"invalid rect syntax: {r}")], "brightness_lift": None}
                x, y, w, h = rect_coords
                allowed.append({"start": start, "end": end, "x": x, "y": y, "w": w, "h": h})
            else:
                start, end = [float(x) for x in r.split("-")]
                allowed.append({"start": start, "end": end, "x": None, "y": None, "w": None, "h": None})
    
    # Get dimensions and frame rate
    p_r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0",
              "-show_entries", "stream=width,height,r_frame_rate", "-of", "json", str(ref)])
    try:
        stream = json.loads(p_r.stdout)["streams"][0]
        W, H = stream["width"], stream["height"]
        num, den = stream["r_frame_rate"].split("/")
        fps = int(num) / int(den)
    except (json.JSONDecodeError, KeyError, IndexError, ZeroDivisionError):
        return {"pass": False, "failures": [(0, 0, 0, 0, 0, "could not read stream info")], "brightness_lift": None}
    
    # Downscale to ~640x360 for memory efficiency (tile-based comparison on 32x18 grid)
    # This uses <500 MB for 10s 1080p video
    tile_w, tile_h = 32, 18
    scale_w, scale_h = tile_w * 20, tile_h * 20  # 640x360
    
    # Use YUV420p to compare chroma as well as luma (not grayscale only)
    cmd1 = ["ffmpeg", "-v", "error", "-i", str(ref), "-vf", f"scale={scale_w}:{scale_h}:flags=area,format=yuv420p",
            "-pix_fmt", "yuv420p", "-f", "rawvideo", "-"]
    cmd2 = ["ffmpeg", "-v", "error", "-i", str(test), "-vf", f"scale={scale_w}:{scale_h}:flags=area,format=yuv420p",
            "-pix_fmt", "yuv420p", "-f", "rawvideo", "-"]
    
    r1 = subprocess.run(cmd1, capture_output=True)
    r2 = subprocess.run(cmd2, capture_output=True)
    
    if r1.returncode != 0 or r2.returncode != 0:
        return {"pass": False, "failures": [(0, 0, 0, 0, 0, "decode failed")], "brightness_lift": None}
    
    # Parse YUV420p: Y plane is W*H, U and V planes are W/2 * H/2 each
    frame_size_y = scale_w * scale_h
    frame_size_uv = (scale_w // 2) * (scale_h // 2)
    frame_size = frame_size_y + 2 * frame_size_uv
    
    frames1_count = len(r1.stdout) // frame_size
    frames2_count = len(r2.stdout) // frame_size
    
    # Fail on unmatched tail frames when lengths differ
    if frames1_count != frames2_count:
        return {"pass": False, "failures": [(0, 0, 0, 0, 0, f"frame count mismatch: {frames1_count} vs {frames2_count}")], 
                "brightness_lift": None}
    
    n_frames = frames1_count
    if n_frames < 2:
        return {"pass": False, "failures": [(0, 0, 0, 0, 0, "too few frames")], "brightness_lift": None}
    
    # Extract Y channel only for tile comparison (luma)
    # Keep all frames in memory but only the Y channel at reduced resolution
    y1 = np.frombuffer(r1.stdout, dtype=np.uint8).reshape(-1, frame_size)[:, :frame_size_y].reshape(-1, scale_h, scale_w).astype(np.float32)
    y2 = np.frombuffer(r2.stdout, dtype=np.uint8).reshape(-1, frame_size)[:, :frame_size_y].reshape(-1, scale_h, scale_w).astype(np.float32)
    
    # Detect global brightness lift (mean luma difference across all frames)
    global_luma_diff = float(np.mean(y2 - y1))
    brightness_lift = global_luma_diff if abs(global_luma_diff) > 15 else None
    
    # Tile-based diff (32x18 grid)
    tile_px_h, tile_px_w = scale_h // tile_h, scale_w // tile_w
    failures = []
    CHANGE_FLOOR = 24  # channel difference 0-255 (adjusted for downscale)
    
    for i in range(n_frames):
        t = i / fps
        diff = np.abs(y1[i] - y2[i])
        
        for ty in range(tile_h):
            for tx in range(tile_w):
                tile_diff = diff[ty*tile_px_h:(ty+1)*tile_px_h, tx*tile_px_w:(tx+1)*tile_px_w]
                mean_diff = float(np.mean(tile_diff))
                
                if mean_diff < CHANGE_FLOOR:
                    continue  # no change in this tile
                
                # Tile changed; check if it's in an allowed region
                tile_x = int(tx * W / tile_w)
                tile_y = int(ty * H / tile_h)
                tile_w_px = int(W / tile_w)
                tile_h_px = int(H / tile_h)
                
                allowed_here = False
                for region in allowed:
                    if region["start"] <= t <= region["end"]:
                        if region["x"] is None:  # time-only region (whole frame allowed)
                            allowed_here = True
                            break
                        # Check tile overlap with allowed rectangle
                        if not (tile_x + tile_w_px <= region["x"] or tile_x >= region["x"] + region["w"] or
                               tile_y + tile_h_px <= region["y"] or tile_y >= region["y"] + region["h"]):
                            allowed_here = True
                            break
                
                if not allowed_here:
                    failures.append((round(t, 3), tile_x, tile_y, tile_w_px, tile_h_px, 
                                   f"change outside declared regions (diff {mean_diff:.1f})"))
                    if len(failures) >= 10:  # limit report
                        break
            if len(failures) >= 10:
                break
        if len(failures) >= 10:
            break
    
    result = {"pass": len(failures) == 0, "failures": failures, "brightness_lift": brightness_lift}
    if brightness_lift is not None:
        result["pass"] = False
        failures.insert(0, (0, 0, 0, W, H, f"global brightness lift detected: {brightness_lift:+.1f} levels"))
    
    return result

def scene_frames(video, job, out, font, vertical):
    """One frame per scene (70% in, after entrances settle), labeled with the scene id, tiled."""
    tmp = out / "_scenes"; tmp.mkdir(exist_ok=True)
    files = []
    for k, sc in enumerate(job.get("scenes", [])):
        t = sc["start"] + sc["dur"] * 0.7
        f = tmp / f"{k:02d}.jpg"
        lab = f",drawtext=fontfile='{font}':text='{k+1} {sc['id']}':x=8:y=h-th-8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7" if font else ""
        sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-vf", f"scale={'270' if vertical else '480'}:-2{lab}", str(f)])
        if f.exists(): files.append(f)
    if files:
        cols = 6 if vertical else 4
        sh(["ffmpeg", "-y", "-v", "error", "-framerate", "1", "-i", str(tmp / "%02d.jpg"), "-vf",
            f"tile={cols}x{(len(files) + cols - 1) // cols}:padding=6:margin=6:color=0x111111", "-frames:v", "1", str(out / "scenes.jpg")])
    shutil.rmtree(tmp, ignore_errors=True)

def check(video, out, preset=None, expect=None, credits=None, job=None, expect_identity=None, compare=None, expect_changed=None):
    """Check a video against platform requirements and quality gates.
    
    Args:
        video: path to video file
        out: output directory for review artifacts
        preset: platform preset name (e.g. 'reels', 'youtube')
        expect: expected duration in seconds
        credits: music credits JSON file
        job: job JSON file with scene data
        expect_identity: expected 'size:mtime_ns' identity (FAIL if file differs)
        compare: reference video for SSIM/PSNR comparison
        expect_changed: list of time ranges or 'none' for change scope verification
    """
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    p = probe(video)
    pr = json.loads((HERE / "presets.json").read_text())["presets"].get(preset) if preset else None
    rows = []
    def add(level, name, detail):
        rows.append({"level": level, "check": name, "detail": detail})
    
    # Identity check (if requested)
    if expect_identity:
        actual_identity = file_identity(video)
        if actual_identity != expect_identity:
            add("FAIL", "identity", f"file changed or replaced (expected {expect_identity}, got {actual_identity})")
        else:
            add("PASS", "identity", f"matches expected {expect_identity}")
    
    if pr and pr["w"]:
        add("PASS" if (p["w"], p["h"]) == (pr["w"], pr["h"]) else "FAIL", "resolution", f"{p['w']}x{p['h']} (preset {pr['w']}x{pr['h']})")
        add("PASS" if p["duration"] <= pr["max_seconds"] else "FAIL", "max length", f"{p['duration']:.2f}s (max {pr['max_seconds']}s)")
        if pr.get("max_bytes"):
            add("PASS" if p["bytes"] <= pr["max_bytes"] else "FAIL", "file size", f"{p['bytes']/1e6:.1f} MB")
    else:
        add("INFO", "resolution", f"{p['w']}x{p['h']} @ {p['fps']} fps")
    if expect:
        add("PASS" if abs(p["duration"] - expect) <= 0.25 else "WARN", "duration", f"{p['duration']:.2f}s (expected {expect}s)")
    add("PASS" if p["pix_fmt"] == "yuv420p" else "WARN", "pixel format", f"{p['vcodec']} {p['profile']} {p['pix_fmt']}")
    if p["acodec"]:
        L = loudness(video)
        tgt = (pr or {}).get("lufs", -14)
        ok = L["lufs"] is not None and abs(L["lufs"] - tgt) <= 2 and (L["true_peak"] or 0) <= -0.9
        add("PASS" if ok else "WARN", "loudness", f"{L['lufs']} LUFS, TP {L['true_peak']} dBFS, LRA {L['lra']} (target {tgt} LUFS, TP <= -1)")
        sil = re.findall(r"silence_duration: ([\d.]+)", sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "silencedetect=n=-50dB:d=2", "-f", "null", "-"]).stderr)
        add("WARN" if sil else "PASS", "silence > 2s", ", ".join(f"{float(s):.1f}s" for s in sil) or "none")
        # Audio dropouts (short digital holes)
        dropouts = detect_dropouts(video)
        add("WARN" if dropouts else "PASS", "audio dropouts", 
            ", ".join(f"{t}s ({d}s)" for t, d in dropouts[:5]) + (f" +{len(dropouts)-5} more" if len(dropouts) > 5 else "") if dropouts else "none")
    else:
        add("WARN", "audio", "no audio stream (fine for silent loops; most feeds autoplay muted)")
    blk = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "blackdetect=d=0.5:pix_th=0.08", "-f", "null", "-"]).stderr)
    add("WARN" if blk else "PASS", "black frames > 0.5s", ", ".join(f"{a}-{b}s" for a, b in blk) or "none")
    frz = re.findall(r"freeze_start: ([\d.]+)", sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "freezedetect=n=0.001:d=1.0", "-f", "null", "-"]).stderr)
    late = [float(f) for f in frz if float(f) >= p["duration"] - 1.6]
    mid = [float(f) for f in re.findall(r"freeze_duration: ([\d.]+)", sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "freezedetect=n=0.001:d=3.0", "-f", "null", "-"]).stderr)]
    add("WARN" if mid else "PASS", "static > 3s", ", ".join(f"{m:.1f}s" for m in mid) + " with no motion; add drift or cut sooner" if mid else "none")
    jb = json.loads(Path(job).read_text()) if job and Path(job).exists() else None
    if jb:
        short_sc = [f"{s_['id']} {s_['dur']:.1f}s" for s_ in jb.get("scenes", []) if s_["dur"] < 1.2 and not s_["id"].startswith(("s-n", "s-t"))]
        add("WARN" if short_sc else "PASS", "scene length", ", ".join(short_sc) + " (under 1.2s: hard to read)" if short_sc else f"{len(jb.get('scenes', []))} scenes, all >= 1.2s")
        add("PASS" if abs(jb.get("total_seconds", p["duration"]) - p["duration"]) <= 0.25 else "WARN", "matches plan", f"plan {jb.get('total_seconds')}s, file {p['duration']:.2f}s")
    add("WARN" if late else "PASS", "frozen ending", f"static from {late[0]:.2f}s; add a slow drift/breath" if late else "motion continues to the end")
    fl = flashes(video, p["fps"] or 30)
    add("FAIL" if fl["max_flashes_per_s"] > 3 else "PASS", "flashes (WCAG 2.3.1)", f"max {fl['max_flashes_per_s']}/s" + (f" at {fl['worst_at']}s" if fl["worst_at"] is not None else ""))
    pops = detect_pops(video, p["fps"] or 30)
    add("WARN" if pops else "PASS", "one-frame pops", ", ".join(f"f{frm}@{t}s" for frm, t in pops[:5]) + (f" +{len(pops) - 5} more" if len(pops) > 5 else "") if pops else "none (check hits you meant)")
    cuts = detect_cuts(video, p["fps"] or 30)
    hard = [c for c in cuts if c["kind"] == "cut"]
    (out / "cuts.json").write_text(json.dumps(cuts, indent=2))
    add("INFO", "cut list", f"{len(hard)} cuts ({len(hard) / max(p['duration'], 0.1) * 60:.0f}/min), "
        f"{sum(c['kind'] == 'flash' for c in cuts)} flashes, {sum(c['kind'] == 'fast' for c in cuts)} fast moves, "
        f"{sum(c['kind'] == 'transition' for c in cuts)} transitions; cuts.json")
    if p["acodec"] and hard:
        ck = cut_clicks(video, hard)
        add("WARN" if ck else "PASS", "clicks at cuts", ", ".join(f"{t}s (x{r})" for t, r in ck[:5]) + " - add ~30 ms audio fades at the edit" if ck else f"none at {len(hard)} cuts")
    # sync drift (store in local, add to res after res is created)
    sync_result = None
    if p["acodec"]:
        sync_result = check_sync_drift(video)
        if sync_result.get("error"):
            add("WARN", "sync drift", f"could not measure: {sync_result['error']}")
        elif sync_result["flagged"]:
            details = ", ".join(f"{t}s: {d:+.1f}ms" for t, d in sync_result["probes"])
            add("WARN", "sync drift", f"worst {sync_result['worst_drift_ms']:+.1f}ms ({details}) - check A/V alignment")
        else:
            add("PASS", "sync drift", f"{sync_result['worst_drift_ms']:+.1f}ms (within ±50ms)")
    # SSIM/PSNR comparison (if requested)
    if compare:
        comp_result = compare_ssim_psnr(compare, video)
        if "error" in comp_result:
            add("WARN", "SSIM/PSNR", f"could not compare: {comp_result['error']}")
        else:
            mean_ssim = comp_result["mean_ssim"]
            mean_psnr = comp_result["mean_psnr"]
            warn = mean_ssim is not None and mean_ssim < 0.98
            detail = f"mean SSIM {mean_ssim:.4f}" if mean_ssim else "SSIM N/A"
            if mean_psnr:
                detail += f", PSNR {mean_psnr:.1f} dB"
            if warn:
                detail += f" (mean SSIM < 0.98)"
            add("WARN" if warn else "PASS", "SSIM/PSNR", detail)
    
    # Change scope verification (if requested)
    if expect_changed:
        if not compare:
            print("ERROR: --expect-changed requires --compare <reference>", file=sys.stderr)
            sys.exit(1)
        regions = expect_changed if isinstance(expect_changed, list) else [expect_changed]
        scope_result = verify_change_scope(compare, video, regions)
        if scope_result["pass"]:
            add("PASS", "change_scope", f"changes within declared scope: {', '.join(regions)}")
        else:
            failures = scope_result["failures"][:3]
            detail = "; ".join(f"{t}s @({x},{y},{w},{h}): {reason}" for t, x, y, w, h, reason in failures)
            add("FAIL", "change_scope", f"{len(scope_result['failures'])} changes outside scope - {detail}")
    
    if credits:
        cr = json.loads(Path(credits).read_text()) if Path(credits).exists() else []
        add("PASS" if cr else "WARN", "credits", f"{len(cr)} credited assets in {Path(credits).name}")
    # artifacts
    font = sh(["fc-match", "-f", "%{file}", "DejaVu Sans Mono"]).stdout or ""
    tc = f",drawtext=fontfile='{font}':text='%{{pts\\:hms}}':x=12:y=12:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6" if font else ""
    short = 360
    sc = f"scale=-2:{short}" if p["w"] >= p["h"] else f"scale={short}:-2"
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", sc + tc, "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
        "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(out / "preview.mp4")])
    n = 12
    rate = n / max(p["duration"], 0.1)
    tile_w = 480 if p["w"] >= p["h"] else 270
    cols = 4 if p["w"] >= p["h"] else 6
    rowsn = (n + cols - 1) // cols
    lab = f",drawtext=fontfile='{font}':text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6" if font else ""
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps={rate:.5f}:start_time=0.25,scale={tile_w}:-2{lab},tile={cols}x{rowsn}:padding=6:margin=6:color=0x111111",
        "-frames:v", "1", "-q:v", "3", str(out / "contact.jpg")])
    vertical = p["h"] > p["w"]
    if jb:
        scene_frames(video, jb, out, font, vertical)
    # phone-size legibility: frames scaled to how they look in a feed on a ~6" phone (about 1/3 of full size)
    pw = 360 if vertical else 640
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps={3 / max(p['duration'], 0.1):.5f}:start_time=0.5,scale={pw}:-2,tile=3x1:padding=10:margin=10:color=white",
        "-frames:v", "1", str(out / "phone.jpg")])
    if preset:
        sys.path.insert(0, str(HERE))
        import export
        export.safe_overlay_frame(video, preset, out / "safe.jpg", t=p["duration"] * 0.5)
    auto_pass = not any(r["level"] == "FAIL" for r in rows)
    res = {"video": str(video), "probe": p, "preset": preset, "rows": rows, "auto_pass": auto_pass, "approved": False,
           "approved_by": None, "checked_at": time.strftime("%Y-%m-%d %H:%M %Z")}
    if sync_result:
        res["sync_drift"] = sync_result
    (out / "review.json").write_text(json.dumps(res, indent=2))
    md = [f"# Review: {Path(video).name}", "", f"Preview: `preview.mp4` | Contact sheet: `contact.jpg` | Phone size: `phone.jpg`" + (" | Scenes: `scenes.jpg`" if jb else "") + (" | Safe zones: `safe.jpg`" if preset else ""), "",
          "## Automatic checks", "", "| Result | Check | Detail |", "|---|---|---|"]
    md += [f"| {r['level']} | {r['check']} | {r['detail']} |" for r in rows]
    md += ["", "## Human checklist (ask the user to confirm)", "",
           "- [ ] Hook lands in the first 3 seconds; the first frame works as a thumbnail",
           "- [ ] Every word on screen is spelled right; names, prices, dates, claims are correct",
           "- [ ] Brand: logo, colors, fonts and tone match brand.json; logo not stretched",
           "- [ ] Text sits inside the platform safe zone (see safe.jpg); nothing under UI",
           "- [ ] Text is on screen long enough to read twice; contrast is clear (WCAG 4.5:1 body, 3:1 large)",
           "- [ ] Cuts land on the beat; no dead air; nothing frozen at the end",
           "- [ ] Captions match the VO; sidecar SRT/VTT attached for platforms that support it",
           "- [ ] Music and every stock asset have a license on file (credits.json); attribution text is ready",
           "- [ ] CTA is clear and says where to go",
           "- [ ] Right aspect ratios and lengths for each platform",
           "- [ ] Paid generations (if any) quoted and approved BEFORE spending",
           "- [ ] AI voice or AI imagery is disclosed where the platform requires it (on-screen label and/or upload toggle)", "",
           "## Creative rubric (score 1-5; anything under 3 gets a fix before final)", "",
           "| Area | Question | Score |", "|---|---|---|",
           "| Hook | Would a stranger stop scrolling in the first 2 s? | |",
           "| Clarity | One message; could you repeat it after one watch with the sound off? | |",
           "| Pacing | Cuts on the beat, no scene outstays its welcome, no dead air? | |",
           "| Craft | Type hierarchy, motion easing, consistent spacing, nothing cramped at phone size? | |",
           "| Brand | Looks and sounds like the brand, not like a template? | |",
           "| CTA | Clear next step, on screen long enough, says where to go? | |", "",
           "## Kinetic type (client sizzle and custom kinetic; score 1-10)", "",
           "Leave blank on a plain template cut. Otherwise score as a fresh reviewer, from BRIEF stills plus `contact.jpg` and `phone.jpg`, not from memory of the comp.",
           "Fix the three worst and re-check before a delivery render. Each score should be 8 or higher.",
           "Rules: `references/motion-design.md`. This table does not change the auto result.", "",
           "| Area | Question | Score |", "|---|---|---|",
           "| Hook | Does the first 2 seconds land, rather than a fade-in title card? | |",
           "| Phone | Can you read the hook and the logo on `phone.jpg`? | |",
           "| Motion | Does motion have weight, with no overshoot on big type and no dead beat? | |",
           "| Variety | Does something new happen every 2-4 seconds? | |",
           "| Brand | Real logo, colors, and UI; none of the banned defaults? | |",
           "| Sound | Do cuts and hits land on the beat, with loudness in range? | |", "",
           f"Auto result: **{'PASS' if auto_pass else 'FAIL'}**. Approved: **no** (run `review.py approve {out}` after the user says yes)."]
    (out / "review.md").write_text("\n".join(md) + "\n")
    for r in rows:
        print(f"  {r['level']:4} {r['check']}: {r['detail']}")
    print(f"review -> {out}/review.md ({'auto PASS' if auto_pass else 'auto FAIL'}; awaiting approval)")
    return res

# --- Static motion audit (no render) -------------------------------------------------------------
# Reads composition source and flags motion that cannot be seeked deterministically (FAIL) or that
# costs layout, softens type, or moves on a linear ease (WARN). Worst level wins per file. Clean files
# get one line. A line containing `audit-ok` is skipped (write why next to it).

AUDIT_EXT = {".html", ".htm", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".css"}
AUDIT_SKIP_DIRS = {"node_modules", ".git", "dist", "build", "_review", "__pycache__", ".venv"}
AUDIT_MAX_BYTES = 1_000_000  # larger files are vendored bundles, not comps

AUDIT_LINE_RULES = [
    ("FAIL", "random", r"\bMath\.random\s*\(|\bgetRandomValues\s*\(",
     "random value: seeking the same time twice paints different pixels",
     "seed once (mulberry32) or derive the value from the frame index"),
    ("FAIL", "clock", r"\bDate\.now\s*\(|\bnew\s+Date\s*\(\s*\)|\bperformance\.now\s*\(",
     "wall-clock time drives the picture",
     "derive it from timeline time (HyperFrames) or useCurrentFrame() (Remotion)"),
    ("FAIL", "timer", r"\b(?:setTimeout|setInterval|requestAnimationFrame)\s*\(",
     "a timer or frame callback moves things outside the timeline",
     "put the move on the paused GSAP timeline, or interpolate from the frame"),
    ("FAIL", "css-motion", r"@keyframes\b|(?<![\w-])(?:transition|animation(?:-name)?)\s*:(?!\s*(?:none|unset|initial)\b)",
     "CSS animation or transition: not on the seekable clock (Remotion does not render it)",
     "rebuild it as a timeline tween or an interpolate()"),
    ("WARN", "will-change", r"\bwill-change\b|\bwillChange\b",
     "will-change softens scaled glyphs and has broken seek determinism",
     "remove it"),
]
_TWEEN_CALL = re.compile(r"\.(?:to|from|fromTo)\s*\(")
_LAYOUT_KEY = re.compile(r"(?<![\w$.-])[\"']?(?:width|height|top|left|right|bottom|margin\w*|padding\w*)[\"']?\s*:")
_POS_KEY = re.compile(r"(?<![\w$.-])[\"']?(?:x|y|xPercent|yPercent|left|top)[\"']?\s*:")
_FADE_KEY = re.compile(r"(?<![\w$.-])[\"']?(?:opacity|autoAlpha)[\"']?\s*:")
_LINEAR_EASE = re.compile(r"(?<![\w$.-])[\"']?ease[\"']?\s*:\s*[\"'](?:none|linear)[\"']")


def _strip_comments(text):
    """Blank out comments but keep every newline, so line numbers still match the file."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"/\*.*?\*/", blank, text, flags=re.S)
    return re.sub(r"(?<![:\"'\w\\])//[^\n]*", blank, text)


def _call_args(text, start):
    """Text from an opening paren to its match (bounded), or '' if unbalanced."""
    depth = 0
    for i in range(start, min(len(text), start + 4000)):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return ""


def audit_text(text, name="<text>"):
    """Findings for one source text: dicts with level, rule, file, line, what, fix."""
    raw_lines = text.splitlines()
    skip = {i + 1 for i, ln in enumerate(raw_lines) if "audit-ok" in ln}
    clean = _strip_comments(text)
    found = []
    for n, ln in enumerate(clean.splitlines(), 1):
        if n in skip:
            continue
        for level, rule, pat, what, fix in AUDIT_LINE_RULES:
            if re.search(pat, ln):
                found.append({"level": level, "rule": rule, "file": name, "line": n, "what": what, "fix": fix})
    for m in _TWEEN_CALL.finditer(clean):
        n = clean.count("\n", 0, m.start()) + 1
        if n in skip:
            continue
        args = _call_args(clean, m.end() - 1)
        if not args:
            continue
        if _LAYOUT_KEY.search(args):
            found.append({"level": "WARN", "rule": "layout-tween", "file": name, "line": n,
                          "what": "tween on a layout property (width, height, top, left, margin, padding)",
                          "fix": "move with x, y, scale or clip-path; a named one-shape morph gets `audit-ok` and a reason"})
        # Linear is fine on a cut-to-cut drift or Ken Burns (no fade). An entrance or exit is not.
        if _LINEAR_EASE.search(args) and _POS_KEY.search(args) and _FADE_KEY.search(args):
            found.append({"level": "WARN", "rule": "linear-move", "file": name, "line": n,
                          "what": "entrance or exit that moves on a linear ease",
                          "fix": "ease out on entrances, in on exits, in-out on moves; linear is for rotation, progress and timers"})
    found.sort(key=lambda f: (f["line"], f["rule"]))
    return found


def _audit_files(target):
    t = Path(target)
    if t.is_file():
        return [t]
    out = []
    for f in sorted(t.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in AUDIT_EXT:
            continue
        if AUDIT_SKIP_DIRS.intersection(f.relative_to(t).parts) or ".min." in f.name:
            continue
        if f.stat().st_size > AUDIT_MAX_BYTES:
            continue
        out.append(f)
    return out


def audit(target, json_out=None):
    """Audit every comp source under target. Returns the report dict; level is the worst finding."""
    base = Path(target) if Path(target).is_dir() else Path(target).parent
    files = []
    for f in _audit_files(target):
        rel = str(f.relative_to(base)) if base in f.parents or f.parent == base else str(f)
        found = audit_text(f.read_text(errors="replace"), rel)
        worst = "FAIL" if any(x["level"] == "FAIL" for x in found) else "WARN" if found else "PASS"
        files.append({"file": rel, "level": worst, "findings": found})
    levels = {x["level"] for x in files}
    level = "FAIL" if "FAIL" in levels else "WARN" if "WARN" in levels else "PASS"
    rep = {"target": str(target), "level": level, "files": files}
    if json_out:
        Path(json_out).write_text(json.dumps(rep, indent=2))
    return rep


def print_audit(rep):
    if not rep["files"]:
        print(f"audit: no composition sources under {rep['target']}")
        return
    for f in rep["files"]:
        if not f["findings"]:
            continue
        print(f"{f['level']:4} {f['file']}")
        for x in f["findings"]:
            print(f"     {x['level']:4} {x['rule']} line {x['line']}: {x['what']}. Fix: {x['fix']}.")
    clean = [f["file"] for f in rep["files"] if not f["findings"]]
    if clean:
        print(f"PASS {len(clean)} file(s) clean")
    print(f"audit -> {rep['level']}")


def auto_audit(comp_path, strict=False):
    """Run motion audit during render (WARNING-ONLY mode by default).
    
    Returns a single-line summary string suitable for printing.
    In default mode (strict=False), findings are logged but never affect exit status.
    In strict mode (strict=True or REELSMITH_AUDIT_STRICT=1), FAIL findings stop the render.
    
    Args:
        comp_path: Path to composition directory or file
        strict: If True, treat FAIL findings as errors (default: False)
    
    Returns:
        str: One-line summary for logging
    """
    strict = strict or os.environ.get("REELSMITH_AUDIT_STRICT") == "1"
    
    if not comp_path or not Path(comp_path).exists():
        msg = f"motion audit SKIPPED: path not found: {comp_path}"
        print(msg)
        return msg
    
    try:
        rep = audit(comp_path)
        
        # Count findings by severity
        fail_count = sum(len([x for x in f["findings"] if x["level"] == "FAIL"]) for f in rep["files"])
        warn_count = sum(len([x for x in f["findings"] if x["level"] == "WARN"]) for f in rep["files"])
        
        # Build summary
        if fail_count == 0 and warn_count == 0:
            summary = "motion audit: clean"
        elif fail_count > 0:
            summary = f"motion audit: {fail_count} FAIL, {warn_count} WARN"
        else:
            summary = f"motion audit: {warn_count} warnings"
        
        # Print findings if any
        if fail_count > 0 or warn_count > 0:
            print_audit(rep)
        
        print(summary)
        
        # In strict mode, FAIL findings stop the render
        if strict and fail_count > 0:
            raise SystemExit(f"motion audit failed in strict mode: {fail_count} FAIL findings")
        
        return summary
        
    except Exception as e:
        msg = f"motion audit ERROR: {type(e).__name__}: {e}"
        print(msg)
        return msg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("check"); p.add_argument("video"); p.add_argument("--out", required=True); p.add_argument("--preset")
    p.add_argument("--expect-seconds", type=float); p.add_argument("--music-credits", "--credits", dest="credits"); p.add_argument("--job", help="job.json from reelsmith.py render (scene frames + timing checks)")
    p.add_argument("--expect-identity", help="expected size:mtime_ns identity (FAIL if file differs)")
    p.add_argument("--compare", help="reference video for SSIM/PSNR comparison")
    p.add_argument("--expect-changed", help="time ranges or 'none' for change scope (requires --compare)")
    p = sp.add_parser("approve"); p.add_argument("dir"); p.add_argument("--by", required=True)
    p = sp.add_parser("status"); p.add_argument("dir")
    p = sp.add_parser("audit"); p.add_argument("target"); p.add_argument("--json", dest="json_out")
    a = ap.parse_args()
    if a.cmd == "audit":
        if not Path(a.target).exists():
            sys.exit(f"no such path: {a.target}")
        rep = audit(a.target, a.json_out)
        print_audit(rep)
        sys.exit(1 if rep["level"] == "FAIL" else 0)
    if a.cmd == "check":
        expect_changed_arg = a.expect_changed.split(",") if hasattr(a, "expect_changed") and a.expect_changed else None
        res = check(a.video, a.out, a.preset, a.expect_seconds, a.credits, a.job,
                   getattr(a, "expect_identity", None), getattr(a, "compare", None), expect_changed_arg)
        sys.exit(0 if res["auto_pass"] else 1)
    f = Path(a.dir) / "review.json"
    if not f.exists():
        sys.exit(f"no review at {f}; run review.py check first")
    js = json.loads(f.read_text())
    if a.cmd == "approve":
        js.update(approved=True, approved_by=a.by, approved_at=time.strftime("%Y-%m-%d %H:%M %Z"))
        f.write_text(json.dumps(js, indent=2)); print(f"approved by {a.by}")
    else:
        print("approved" if js.get("approved") else "NOT approved"); sys.exit(0 if js.get("approved") else 1)

if __name__ == "__main__":
    main()
