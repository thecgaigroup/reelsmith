#!/usr/bin/env python3
"""Review gate: required before the final render/export and before ANY paid generation.

  review.py check VIDEO --out DIR [--preset reels] [--expect-seconds 15] [--music-credits credits.json] [--job job.json]
      -> DIR/preview.mp4 (low-res, timecoded), DIR/contact.jpg (ffmpeg tile), DIR/safe.jpg,
         DIR/scenes.jpg (one labeled frame per scene, with --job), DIR/phone.jpg (frames at phone size: can you read it?),
         DIR/review.md (checklist), DIR/review.json (auto results, approved=false)
  review.py approve DIR --by "name or 'user in chat'"     # record the user's OK
  review.py status DIR                                     # exit 0 only if approved

Auto checks: resolution/fps/duration vs preset, loudness (EBU R128 integrated + true peak),
black frames, long silence (dead air), frozen mid-video stretches, frozen ending, photosensitive flashes (WCAG 2.3.1 heuristic),
scene timing vs job.json (every scene long enough to read).
"""
import argparse, json, re, shutil, subprocess, sys, time
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

def check(video, out, preset=None, expect=None, credits=None, job=None):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    p = probe(video)
    pr = json.loads((HERE / "presets.json").read_text())["presets"].get(preset) if preset else None
    rows = []
    def add(level, name, detail):
        rows.append({"level": level, "check": name, "detail": detail})
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

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("check"); p.add_argument("video"); p.add_argument("--out", required=True); p.add_argument("--preset")
    p.add_argument("--expect-seconds", type=float); p.add_argument("--music-credits", "--credits", dest="credits"); p.add_argument("--job", help="job.json from reelsmith.py render (scene frames + timing checks)")
    p = sp.add_parser("approve"); p.add_argument("dir"); p.add_argument("--by", required=True)
    p = sp.add_parser("status"); p.add_argument("dir")
    a = ap.parse_args()
    if a.cmd == "check":
        res = check(a.video, a.out, a.preset, a.expect_seconds, a.credits, a.job)
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
