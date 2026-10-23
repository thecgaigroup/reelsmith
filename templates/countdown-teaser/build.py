import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in, attach_vo  # noqa: E402

def plan(c, ctx):
    sc = [{"id": f"s-t{k}", "seconds": 1.9} for k in range(len(c.get("tease", [])))]
    n = int(c.get("count_from", 5))
    sc += [{"id": f"s-n{v}", "seconds": 1.0, "min": 0.8} for v in range(n, 0, -1)]
    sc += [{"id": "s-reveal", "seconds": 3.4}, {"id": "s-end", "seconds": 3.2}]
    return attach_vo(sc, c)

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        nxt = scenes[i + 1]["id"] if i + 1 < len(scenes) else ""
        if sid.startswith("s-t"):
            line = c["tease"][int(sid[3:])]
            h = stage(f'<div class="h2 tz">{W(line)}</div>')
            js += [f'tl.fromTo("#{sid} .tz .w", {{opacity: 0, filter: "blur(10px)", letterSpacing: ".3em"}}, {{opacity: 1, filter: "blur(0px)", letterSpacing: "0em", duration: 0.6, stagger: 0.08, ease: "power3.out"}}, {t(st + 0.05)});',
                   f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.07}});']
        elif sid.startswith("s-n"):
            v = sid[3:]
            lab = c.get("count_label", "")
            if v == "1" and lab:  # "days to go" -> "day to go" (override with count_label_one)
                w0, _, rest = lab.partition(" ")
                lab = c.get("count_label_one") or ((w0[:-1] if w0.lower().endswith("s") and len(w0) > 2 else w0) + (" " + rest if rest else ""))
            h = stage(f'<div class="ring"></div><div class="num">{v}</div>'
                      + (f'<div class="kicker cl">{E(lab)}</div>' if lab else ""))
            js += [f'tl.fromTo("#{sid} .num", {{scale: 1.8, opacity: 0, filter: "blur(12px)"}}, {{scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.32, ease: "power4.out"}}, {t(st)});',
                   f'tl.to("#{sid} .num", {{scale: 0.9, duration: {t(d - 0.32)}, ease: "none"}}, {t(st + 0.32)});',
                   f'tl.fromTo("#{sid} .ring", {{scale: 0.6, opacity: 0.9}}, {{scale: 1.25, opacity: 0, duration: {t(d)}, ease: "power2.out"}}, {t(st)});',
                   f'tl.set("#{sid} .cl", {{opacity: 1}}, {t(st)});']
        elif sid == "s-reveal":
            h = stage(f'<div class="kicker">{E(c.get("kicker", ""))}</div><div class="h1 rv">{W(c["title"])}</div>'
                      f'<div class="bar"></div><div class="h2 dt">{E(c["date_text"])}</div>')
            js += [f'enter("#{sid} .kicker", {t(st + 0.05)}, "mask");', words_in(f"#{sid} .rv", st + 0.15, 0.1, "slam", 0.5),
                   f'tl.fromTo("#{sid} .bar", {{scaleX: 0}}, {{scaleX: 1, duration: 0.6, ease: "power4.inOut"}}, {t(st + 0.7)});',
                   f'enter("#{sid} .dt", {t(st + 0.95)}, "rise");', f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.06}});']
        else:
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"), c.get("title"))
            js += j
        if sid.startswith("s-n"):
            if not nxt.startswith("s-n"):
                js.append(f'exit("#{sid} .stage", {t(st + d - 0.25)}, "scale", {{duration: 0.24}});')
        else:
            js += cut_js(s, i, scenes, ctx, "blur", wipe=not nxt.startswith("s-n") and not sid.startswith("s-t"))
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    css = """
.num { font-family: var(--font-heading); font-weight: 700; font-size: calc(var(--h1) * 3.6); line-height: 1; color: var(--fg); font-variant-numeric: tabular-nums; }
.ring { position: absolute; left: 50%; top: 50%; width: 52vmin; height: 52vmin; margin: -26vmin 0 0 -26vmin; border-radius: 50%; border: .8vmin solid var(--primary); }
.cl { opacity: 0; color: var(--accent); }
.rv { font-size: calc(var(--h1) * 1.5); }
.bar { width: 30%; height: 1vmin; background: linear-gradient(90deg, var(--primary), var(--secondary)); border-radius: 1vmin; transform-origin: center; }
.dt { color: var(--muted); }
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
