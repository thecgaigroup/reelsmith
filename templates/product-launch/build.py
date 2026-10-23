import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in  # noqa: E402

def media(c):
    return [c["image"]] if c.get("image") else []

def plan(c, ctx):
    vo = c.get("vo") or {}
    sc = [{"id": "s-name", "seconds": 2.6}, {"id": "s-head", "seconds": 2.8},
          {"id": "s-feat", "seconds": 1.6 + 1.2 * len(c["features"])}]
    if c.get("image"): sc.append({"id": "s-hero", "seconds": 3.2})
    if c.get("stat"): sc.append({"id": "s-stat", "seconds": 2.8})
    sc.append({"id": "s-end", "seconds": 3.6})
    for s in sc:
        if vo.get(s["id"]): s["vo"] = vo[s["id"]]
    return sc

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        if sid == "s-name":
            h = stage(f'<div class="kicker k">{E(c.get("kicker", ""))}</div><div class="h1 name">{W(c["product"])}</div>'
                      f'<div class="bar"></div>')
            js += [f'enter("#{sid} .k", {t(st + 0.05)}, "mask", {{duration: 0.5}});', words_in(f"#{sid} .name", st + 0.2, 0.09, "slam", 0.45),
                   f'tl.fromTo("#{sid} .bar", {{scaleX: 0}}, {{scaleX: 1, duration: 0.7, ease: "power4.inOut"}}, {t(st + 0.6)});',
                   f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.06}});']
        elif sid == "s-head":
            h = stage(f'<div class="h1 head">{W(c["headline"])}</div>')
            js += [words_in(f"#{sid} .head", st + 0.08, 0.12), f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.05, y: "-1vmin"}});']
        elif sid == "s-feat":
            cards = "".join(f'<div class="card f f{k}"><div class="fi">{k + 1:02d}</div><div class="h2 ft">{E(f["title"])}</div>'
                            f'<div class="body fb">{E(f.get("body", ""))}</div></div>' for k, f in enumerate(c["features"]))
            h = stage(f'<div class="feats">{cards}</div>')
            for k in range(len(c["features"])):
                js.append(f'enter("#{sid} .f{k}", {t(st + 0.15 + k * 0.9)}, "{"left" if not ctx["vertical"] else "right"}", {{duration: 0.6, ease: "back.out(1.4)"}});')
                js.append(f'tl.fromTo("#{sid} .f{k} .fi", {{color: "var(--muted)"}}, {{color: "var(--accent)", duration: 0.3}}, {t(st + 0.5 + k * 0.9)});')
            js.append(f'drift("#{sid} .feats", {t(st)}, {t(d)}, {{to: 1.03}});')
        elif sid == "s-hero":
            src = ctx["media"](c["image"])
            h = (f'<div class="media"><img class="hero" src="{src}" alt=""></div><div class="shade"></div>'
                 + stage(f'<div class="h2 cap">{W(c.get("image_caption", ""))}</div>', "hero-st"))
            js += [f'kenburns("#{sid} .hero", {t(st)}, {t(d)}, 1);', words_in(f"#{sid} .cap", st + 0.35, 0.06)]
        elif sid == "s-stat":
            h = stage(f'<div class="h1 sv">{E(c["stat"]["value"])}</div><div class="h2 sl">{E(c["stat"]["label"])}</div>'
                      + (f'<div class="fn">{E(c.get("footnote", ""))}</div>' if c.get("footnote") else ""))
            js += [f'enter("#{sid} .sv", {t(st + 0.05)}, "slam", {{duration: 0.5}});', f'enter("#{sid} .sl", {t(st + 0.4)}, "rise");',
                   f'enter("#{sid} .fn", {t(st + 0.8)}, "fade");',
                   f'tl.fromTo("#{sid} .sv", {{scale: 1}}, {{scale: 1.08, duration: {t(d - 0.6)}, ease: "none"}}, {t(st + 0.55)});']
        else:
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"), c.get("product"))
            js += j
        js += cut_js(s, i, scenes, ctx)
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    v = ctx["vertical"]
    css = f"""
.bar {{ width: {"50%" if v else "28%"}; height: 1vmin; background: linear-gradient(90deg, var(--primary), var(--secondary)); border-radius: 1vmin; transform-origin: left; }}
.feats {{ display: flex; flex-direction: {"column" if v or ctx["square"] else "row"}; gap: {"1.8vmin" if v else "2.6vmin"}; width: 100%; align-items: stretch; }}
.feats .card {{ flex: 1; text-align: left; display: flex; flex-direction: column; gap: 1vmin; padding: {"2vmin 3.2vmin" if v else "2.6vmin 3.4vmin" if ctx["square"] else "3.4vmin"}; }}
.fi {{ font-family: var(--font-heading); font-weight: 700; font-size: var(--kicker); letter-spacing: .1em; }}
.feats .ft {{ font-size: calc(var(--h2) * {0.62 if ctx["square"] else 0.72}); }}
.feats .fb {{ font-size: calc(var(--body) * {0.82 if ctx["square"] else 0.9}); }}
.hero-st {{ justify-content: flex-end; }}
.cap {{ text-shadow: 0 .4vmin 2vmin rgba(0,0,0,.6); }}
.name {{ font-size: calc(var(--h1) * 1.45); }}
.head {{ font-size: calc(var(--h1) * 1.15); }}
.sv {{ font-size: calc(var(--h1) * 2.4); background: linear-gradient(90deg, var(--primary), var(--secondary)); -webkit-background-clip: text; background-clip: text; color: transparent; line-height: 1; }}
.fn {{ font-size: calc(var(--kicker) * .8); color: var(--muted); }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
