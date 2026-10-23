#!/usr/bin/env python3
"""YouTube publish-prep: builds everything you need to upload by hand. It NEVER uploads.

  youtube_prep.py VIDEO --job DIR/job.json --out DIR/youtube [--title "..."] [--summary "..."] [--tags a,b,c]
                  [--thumb-at 3.2] [--thumb-text "3 steps"] [--brand brand.json] [--srt file.srt] [--review DIR/_review]
                  [--made-for-kids no] [--privacy private]

Writes DIR/youtube/:
  metadata.json       title, description, tags, category, privacy, language, chapters, AI-disclosure flags
  description.txt     ready to paste (summary + chapters + credits + links)
  thumbnail.jpg       1280x720, < 2 MB, brand font, big 2-4 word text, high contrast
  captions.srt/.vtt   copied sidecars (upload them; auto-captions are worse)
  upload-checklist.md QA gates (PASS/FAIL) + the manual steps in YouTube Studio
  manifest.json       sha256 + bytes of every file, so the uploaded file is provably the reviewed one

Gates (exit 1 if any FAIL): review approved (review.py approve), H.264/yuv420p/AAC, 16:9 for regular uploads
(9:16 <= 3 min is treated as a Short), title <= 100 chars, description <= 5000, tags <= 500 chars total,
chapters valid (first at 0:00, >= 3, each >= 10 s) or omitted with a note.
"""
import argparse, hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe(v):
    js = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt:format=duration,size", "-of", "json", str(v)]).stdout)
    vs = next(s for s in js["streams"] if s["codec_type"] == "video")
    a = next((s for s in js["streams"] if s["codec_type"] == "audio"), None)
    return {"w": vs["width"], "h": vs["height"], "vcodec": vs["codec_name"], "pix_fmt": vs.get("pix_fmt"),
            "acodec": a and a["codec_name"], "duration": float(js["format"]["duration"]), "bytes": int(js["format"]["size"])}

def ts(sec):
    sec = int(round(sec)); h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def chapters_from_job(job):
    """Merge consecutive scenes into chapters. Uses scene['chapter'] when templates set it, else the scene id."""
    out = []
    for s in job.get("scenes", []):
        name = s.get("chapter") or s.get("title") or s["id"].replace("s-", "").replace("-", " ").title()
        if out and out[-1]["title"] == name:
            continue
        out.append({"start": s["start"], "title": name})
    if out:
        out[0]["start"] = 0.0
    return out

def validate_chapters(ch, total):
    if len(ch) < 3:
        return False, f"{len(ch)} chapters (YouTube needs >= 3)"
    ends = [c["start"] for c in ch[1:]] + [total]
    short = [c["title"] for c, e in zip(ch, ends) if e - c["start"] < 10]
    if short:
        return False, f"chapters under 10 s: {', '.join(short[:4])}"
    return True, f"{len(ch)} chapters"

def merge_short(ch, total):
    """Fold chapters under 10 s into the previous one (the first absorbs the next) so mid-length videos keep valid chapters."""
    ch = [dict(c) for c in ch]
    i = 0
    while i < len(ch) and len(ch) > 1:
        end = ch[i + 1]["start"] if i + 1 < len(ch) else total
        if end - ch[i]["start"] < 10:
            if i == 0:
                del ch[1]  # first chapter absorbs the next; keeps its 0:00 title
            else:
                del ch[i]  # previous chapter absorbs this one
            continue
        i += 1
    if ch: ch[0]["start"] = 0.0
    return ch

def font_for(brand):
    if brand:
        root = Path(brand).parent
        f = ((json.loads(Path(brand).read_text()).get("fonts") or {}).get("heading") or {}).get("file")
        if f and (root / f).exists():
            return str(root / f)
    return sh(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"]).stdout or None

def thumbnail(video, at, text, out, brand=None, accent="#FFB020"):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    frame = out.with_suffix(".frame.png")
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", str(frame)])
    src = Image.open(frame).convert("RGB")
    W, H = 1280, 720
    if src.width / src.height < W / H:  # vertical/square source: blurred fill + centered frame
        bg = src.resize((W, int(W * src.height / src.width))).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(28))
        fg = src.resize((int(H * src.width / src.height), H))
        bg.paste(fg, ((W - fg.width) // 2, 0)); img = bg
    else:
        img = src.resize((W, H))
    if text:
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, int(H * 0.58), W, H], fill=(0, 0, 0, 150))
        fp = font_for(brand); size = 120
        while size > 40:
            fnt = ImageFont.truetype(fp, size) if fp else ImageFont.load_default()
            if d.textlength(text, font=fnt) <= W * 0.9: break
            size -= 6
        try: fnt.set_variation_by_axes([800])
        except Exception: pass
        tw = d.textlength(text, font=fnt)
        d.text(((W - tw) / 2, int(H * 0.64)), text, font=fnt, fill="white", stroke_width=3, stroke_fill="black")
        d.rectangle([(W - tw) / 2, int(H * 0.64) + size * 1.15, (W + tw) / 2, int(H * 0.64) + size * 1.15 + 10], fill=accent)
    img.save(out, "JPEG", quality=88, optimize=True)
    frame.unlink(missing_ok=True)
    return out

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--job"); ap.add_argument("--out", required=True)
    ap.add_argument("--title"); ap.add_argument("--summary", default=""); ap.add_argument("--tags", default="")
    ap.add_argument("--thumb-at", type=float); ap.add_argument("--thumb-text"); ap.add_argument("--brand")
    ap.add_argument("--srt"); ap.add_argument("--vtt"); ap.add_argument("--review", help="review dir from review.py check (must be approved)")
    ap.add_argument("--category", default="27", help="27 Education, 28 Science & Tech, 22 People & Blogs")
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--made-for-kids", default="no", choices=["yes", "no"]); ap.add_argument("--language", default="en")
    ap.add_argument("--links", default="", help="extra description lines, separated by |")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    video = Path(a.video); p = probe(video)
    job = json.loads(Path(a.job).read_text()) if a.job else {}
    gates = []
    def gate(ok, name, detail, level=None):
        gates.append({"level": level or ("PASS" if ok else "FAIL"), "gate": name, "detail": detail})
    # review gate
    if a.review and (Path(a.review) / "review.json").exists():
        rv = json.loads((Path(a.review) / "review.json").read_text())
        gate(rv.get("approved"), "review approved", f"approved by {rv.get('approved_by')}" if rv.get("approved") else "run review.py approve after the user OKs the preview")
    else:
        gate(False, "review approved", "no review dir; run review.py check + approve first")
    short = p["h"] > p["w"] and p["duration"] <= 180
    gate(p["vcodec"] == "h264" and p["pix_fmt"] == "yuv420p", "video codec", f"{p['vcodec']} {p['pix_fmt']} {p['w']}x{p['h']}")
    gate(p["acodec"] in ("aac", None), "audio codec", str(p["acodec"]), None if p["acodec"] else "WARN")
    gate(p["w"] >= p["h"] or short, "format", "Short (vertical, <= 3 min)" if short else ("16:9 upload" if p["w"] * 9 == p["h"] * 16 else f"{p['w']}x{p['h']} (letterboxed on YouTube)"),
         None if (p["w"] * 9 == p["h"] * 16 or short) else "WARN")
    title = (a.title or job.get("title") or job.get("template", video.stem).replace("-", " ").title()).strip()
    gate(len(title) <= 100, "title length", f"{len(title)} chars (max 100; keep the hook in the first ~60)")
    gate("<" not in title and ">" not in title, "title characters", "no angle brackets")
    # chapters
    ch, chap_note = [], ""
    if job.get("scenes") and not short:
        ch = chapters_from_job(job)
        ok, note = validate_chapters(ch, p["duration"])
        if not ok:
            ch2 = merge_short(ch, p["duration"]); ok2, note2 = validate_chapters(ch2, p["duration"])
            ch, chap_note = (ch2, f"merged short chapters: {note2}") if ok2 else ([], f"omitted ({note}); videos under ~30 s rarely qualify")
        else:
            chap_note = note
        gate(True, "chapters", chap_note, "PASS" if ch else "INFO")
    # disclosure: synthetic voice / generated media
    vo = (job.get("voiceover") or {}).get("provider")
    gen = bool(job.get("generated_media"))
    disclosure = {"ai_voice": bool(vo), "ai_voice_provider": vo, "generated_media": gen,
                  "altered_or_synthetic_toggle": "Consider YES if the voice or visuals could be mistaken for a real person or real event; "
                                                "a clearly synthetic narrator over motion graphics usually does not require it, but disclosing is the safe default."}
    # description
    credits = []
    cfile = video.parent / "credits.json"
    if cfile.exists():
        for c in json.loads(cfile.read_text()):
            line = c.get("attribution") or " ".join(x for x in [c.get("title"), "by " + c["author"] if c.get("author") else "", f"({c.get('license')})" if c.get("license") else "", c.get("url", "")] if x)
            if line.strip(): credits.append(line.strip())
    desc = [a.summary.strip()] if a.summary.strip() else []
    if ch:
        desc += ["", "Chapters:"] + [f"{ts(c['start'])} {c['title']}" for c in ch]
    if a.links:
        desc += [""] + [l.strip() for l in a.links.split("|") if l.strip()]
    if vo:
        desc += ["", "Narration is an AI-generated voice."]
    if credits:
        desc += ["", "Credits:"] + [f"- {c}" for c in credits]
    description = "\n".join(desc).strip() + "\n"
    gate(len(description) <= 5000, "description length", f"{len(description)} chars (max 5000)")
    gate("<" not in description and ">" not in description, "description characters", "no angle brackets (YouTube rejects them)")
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    tag_len = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)
    gate(tag_len <= 500, "tags", f"{len(tags)} tags, {tag_len}/500 chars")
    if short:
        gate("#shorts" in (title + description).lower() or True, "shorts", "vertical <= 3 min: YouTube files it under Shorts automatically; #Shorts in title/description is optional", "INFO")
    # thumbnail
    at = a.thumb_at if a.thumb_at is not None else min(p["duration"] * 0.3, 3.0)
    words = a.thumb_text if a.thumb_text is not None else " ".join(w.strip(".") for w in re.sub(r"[^\w\s'.]", "", title).split()[:4])
    brand_json = a.brand
    accent = "#FFB020"
    if brand_json:
        accent = (json.loads(Path(brand_json).read_text()).get("colors") or {}).get("accent", accent)
    thumb = thumbnail(video, at, words, out / "thumbnail.jpg", brand_json, accent)
    tb = thumb.stat().st_size
    gate(tb < 2_000_000, "thumbnail", f"1280x720 JPG, {tb/1e3:.0f} KB (max 2 MB), text: '{words}'")
    # captions
    for src, name in ((a.srt or video.with_suffix(".srt"), "captions.srt"), (a.vtt or video.with_suffix(".vtt"), "captions.vtt")):
        if src and Path(src).exists():
            shutil.copy(src, out / name)
    has_caps = (out / "captions.srt").exists()
    gate(has_caps or not vo, "captions file", "captions.srt ready to upload" if has_caps else ("no VO, none needed" if not vo else "VO but no SRT; run captions.py build"),
         None if has_caps or not vo else "WARN")
    meta = {"title": title, "description": description, "tags": tags, "categoryId": a.category, "privacyStatus": a.privacy,
            "madeForKids": a.made_for_kids == "yes", "defaultLanguage": a.language, "defaultAudioLanguage": a.language,
            "chapters": ch, "is_short": short, "disclosure": disclosure, "video_file": video.name,
            "duration_seconds": round(p["duration"], 2), "prepared_at": time.strftime("%Y-%m-%d %H:%M %Z"),
            "note": "Prepared for manual upload in YouTube Studio. This tool never uploads."}
    (out / "metadata.json").write_text(json.dumps(meta, indent=2))
    (out / "description.txt").write_text(description)
    ok = not any(g["level"] == "FAIL" for g in gates)
    md = [f"# YouTube upload checklist: {video.name}", "", f"Gates: **{'PASS' if ok else 'FAIL'}**", "", "| Result | Gate | Detail |", "|---|---|---|"]
    md += [f"| {g['level']} | {g['gate']} | {g['detail']} |" for g in gates]
    md += ["", "## Manual steps in YouTube Studio (nothing here uploads for you)", "",
           f"1. Upload `{video.name}` (sha256 in manifest.json). Start as **{a.privacy}**.",
           "2. Paste the title and `description.txt`; add tags from metadata.json.",
           "3. Upload `thumbnail.jpg` (needs a verified channel for custom thumbnails).",
           "4. Subtitles: upload `captions.srt` (language: " + a.language + ").",
           f"5. Audience: made for kids = **{a.made_for_kids}**.",
           "6. Altered or synthetic content: " + ("this video uses an AI voice. " if vo else "") + disclosure["altered_or_synthetic_toggle"],
           "7. Add end screen / cards in the last 5-20 s if the video is longer than 25 s.",
           "8. Watch the processed HD version once before switching to public."]
    (out / "upload-checklist.md").write_text("\n".join(md) + "\n")
    files = [video] + sorted(f for f in out.iterdir() if f.is_file() and f.name != "manifest.json")
    man = {"generated_at": meta["prepared_at"], "files": [{"file": str(f.name), "bytes": f.stat().st_size, "sha256": sha(f)} for f in files]}
    (out / "manifest.json").write_text(json.dumps(man, indent=2))
    for g in gates:
        print(f"  {g['level']:4} {g['gate']}: {g['detail']}")
    print(f"youtube prep -> {out} ({'PASS' if ok else 'FAIL'}; not uploaded)")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
