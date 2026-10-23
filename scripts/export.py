#!/usr/bin/env python3
"""Per-platform export: resize/fit, H.264 High + AAC, closed GOP, two-pass loudnorm, faststart,
metadata stripped, limit checks, thumbnail/cover, caption sidecars.

  export.py run VIDEO --preset reels,tiktok,youtube --out DIR --review REVIEW_DIR
            [--fit pad-blur|crop|pad] [--thumb-at 1.2] [--srt captions.srt] [--vtt captions.vtt]
  export.py overlay --preset reels -o reels-safe.png         # transparent safe-zone guide
  export.py list                                              # show presets
  export.py loudnorm IN.mp4 OUT.mp4 [--lufs -14]              # master the mix only (video stream copied); not a delivery
The review gate: REVIEW_DIR/review.json must be approved (see review.py). --unreviewed skips it for
internal tests only; never for a deliverable.
"""
import argparse, re, json, math, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRESETS = json.loads((HERE / "presets.json").read_text())["presets"]

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe(v):
    js = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration,size", "-of", "json", str(v)]).stdout)
    vs = next(s for s in js["streams"] if s["codec_type"] == "video")
    has_a = any(s["codec_type"] == "audio" for s in js["streams"])
    n, d = vs["r_frame_rate"].split("/")
    return {"w": vs["width"], "h": vs["height"], "fps": int(n) / int(d), "duration": float(js["format"]["duration"]),
            "bytes": int(js["format"]["size"]), "audio": has_a}

def overlay_png(preset, out, w=None, h=None):
    from PIL import Image, ImageDraw
    p = PRESETS[preset]
    W, H = w or p["w"], h or p["h"]
    s = p["safe"]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    red = (255, 40, 60, 90)
    t, b, l, r = int(H * s["top"]), int(H * s["bottom"]), int(W * s["left"]), int(W * s["right"])
    d.rectangle([0, 0, W, t], fill=red); d.rectangle([0, H - b, W, H], fill=red)
    d.rectangle([0, t, l, H - b], fill=red); d.rectangle([W - r, t, W, H - b], fill=red)
    if "right_rail" in s:
        d.rectangle([int(W * s["right_rail"]["x"]), int(H * s["right_rail"]["y"]), W - r, H - b], fill=(255, 140, 0, 90))
    d.rectangle([l, t, W - r, H - b], outline=(0, 255, 140, 255), width=max(2, W // 400))
    # title-safe guide (inner 90%)
    d.rectangle([int(W * .05), int(H * .05), int(W * .95), int(H * .95)], outline=(255, 255, 255, 120), width=max(1, W // 800))
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(sh(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"]).stdout, max(18, W // 45))
        d.text((l + 10, t + 10), f"{p['label']} safe area", fill=(0, 255, 140, 255), font=f)
    except Exception:
        pass
    im.save(out)
    return out

def safe_overlay_frame(video, preset, out, t=1.0):
    p = probe(video)
    png = Path(out).with_suffix(".overlay.png")
    overlay_png(preset, png, p["w"], p["h"])
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-i", str(png), "-filter_complex", "[0:v][1:v]overlay=0:0", "-frames:v", "1", "-q:v", "3", str(out)])
    png.unlink(missing_ok=True)
    return out

def fit_filter(src, p, mode):
    W, H = p["w"] or src["w"], p["h"] or src["h"]
    W, H = W - W % 2, H - H % 2
    same = abs(src["w"] / src["h"] - W / H) < 0.01
    if same or mode == "crop":
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1", same
    if mode == "pad":
        return f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1", False
    return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.08[bg];"
            f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"), False

def measure_loudness(v):
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(v), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    txt = r.stderr
    return json.loads(txt[txt.rfind("{"):txt.rfind("}") + 1])

def true_peak(f):
    """Integrated loudness + true peak of the encoded file (what the platform will measure)."""
    t = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", t); P = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", t)
    return (float(I[-1]) if I else None), (float(P[-1]) if P and P[-1] != "-inf" else -99.0)

def master_audio(src, out, lufs=-14.0, kbps=192, hz=48000, ceiling=-1.0, meas=None, keep_wav=None):
    """Two-pass loudnorm (linear) + an oversampled peak limiter to WAV, then AAC, then re-measure the ENCODED file.
    AAC adds 0.5-1.5 dB of true-peak overshoot on transient-heavy mixes (worse at 128k), so if the encoded file is still
    above the ceiling, trim the gain by the overshoot + 0.2 dB and re-encode (max 3 passes). Costs at most ~1 LU."""
    L = meas or measure_loudness(src)
    wav = Path(out).with_suffix(".pre.wav")
    af = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={L['input_i']}:measured_TP={L['input_tp']}:measured_LRA={L['input_lra']}"
          f":measured_thresh={L['input_thresh']}:offset={L['target_offset']}:linear=true,"
          f"aresample=192000,alimiter=limit=-2.5dB:attack=1:release=50:level=false,aresample={hz}")
    r = sh(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:a:0", "-vn", "-af", af, "-ac", "2", "-c:a", "pcm_s24le", str(wav)])
    if r.returncode:
        raise SystemExit(f"audio master failed: {r.stderr[-400:]}")
    gain = 0.0
    for _ in range(3):
        r = sh(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", f"volume={gain:.2f}dB", "-c:a", "aac", "-aac_coder", "fast",
                "-b:a", f"{kbps}k", "-ar", str(hz), str(out)])
        if r.returncode:
            raise SystemExit(f"aac encode failed: {r.stderr[-400:]}")
        I, P = true_peak(out)
        if P <= ceiling:
            break
        gain = max(gain - (P - ceiling) - 0.2, -3.0)   # never trim more than 3 dB
    if keep_wav is None:
        wav.unlink(missing_ok=True)
    return I, P

def export_one(video, preset, outdir, mode="pad-blur", thumb_at=None, srt=None, vtt=None, src=None, meas=None):
    p = PRESETS[preset]
    src = src or probe(video)
    fps = p["fps"] or round(src["fps"])
    vf, same = fit_filter(src, p, mode)
    gop = fps // 2 if p["gop"] == "half_fps" else 2 * fps
    out = Path(outdir) / f"{Path(video).stem}-{preset}.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(video)]
    amap = []
    if src["audio"]:
        aud = Path(outdir) / f".{Path(video).stem}-{preset}.m4a"
        master_audio(video, aud, p.get("lufs", -14), p["audio_kbps"], p["audio_hz"], p.get("true_peak", -1.0), meas)
        cmd += ["-i", str(aud)]
        amap = ["-map", "1:a:0", "-c:a", "copy"]
    cmd += ["-filter_complex", f"[0:v]{vf},fps={fps},format=yuv420p[v]", "-map", "[v]"] + amap
    v = ["-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0", "-bf", "2", "-flags", "+cgop"]
    if p.get("video_kbps"):
        v += ["-crf", "18", "-maxrate", f"{p['maxrate_kbps']}k", "-bufsize", f"{p['maxrate_kbps'] * 2}k"]
    else:
        v += ["-crf", str(p.get("crf", 16))]
    v += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", "-map_metadata", "-1"]
    r = sh(cmd + v + ["-shortest", str(out)])
    if src["audio"]:
        aud.unlink(missing_ok=True)
    if r.returncode:
        raise SystemExit(f"{preset}: ffmpeg failed: {r.stderr[-400:]}")
    o = probe(out)
    notes = []
    if o["duration"] > p["max_seconds"]:
        notes.append(f"FAIL over {preset} max length ({o['duration']:.1f}s > {p['max_seconds']}s)")
    if p.get("max_bytes") and o["bytes"] > p["max_bytes"]:
        notes.append(f"FAIL over {preset} max size")
    if not same:
        notes.append(f"aspect converted with '{mode}'; a native render at {p['w']}x{p['h']} looks better")
    # thumbnail / cover
    th = p["thumb"]
    if th.get("w"):
        t = thumb_at if thumb_at is not None else min(1.2, o["duration"] / 3)
        tf = Path(outdir) / f"{Path(video).stem}-{preset}-thumb.{th['format']}"
        q = 2
        while True:
            sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(out), "-frames:v", "1", "-vf",
                f"scale={th['w']}:{th['h']}:force_original_aspect_ratio=increase,crop={th['w']}:{th['h']}", "-q:v", str(q), str(tf)])
            if not th.get("max_bytes") or tf.stat().st_size <= th["max_bytes"] or q >= 10:
                break
            q += 2
    for side in (srt, vtt):
        if side:
            shutil.copy(side, Path(outdir) / f"{Path(video).stem}-{preset}{Path(side).suffix}")
    rep = {"preset": preset, "file": str(out), "w": o["w"], "h": o["h"], "fps": o["fps"], "seconds": round(o["duration"], 3),
           "mb": round(o["bytes"] / 1e6, 2), "notes": notes}
    print(f"  {preset:16} {o['w']}x{o['h']} {o['fps']:.0f}fps {o['duration']:.2f}s {rep['mb']} MB {'; '.join(notes)}")
    return rep

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("run"); p.add_argument("video"); p.add_argument("--preset", required=True); p.add_argument("--out", required=True)
    p.add_argument("--review"); p.add_argument("--unreviewed", action="store_true"); p.add_argument("--fit", default="pad-blur", choices=["pad-blur", "crop", "pad"])
    p.add_argument("--thumb-at", type=float); p.add_argument("--srt"); p.add_argument("--vtt")
    p = sp.add_parser("overlay"); p.add_argument("--preset", required=True); p.add_argument("-o", "--out", required=True)
    sp.add_parser("list")
    p = sp.add_parser("loudnorm"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    if a.cmd == "loudnorm":
        aud = Path(a.dst).with_suffix(".tmp.m4a")
        I, P = master_audio(a.src, aud, a.lufs)
        r = sh(["ffmpeg", "-y", "-v", "error", "-i", a.src, "-i", str(aud), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                "-movflags", "+faststart", "-shortest", a.dst])
        aud.unlink(missing_ok=True)
        if r.returncode: sys.exit(r.stderr[-400:])
        print(f"loudnorm {a.src} -> {a.dst}: {I} LUFS, true peak {P} dBTP (encoded)"); return
    if a.cmd == "list":
        for k, v in PRESETS.items():
            print(f"  {k:16} {v['label']:36} {v['w']}x{v['h']} max {v['max_seconds']}s")
        return
    if a.cmd == "overlay":
        print(overlay_png(a.preset, a.out)); return
    if not a.unreviewed:
        rv = Path(a.review or "") / "review.json"
        if not a.review or not rv.exists() or not json.loads(rv.read_text()).get("approved"):
            sys.exit("Export blocked: run review.py check, show the user preview/contact sheet, then review.py approve. (--unreviewed is for internal tests only.)")
    Path(a.out).mkdir(parents=True, exist_ok=True)
    src = probe(a.video)
    meas = measure_loudness(a.video) if src["audio"] else None
    reps = [export_one(a.video, pr.strip(), a.out, a.fit, a.thumb_at, a.srt, a.vtt, src, meas) for pr in a.preset.split(",")]
    (Path(a.out) / "export-report.json").write_text(json.dumps(reps, indent=2))
    sys.exit(1 if any(n.startswith("FAIL") for r in reps for n in r["notes"]) else 0)

if __name__ == "__main__":
    main()
