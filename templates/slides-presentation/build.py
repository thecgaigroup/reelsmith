import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, words_in  # noqa: E402

XF = 0.667   # crossfade overlap (20 frames @ 30 fps)

def media(c):
    return [s["image"] for s in c["slides"] if s.get("image")]

def plan(c, ctx):
    mn = float(c.get("min_seconds", 5))
    out = []
    for k, s in enumerate(c["slides"]):
        sc = {"id": f"sl{k}", "seconds": max(mn, float(s.get("seconds", 6))), "min": mn, "kind": s.get("kind", "bullets"),
              "chapter": ctx["plain"](s.get("title") or s.get("quote") or f"Slide {k + 1}")[:60]}
        if s.get("vo"): sc["vo"] = s["vo"]
        out.append(sc)
    return out

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    v = ctx["vertical"]
    N = len(scenes); out, js = [], []
    total = ctx["total"]
    chrome = (f'<div class="hdr"><div class="hl">{ctx["logo"]}</div><div class="ht">{E(c["title"])}</div></div>')
    out.append({"id": "deck-chrome", "start": 0, "dur": total, "track": 7, "html": chrome})
    js.append('tl.fromTo("#deck-chrome .hdr", {opacity: 0, y: "-2vmin"}, {opacity: 1, y: 0, duration: 0.6}, 0.1);' if not ctx["loop"]
              else 'tl.set("#deck-chrome .hdr", {opacity: 1}, 0);')
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        sl = c["slides"][i]; kind = sl.get("kind", "bullets")
        last = i == N - 1
        dots = "".join(f'<span class="dot{" on" if k == i else ""}"></span>' for k in range(N))
        foot = f'<div class="ftr"><span class="fl">{E(c.get("footer", ""))}</span><span class="fn">{i + 1} of {N}</span><span class="dots">{dots}</span></div>'
        if kind in ("title", "section", "question"):
            q = '<div class="qbadge">Question</div>' if kind == "question" else ""
            body = (f'{q}<div class="h1 tt">{W(sl.get("title", ""))}</div>' +
                    (f'<div class="h2 st">{E(sl.get("subtitle", ""))}</div>' if sl.get("subtitle") else "") +
                    (f'<div class="kicker pr">{E(c.get("presenter", ""))}</div>' if kind == "title" and c.get("presenter") else ""))
            ent = [f'enter("#{sid} .qbadge", {t(st + 0.25)}, "pop");', words_in(f"#{sid} .tt", st + 0.35, 0.45 / max(1, len(sl.get("title", "").split()))),
                   f'enter("#{sid} .st", {t(st + 0.9)}, "rise");', f'enter("#{sid} .pr", {t(st + 1.3)}, "fade");']
        elif kind == "bullets":
            bl = "".join(f'<li class="body b b{k}"><span class="bd"></span>{W(x)}</li>' for k, x in enumerate(sl.get("bullets", [])))
            body = f'<div class="h2 bt">{W(sl.get("title", ""))}</div><ul class="bl">{bl}</ul>'
            ent = [f'enter("#{sid} .bt", {t(st + 0.3)}, "rise");'] + \
                  [f'tl.fromTo("#{sid} .b{k}", {{x: "-6vmin", opacity: 0}}, {{x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.3)"}}, {t(st + 0.8 + k * 0.45)});'
                   for k in range(len(sl.get("bullets", [])))]
        elif kind == "stat":
            body = (f'<div class="kicker">{E(sl.get("title", ""))}</div><div class="sv">{E(sl["value"])}</div><div class="h2 sl2">{E(sl.get("label", ""))}</div>'
                    + (f'<div class="note">{E(sl["note"])}</div>' if sl.get("note") else ""))
            ent = [f'enter("#{sid} .kicker", {t(st + 0.25)}, "mask");', f'enter("#{sid} .sv", {t(st + 0.4)}, "pop", {{duration: 0.7}});',
                   f'enter("#{sid} .sl2", {t(st + 0.9)}, "rise");', f'enter("#{sid} .note", {t(st + 1.3)}, "fade");']
        elif kind == "quote":
            body = f'<div class="qq">&ldquo;</div><div class="h2 qt">{W(sl["quote"])}</div><div class="body by">{E(sl.get("by", ""))}</div>'
            ent = [f'enter("#{sid} .qq", {t(st + 0.25)}, "pop");',
                   f'tl.fromTo("#{sid} .qt .w", {{opacity: 0.1}}, {{opacity: 1, duration: 0.3, stagger: 0.09}}, {t(st + 0.5)});',
                   f'enter("#{sid} .by", {t(st + 1.6)}, "rise");']
        else:  # image
            body = (f'<div class="h2 it">{W(sl.get("title", ""))}</div><div class="imgf"><img class="im" src="{ctx["media"](sl["image"])}" alt=""></div>')
            ent = [f'enter("#{sid} .it", {t(st + 0.3)}, "rise");', f'enter("#{sid} .imgf", {t(st + 0.5)}, "rise", {{duration: 0.7}});',
                   f'kenburns("#{sid} .im", {t(st)}, {t(d + XF)}, {i});']
        html = stage(f'<div class="slide-in">{body}</div>', "slidest") + foot
        dur = d + (0 if last else XF)
        if i == 0 and not ctx["loop"]:
            js.append(f'tl.set("#{sid}", {{opacity: 1}}, 0);')
        else:
            js.append(f'tl.fromTo("#{sid}", {{opacity: 0}}, {{opacity: 1, duration: {XF}, ease: "none"}}, {t(st)});')
        js += ent
        js.append(f'tl.fromTo("#{sid} .slide-in", {{scale: 1}}, {{scale: 1.015, duration: {t(dur)}, ease: "none"}}, {t(st)});')
        if last and ctx["loop"]:
            js.append(f'tl.to("#{sid}", {{opacity: 0, duration: {XF}, ease: "none"}}, {t(st + d - XF)});')
        out.append({"id": sid, "start": st, "dur": dur, "html": html, "track": 1 + i % 2})
    css = f"""
.hdr {{ position: absolute; left: var(--safe-l); right: var(--safe-r); top: calc(var(--safe-t) * .45); display: flex; align-items: center; gap: 1.6vmin; opacity: 0; }}
.hl {{ height: 3.6vmin; }} .hl img, .hl svg {{ height: 100%; width: auto; }}
.ht {{ font-family: var(--font-heading); font-weight: 700; font-size: 2.2vmin; color: var(--muted); letter-spacing: .04em; }}
.slidest {{ top: calc(var(--safe-t) + 4vmin); bottom: calc(var(--safe-b) + 3vmin); }}
.slide-in {{ display: flex; flex-direction: column; align-items: center; gap: 2.6vmin; width: 100%; }}
.ftr {{ position: absolute; left: var(--safe-l); right: var(--safe-r); bottom: calc(var(--safe-b) * .5); display: flex; align-items: center; gap: 2vmin; font-size: 1.9vmin; color: var(--muted); }}
.fl {{ flex: 1; }} .fn {{ font-variant-numeric: tabular-nums; }}
.dots {{ display: flex; gap: .8vmin; }} .dot {{ width: 1vmin; height: 1vmin; border-radius: 50%; background: rgba(255,255,255,.22); }} .dot.on {{ background: var(--primary); width: 3vmin; border-radius: 1vmin; }}
.qbadge {{ background: var(--accent); color: #111; font-family: var(--font-heading); font-weight: 700; padding: .8vmin 2.2vmin; border-radius: 99px; font-size: var(--kicker); letter-spacing: .1em; text-transform: uppercase; }}
.tt {{ font-size: calc(var(--h1) * 1.15); }}
.st {{ color: var(--muted); font-weight: 500; max-width: 80%; }}
.bt {{ align-self: {"center" if v else "flex-start"}; }}
.bl {{ list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 2.2vmin; align-self: {"center" if v else "flex-start"}; text-align: left; }}
.b {{ display: flex; align-items: center; gap: 2vmin; font-size: calc(var(--body) * 1.15); }}
.bd {{ width: 1.6vmin; height: 1.6vmin; border-radius: .4vmin; background: linear-gradient(135deg, var(--primary), var(--secondary)); flex: none; }}
.sv {{ font-family: var(--font-heading); font-weight: 700; font-size: calc(var(--h1) * 2.6); line-height: 1; color: var(--secondary); }}
.note {{ font-size: calc(var(--kicker) * .85); color: var(--muted); }}
.qq {{ font-family: var(--font-heading); font-size: calc(var(--h1) * 2.2); line-height: .5; height: calc(var(--h1) * 1); color: var(--primary); }}
.qt {{ max-width: 86%; }}
.by {{ color: var(--muted); }}
.imgf {{ width: {"100%" if v else "70%"}; aspect-ratio: 16 / 9; border-radius: 2vmin; overflow: hidden; box-shadow: 0 3vmin 6vmin rgba(0,0,0,.45); }}
.im {{ width: 100%; height: 100%; object-fit: cover; }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
