import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in, J  # noqa: E402

BASE = {"intro": 3.5, "step": 5.0, "three": 5.5, "compare": 5.5, "checklist": 5.0, "outro": 4.0}


def _aspect(sec, ctx):
    """Frame aspect = the screenshot's own aspect, so focus/callout fractions land on the right pixels."""
    if sec.get("image_aspect"):
        return float(sec["image_aspect"])
    try:
        from PIL import Image
        with Image.open(ctx["media_abs"](sec["image"])) as im:
            return max(0.5, min(2.4, im.width / im.height))
    except Exception:
        return 1.6

def media(c):
    return [s["image"] for s in c["sections"] if s.get("image")]

def plan(c, ctx):
    out, n = [], 0
    for k, s in enumerate(c["sections"]):
        kind = s.get("kind", "step")
        if kind == "step": n += 1
        sc = {"id": f"s{k}-{kind}", "seconds": float(s.get("seconds", BASE.get(kind, 5))), "kind": kind,
              "chapter": (f"Step {n}: " if kind == "step" else "") + ctx["plain"](s.get("title", kind.title()))}
        if s.get("vo"): sc["vo"] = s["vo"]
        out.append(sc)
    return out

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    v, sq = ctx["vertical"], ctx["square"]
    out, js, n = [], [], 0
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        sec = c["sections"][i]; kind = sec.get("kind", "step")
        if kind == "intro":
            h = stage(f'<div class="kicker">How-to</div><div class="h1 it">{W(sec.get("title", c["title"]))}</div>'
                      + (f'<div class="body sub">{E(c.get("subtitle", ""))}</div>' if c.get("subtitle") else ""))
            js += [f'enter("#{sid} .kicker", {t(st + 0.05)}, "mask");', words_in(f"#{sid} .it", st + 0.2, 0.09),
                   f'enter("#{sid} .sub", {t(st + 0.9)}, "fade");', f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.04}});']
        elif kind == "step":
            n += 1
            f = sec.get("focus") or {}; z = float(f.get("zoom", 1.5)); fx, fy = f.get("x", 0.5), f.get("y", 0.5)
            co = sec.get("callout")
            mark = (f'<div class="co{" co-l" if co["x"] > 0.65 else ""}" style="left:{co["x"] * 100:.1f}%;top:{co["y"] * 100:.1f}%"><div class="co-ring"></div>'
                    f'<div class="co-t">{E(co.get("text", ""))}</div></div>') if co else ""
            ar = _aspect(sec, ctx)
            mh = 48 if ctx["vertical"] else 62
            fwid = "100%" if ctx["vertical"] or ctx["square"] else "78%"
            frame = (f'<div class="frame" style="aspect-ratio:{ar:.4f};width:min({fwid},{mh * ar:.1f}vh)"><div class="cam"><img src="{ctx["media"](sec["image"])}" alt="">{mark}</div></div>'
                     if sec.get("image") else "")
            h = stage(f'<div class="sh"><div class="chip sn">Step {n}</div><div class="h2 stt">{E(sec.get("title", ""))}</div></div>'
                      f'{frame}' + ("" if ctx.get("burn_captions") else f'<div class="body sb">{E(sec.get("body", ""))}</div>'), "stepst")  # burned captions replace the body line
            keys = [{"t": 0, "zoom": 1, "x": .5, "y": .5}, {"t": 0.6, "zoom": 1, "x": .5, "y": .5},
                    {"t": 1.8, "zoom": z, "x": fx, "y": fy}, {"t": max(2.0, d - 0.4), "zoom": z * 1.04, "x": fx, "y": fy}]
            js += [f'enter("#{sid} .sh", {t(st + 0.05)}, "left");', f'enter("#{sid} .frame", {t(st + 0.15)}, "rise", {{duration: 0.6}});',
                   f'camera("#{sid} .cam", {t(st)}, {J(keys)});'] + ([] if ctx.get("burn_captions") else [f'enter("#{sid} .sb", {t(st + 0.8)}, "fade");'])
            if co:
                js += [f'tl.fromTo("#{sid} .co", {{scale: 0, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2)"}}, {t(st + 2.0)});',
                       f'tl.fromTo("#{sid} .co-ring", {{boxShadow: "0 0 0 0 rgba(255,176,32,.7)"}}, {{boxShadow: "0 0 0 2.4vmin rgba(255,176,32,0)", duration: 1, repeat: {max(0, int(d - 3))}, ease: "power1.out"}}, {t(st + 2.3)});']
        elif kind == "three":
            pts = "".join(f'<div class="card p p{k}"><div class="pn">{k + 1}</div><div class="body">{E(p)}</div></div>' for k, p in enumerate(sec["points"][:3]))
            h = stage(f'<div class="h2">{E(sec.get("title", ""))}</div><div class="pts">{pts}</div>')
            js += [f'enter("#{sid} .h2", {t(st + 0.05)}, "rise");'] + [f'enter("#{sid} .p{k}", {t(st + 0.5 + k * 0.5)}, "pop");' for k in range(3)] + \
                  [f'drift("#{sid} .pts", {t(st)}, {t(d)}, {{to: 1.03}});']
        elif kind == "compare":
            def col(x, cls):
                return (f'<div class="card cmp {cls}"><div class="kicker">{E(x["label"])}</div>'
                        + "".join(f'<div class="body ci">{"✕" if cls == "l" else "✓"} {E(p)}</div>' for p in x["points"]) + "</div>")
            h = stage(f'<div class="h2">{E(sec.get("title", ""))}</div><div class="cmpw">{col(sec["left"], "l")}<div class="vs">vs</div>{col(sec["right"], "r")}</div>')
            js += [f'enter("#{sid} .h2", {t(st + 0.05)}, "rise");', f'enter("#{sid} .cmp.l", {t(st + 0.4)}, "left");',
                   f'enter("#{sid} .vs", {t(st + 0.8)}, "pop");', f'enter("#{sid} .cmp.r", {t(st + 1.1)}, "right");',
                   f'tl.fromTo("#{sid} .cmp.l", {{opacity: 1}}, {{opacity: 0.55, duration: 0.5}}, {t(st + 1.8)});',
                   f'drift("#{sid} .cmpw", {t(st)}, {t(d)}, {{to: 1.03}});']
        elif kind == "checklist":
            items = "".join(f'<div class="body ck ck{k}"><span class="box"><span class="tick">✓</span></span>{E(x)}</div>' for k, x in enumerate(sec["items"]))
            h = stage(f'<div class="h2">{E(sec.get("title", ""))}</div><div class="cks">{items}</div>')
            gap = max(0.35, (d - 1.5) / max(1, len(sec["items"])))
            js += [f'enter("#{sid} .h2", {t(st + 0.05)}, "rise");']
            for k in range(len(sec["items"])):
                js += [f'enter("#{sid} .ck{k}", {t(st + 0.4 + k * gap)}, "left");',
                       f'tl.fromTo("#{sid} .ck{k} .tick", {{scale: 0}}, {{scale: 1, duration: 0.3, ease: "back.out(3)"}}, {t(st + 0.7 + k * gap)});']
        else:
            h, j = endcard(ctx, s, sec.get("cta"), sec.get("url"), sec.get("title"))
            js += j
        js += cut_js(s, i, scenes, ctx, "blur")
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    fw = "100%" if v or sq else "78%"
    css = f"""
.stepst {{ gap: 2.2vmin; justify-content: {"center" if v else "flex-start"}; }}
.sh {{ display: flex; align-items: center; gap: 2vmin; align-self: {"center" if v else "flex-start"}; }}
.frame {{ width: {fw}; aspect-ratio: 16 / 10; border-radius: 2vmin; overflow: hidden; box-shadow: 0 3vmin 6vmin rgba(0,0,0,.45); border: .3vmin solid rgba(255,255,255,.12); background: #fff; flex: 0 0 auto; }}
.cam {{ position: relative; width: 100%; height: 100%; transform-origin: 50% 50%; }}
.cam img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.co {{ position: absolute; transform-origin: 0 0; }}
.co-ring {{ position: absolute; left: -2.2vmin; top: -2.2vmin; width: 4.4vmin; height: 4.4vmin; border-radius: 50%; border: .5vmin solid var(--accent); }}
.co-l .co-t {{ left: auto; right: 3vmin; }}
.co-t {{ position: absolute; left: 3vmin; top: -2vmin; white-space: nowrap; background: var(--accent); color: #111; font-family: var(--font-heading); font-weight: 700; font-size: 2.2vmin; padding: .5vmin 1.4vmin; border-radius: 1vmin; }}
.sb {{ color: var(--muted); }}
.pts {{ display: flex; flex-direction: {"column" if v else "row"}; gap: 2.4vmin; width: 100%; }}
.p {{ flex: 1; display: flex; flex-direction: column; gap: 1vmin; align-items: flex-start; text-align: left; }}
.pn {{ font-family: var(--font-heading); font-weight: 700; font-size: var(--h2); color: var(--accent); }}
.cmpw {{ display: flex; flex-direction: {"column" if v else "row"}; gap: 2.4vmin; align-items: center; width: 100%; }}
.cmp {{ flex: 1; width: 100%; text-align: left; display: flex; flex-direction: column; gap: 1.2vmin; }}
.cmp.r {{ border-color: var(--secondary); }}
.vs {{ font-family: var(--font-heading); font-weight: 700; font-size: var(--h2); color: var(--accent); }}
.cks {{ display: flex; flex-direction: column; gap: 1.6vmin; align-items: flex-start; }}
.ck {{ display: flex; align-items: center; gap: 1.6vmin; }}
.box {{ width: 4vmin; height: 4vmin; border-radius: 1vmin; border: .4vmin solid var(--muted); display: grid; place-items: center; }}
.tick {{ color: var(--secondary); font-weight: 700; }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
