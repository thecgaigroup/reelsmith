#!/usr/bin/env python3
"""Lint a video script before anything is rendered or voiced.

  script_lint.py script.json [--wps 2.5] [--preset tiktok] [--json]

script.json: {"title": "...", "aspect": "9:16", "wps": 2.5,
              "scenes": [{"id": "hook", "duration": 3, "vo": "...", "on_screen": "..."}, ...]}
Plain text also works, one scene per line:   3 | on-screen text | voiceover text

Checks: VO fits each scene at the speaking rate, on-screen text is short enough to read,
the first 3 seconds hook, the last scene has a CTA, long sentences, total vs platform max.
Exit code 1 when anything FAILs.
"""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEAK_OPENERS = ["hi ", "hey ", "hello", "welcome", "in this video", "today we", "today i", "so,", "um", "let me introduce",
                "my name is", "we are excited", "we're excited", "have you ever wondered"]
CTA_VERBS = ["try", "start", "get", "join", "book", "download", "visit", "shop", "sign up", "signup", "learn", "register",
             "follow", "subscribe", "save", "order", "claim", "watch", "discover", "explore", "request", "contact", "apply",
             "reserve", "buy", "grab", "see", "link in bio", "tap"]
LINE_CHARS = {"16:9": 42, "9:16": 26, "1:1": 32, "4:5": 30}

def words(t):
    return re.findall(r"[A-Za-z0-9'’%$€£.-]+", t or "")

def parse(path):
    txt = Path(path).read_text()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        scenes = []
        for i, line in enumerate(l for l in txt.splitlines() if l.strip() and not l.startswith("#")):
            parts = [p.strip() for p in line.split("|")]
            d = float(re.sub(r"[^0-9.]", "", parts[0]) or 3)
            scenes.append({"id": f"s{i + 1}", "duration": d, "on_screen": parts[1] if len(parts) > 1 else "", "vo": parts[2] if len(parts) > 2 else ""})
        return {"scenes": scenes}

def lint(doc, wps=None, preset=None):
    wps = wps or doc.get("wps") or 2.5
    aspect = doc.get("aspect", "16:9")
    scenes = doc["scenes"]
    rows, t = [], 0.0
    def add(level, sid, msg):
        rows.append({"level": level, "scene": sid, "msg": msg})
    for i, s in enumerate(scenes):
        sid, d = s.get("id", f"s{i + 1}"), float(s.get("duration", 0))
        vo, ons = s.get("vo", ""), s.get("on_screen", "")
        nw = len(words(vo))
        if nw:
            need = nw / wps + 0.3  # breath + tail
            if need > d:
                add("FAIL", sid, f"VO {nw} words needs ~{need:.1f}s at {wps} wps, scene is {d:.1f}s. Cut ~{int((need - d) * wps) + 1} words or lengthen.")
            elif need > 0.9 * d:
                add("WARN", sid, f"VO is tight: {need:.1f}s of {d:.1f}s.")
        if ons:
            ow = len(words(ons))
            read = ow / 3.0 + 0.5  # comfortable on-screen reading: ~3 words/s + settle time
            if read > d:
                add("FAIL", sid, f"on-screen text ({ow} words) needs ~{read:.1f}s to read; scene is {d:.1f}s.")
            longest = max((len(l) for l in ons.split("\n")), default=0)
            lim = LINE_CHARS.get(aspect, 42)
            if longest > lim * 2:
                add("WARN", sid, f"on-screen line is {longest} chars; at {aspect} keep <= {lim}/line, 2 lines.")
            if ow > 9:
                add("WARN", sid, f"on-screen text has {ow} words; headlines read best at 3-7.")
        for sent in re.split(r"(?<=[.!?])\s+", vo):
            if len(words(sent)) > 20:
                add("WARN", sid, f"long sentence ({len(words(sent))} words); split it for VO and captions.")
        if re.search(r"\b(two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|percent)\b", ons, re.I):
            add("INFO", sid, "on-screen text spells out a number; digits read faster (3x, 40%).")
        t += d
    if scenes:
        first = scenes[0]
        hook_text = (first.get("vo") or first.get("on_screen") or "").strip().lower()
        if float(first.get("duration", 0)) > 3.5:
            add("WARN", first.get("id", "s1"), "first scene is longer than 3.5s; land the hook inside 3 seconds.")
        if any(hook_text.startswith(w) for w in WEAK_OPENERS):
            add("FAIL", first.get("id", "s1"), "weak opener (greeting/preamble). Open on the payoff, a bold claim, a question or a visual surprise.")
        if len(words(first.get("vo", ""))) > 9:
            add("WARN", first.get("id", "s1"), "hook VO over 9 words; aim for one punchy line.")
        last = scenes[-1]
        lt = f"{last.get('vo', '')} {last.get('on_screen', '')}".lower()
        if not any(re.search(rf"\b{re.escape(v)}\b", lt) for v in CTA_VERBS):
            add("FAIL", last.get("id", "end"), "no call to action in the last scene (Try / Start / Book / Visit ... + where).")
    if preset:
        presets = json.loads((HERE / "presets.json").read_text())["presets"]
        p = presets.get(preset)
        if p and t > p["max_seconds"]:
            add("FAIL", "-", f"total {t:.1f}s exceeds {preset} max {p['max_seconds']}s.")
        elif p and p.get("recommended_seconds") and t > p["recommended_seconds"][1]:
            add("WARN", "-", f"total {t:.1f}s is above the usual {preset} sweet spot {p['recommended_seconds']}.")
    return {"total_seconds": round(t, 2), "wps": wps, "rows": rows, "pass": not any(r["level"] == "FAIL" for r in rows)}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("--wps", type=float); ap.add_argument("--preset"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = lint(parse(a.script), a.wps, a.preset)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"total {res['total_seconds']}s at {res['wps']} wps")
        for r in res["rows"]:
            print(f"  {r['level']:4}  [{r['scene']}] {r['msg']}")
        print("RESULT:", "PASS" if res["pass"] else "FAIL")
    sys.exit(0 if res["pass"] else 1)

if __name__ == "__main__":
    main()
