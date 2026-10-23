import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in, attach_vo  # noqa: E402

def media(c):
    return [q["avatar"] for q in c["quotes"] if q.get("avatar")]

def plan(c, ctx):
    sc = []
    if c.get("headline"): sc.append({"id": "s-open", "seconds": 2.6})
    for k, q in enumerate(c["quotes"]):
        n = len(q["text"].split())
        sc.append({"id": f"s-q{k}", "seconds": max(4.0, 1.6 + n / 2.6 + 1.6)})
    sc.append({"id": "s-end", "seconds": 3.6})
    return attach_vo(sc, c)

def initials(name):
    return "".join(p[0] for p in name.split()[:2]).upper()

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    stars = "★" * int(c.get("rating", 0) or 0)
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        if sid == "s-open":
            h = stage((f'<div class="stars">{"".join(f"<span>{x}</span>" for x in stars)}</div>' if stars else "")
                      + f'<div class="h1 oh">{W(c["headline"])}</div>')
            js += [f'tl.fromTo("#{sid} .stars span", {{scale: 0, rotation: -40}}, {{scale: 1, rotation: 0, duration: 0.45, stagger: 0.08, ease: "back.out(2)"}}, {t(st + 0.1)});',
                   words_in(f"#{sid} .oh", st + 0.45, 0.1), f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.05}});']
        elif sid.startswith("s-q"):
            q = c["quotes"][int(sid[3:])]
            av = (f'<img class="av" src="{ctx["media"](q["avatar"])}" alt="">' if q.get("avatar")
                  else f'<div class="av avi">{E(initials(q["name"]))}</div>')
            h = stage(f'<div class="qm">&ldquo;</div><div class="h2 qt">{W(q["text"])}</div>'
                      f'<div class="who">{av}<div class="wt"><div class="wn">{E(q["name"])}</div><div class="wr">{E(q.get("role", ""))}</div></div></div>')
            n = len(q["text"].split()); rd = min(0.22, (d - 2.6) / max(1, n))
            js += [f'enter("#{sid} .qm", {t(st + 0.05)}, "pop", {{duration: 0.6}});',
                   f'tl.fromTo("#{sid} .qt .w", {{opacity: 0.08, y: "1.2vmin"}}, {{opacity: 1, y: 0, duration: 0.35, stagger: {rd:.3f}, ease: "power2.out"}}, {t(st + 0.35)});',
                   f'enter("#{sid} .who", {t(st + 0.6 + n * rd)}, "rise", {{duration: 0.6}});',
                   f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.035, y: "-0.8vmin"}});',
                   f'tl.fromTo("#{sid} .qm", {{rotation: -4}}, {{rotation: 4, duration: {t(d)}, ease: "sine.inOut"}}, {t(st)});']
        else:
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"))
            js += j
        js += cut_js(s, i, scenes, ctx, "fade")
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    css = f"""
.stars {{ font-size: calc(var(--h2) * .9); color: var(--accent); letter-spacing: .25em; }}
.stars span {{ display: inline-block; }}
.qm {{ font-family: var(--font-heading); font-size: calc(var(--h1) * 2.6); line-height: .6; color: var(--primary); height: calc(var(--h1) * 1.2); }}
.qt {{ max-width: {"100%" if ctx["vertical"] else "86%"}; font-weight: 600; line-height: 1.22; }}
.who {{ display: flex; align-items: center; gap: 2.2vmin; margin-top: 2vmin; text-align: left; }}
.av {{ width: 9vmin; height: 9vmin; border-radius: 50%; object-fit: cover; border: .4vmin solid var(--primary); }}
.avi {{ display: grid; place-items: center; background: linear-gradient(135deg, var(--primary), var(--secondary)); font-family: var(--font-heading); font-weight: 700; font-size: 3.4vmin; color: var(--bg); }}
.wn {{ font-family: var(--font-heading); font-weight: 700; font-size: var(--body); }}
.wr {{ font-size: calc(var(--kicker) * 1.05); color: var(--muted); }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
