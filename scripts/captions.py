#!/usr/bin/env python3
"""Captions from word timings: SRT + VTT sidecars, ASS for burn-in, and ffmpeg burn.

  captions.py build --words words.json -o out/captions [--profile netflix|bbc|social] [--aspect 9:16]
                    [--style clean|boxed|karaoke|pop] [--brand brand.json] [--offset 0]
        -> out/captions.srt, .vtt, .ass
  captions.py estimate --text "Spoken line." --start 1.2 --end 4.0 >> words.json   # no timings? spread by syllables
  captions.py burn video.mp4 captions.ass -o out.mp4 [--fontsdir brand/fonts]

words.json: [{"text": "Hello", "start": 0.12, "end": 0.40}, ...] in seconds. Also accepts Remotion/@remotion/captions
{"text","startMs","endMs"} and hyperframes transcript.json ({"words": [...]}) shapes.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PROFILES = {
    # Netflix Timed Text Style Guide (general): 42 chars/line, 2 lines, 20 cps adult, 5/6 s min, 7 s max.
    "netflix": {"chars": 42, "lines": 2, "cps": 20, "min": 5 / 6, "max": 7.0, "gap": 2 / 24},
    # BBC Subtitle Guidelines: ~160-180 wpm, 37 chars for broadcast; online ~68% width.
    "bbc": {"chars": 37, "lines": 2, "cps": 17, "min": 1.0, "max": 7.0, "gap": 0.08},
    # Burned-in social captions: short chunks that track speech; 1-2 short lines.
    "social": {"chars": 24, "lines": 2, "cps": 22, "min": 0.6, "max": 3.0, "gap": 0.0},
}

def load_words(path, offset=0.0):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("words") or data.get("segments") or data.get("captions") or []
    out = []
    for w in data:
        if "startMs" in w:
            s, e = w["startMs"] / 1000, w["endMs"] / 1000
        else:
            s, e = float(w.get("start", 0)), float(w.get("end", 0))
        t = (w.get("text") or w.get("word") or "").strip()
        if t:
            out.append({"text": t, "start": s + offset, "end": max(e, s + 0.05) + offset})
    return out

def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    return max(1, len(re.findall(r"[aeiouy]+", w)) - (1 if w.endswith("e") and len(w) > 3 else 0))

def estimate(text, start, end):
    ws = text.split()
    weights = [syllables(w) + (0.6 if re.search(r"[,.;:!?]$", w) else 0) for w in ws]
    total, t, out = sum(weights), start, []
    for w, wt in zip(ws, weights):
        d = (end - start) * wt / total
        out.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.92, 3)})
        t += d
    return out

def wrap(text, chars, lines):
    if len(text) <= chars:
        return [text]
    # balanced 2-line split at the space nearest the middle, bottom line slightly longer
    best = None
    for m in re.finditer(" ", text):
        a, b = text[:m.start()], text[m.end():]
        if len(a) <= chars and len(b) <= chars:
            score = abs(len(a) - len(b)) + (0 if len(b) >= len(a) else 2)
            best = min(best or (9e9, None), (score, [a, b]))
    return best[1] if best else [text[:chars], text[chars:]]

def build_cues(words, prof):
    P = PROFILES[prof]
    cues, cur = [], []
    def flush():
        if cur:
            text = " ".join(w["text"] for w in cur)
            cues.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": text, "words": list(cur)})
            cur.clear()
    for i, w in enumerate(words):
        cand = " ".join(x["text"] for x in cur + [w])
        dur = w["end"] - (cur[0]["start"] if cur else w["start"])
        too_long = len(cand) > P["chars"] * P["lines"] or dur > P["max"]
        if cur and (too_long or (w["start"] - cur[-1]["end"] > 0.6)):
            flush()
        cur.append(w)
        if re.search(r"[.!?]$", w["text"]) or (prof == "social" and re.search(r"[,;:]$", w["text"]) and len(cand) > 10):
            flush()
    flush()
    # timing rules: min duration, reading speed, gaps, no overlaps
    for i, c in enumerate(cues):
        need = max(P["min"], len(c["text"]) / P["cps"])
        nxt = cues[i + 1]["start"] - P["gap"] if i + 1 < len(cues) else c["end"] + need
        c["end"] = round(min(max(c["end"], c["start"] + need), max(nxt, c["end"])), 3)
        c["lines"] = wrap(c["text"], P["chars"], P["lines"])
    return cues

def ts(t, sep=","):
    t = max(0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    s = t % 60
    return f"{h:02}:{m:02}:{int(s):02}{sep}{int(round((s - int(s)) * 1000)) % 1000:03}"

def to_srt(cues):
    return "\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n" + "\n".join(c["lines"]) + "\n" for i, c in enumerate(cues, 1))

def to_vtt(cues):
    return "WEBVTT\n\n" + "\n".join(f"{ts(c['start'], '.')} --> {ts(c['end'], '.')} line:85%\n" + "\n".join(c["lines"]) + "\n" for c in cues)

def ass_color(hexc, alpha=0):
    h = hexc.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()

def to_ass(cues, aspect, style, brand=None):
    W, H = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}[aspect]
    c = (brand or {}).get("colors", {})
    fg, accent, box = c.get("fg", "#FFFFFF"), c.get("accent") or c.get("primary", "#FFD400"), c.get("surface") or c.get("bg", "#000000")
    font = ((brand or {}).get("fonts", {}).get("heading") or {}).get("family", "Inter")
    size = int(min(W, H) * (0.058 if aspect != "16:9" else 0.05))
    # vertical: sit above the bottom ~35% that Reels/TikTok/Shorts UI covers
    margin_v = int(H * (0.36 if aspect in ("9:16",) else 0.12 if aspect == "4:5" else 0.08))
    border, outline, shadow, back = (3, 18, 0, ass_color(box, 0x30)) if style == "boxed" else (1, max(3, size // 14), 2, "&H80000000")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{ass_color(fg)},{ass_color(accent)},{ass_color(box) if style == 'boxed' else '&H00101010'},{back},-1,0,0,0,100,100,0,0,{border},{outline},{shadow},2,{int(W*0.08)},{int(W*0.08)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def a(t):
        return ts(t, ".")[:-1]  # ASS uses centiseconds
    ev = []
    for cue in cues:
        if style == "karaoke":
            # word-by-word highlight: \k durations in centiseconds, SecondaryColour = upcoming, Primary = sung
            parts, prev = [], cue["start"]
            for w in cue["words"]:
                k = int(round((w["end"] - prev) * 100)); prev = w["end"]
                parts.append(f"{{\\kf{max(1, k)}}}{w['text']}")
            text = " ".join(parts)
            text = f"{{\\1c{ass_color(accent)}\\2c{ass_color(fg)}}}" + text
        elif style == "pop":
            text = "{\\fscx80\\fscy80\\t(0,120,\\fscx100\\fscy100)}" + "\\N".join(cue["lines"])
        else:
            text = "\\N".join(cue["lines"])
        ev.append(f"Dialogue: 0,{a(cue['start'])},{a(cue['end'])},Default,,0,0,0,,{text}")
    return head + "\n".join(ev) + "\n"

def burn(video, ass, out, fontsdir=None):
    esc = str(Path(ass).resolve()).replace(":", r"\:").replace("'", r"\'")
    vf = f"subtitles='{esc}'" + (f":fontsdir='{Path(fontsdir).resolve()}'" if fontsdir else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", vf, "-c:v", "libx264", "-crf", "18",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-map_metadata", "-1", str(out)], check=True)
    print(f"burned {ass} -> {out}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("build"); p.add_argument("--words", required=True); p.add_argument("-o", "--out", required=True)
    p.add_argument("--profile", default=None, choices=list(PROFILES)); p.add_argument("--aspect", default="16:9")
    p.add_argument("--style", default="clean", choices=["clean", "boxed", "karaoke", "pop"]); p.add_argument("--brand"); p.add_argument("--offset", type=float, default=0)
    p = sp.add_parser("estimate"); p.add_argument("--text", required=True); p.add_argument("--start", type=float, required=True); p.add_argument("--end", type=float, required=True)
    p = sp.add_parser("burn"); p.add_argument("video"); p.add_argument("ass"); p.add_argument("-o", "--out", required=True); p.add_argument("--fontsdir")
    a = ap.parse_args()
    if a.cmd == "estimate":
        print(json.dumps(estimate(a.text, a.start, a.end), indent=1)); return
    if a.cmd == "burn":
        burn(a.video, a.ass, a.out, a.fontsdir); return
    words = load_words(a.words, a.offset)
    prof = a.profile or ("social" if a.aspect in ("9:16", "1:1", "4:5") else "netflix")
    sidecar = build_cues(words, "netflix" if prof == "social" else prof)  # sidecars follow broadcast rules
    burned = build_cues(words, prof)
    brand = json.loads(Path(a.brand).read_text()) if a.brand else None
    base = Path(a.out); base.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{base}.srt").write_text(to_srt(sidecar))
    Path(f"{base}.vtt").write_text(to_vtt(sidecar))
    Path(f"{base}.ass").write_text(to_ass(burned, a.aspect, a.style, brand))
    cps = max((len(c["text"]) / max(0.01, c["end"] - c["start"]) for c in sidecar), default=0)
    print(f"{len(sidecar)} sidecar cues (max {cps:.1f} cps), {len(burned)} burn-in cues ({prof}, {a.style}) -> {base}.srt/.vtt/.ass")

if __name__ == "__main__":
    main()
