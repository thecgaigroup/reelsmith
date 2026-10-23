import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in, rollnum, attach_vo  # noqa: E402

def media(c):
    return [p["src"] for p in c["photos"]]

def plan(c, ctx):
    sc = [{"id": "s-title", "seconds": 3.0}] + [{"id": f"s-p{k}", "seconds": 2.4} for k in range(1, len(c["photos"]))]
    if c.get("stats"): sc.append({"id": "s-stats", "seconds": 3.4})
    sc.append({"id": "s-end", "seconds": 3.4})
    return attach_vo(sc, c)

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        if sid == "s-title":
            p = c["photos"][0]
            h = (f'<div class="media"><img class="ph" src="{ctx["media"](p["src"])}" alt=""></div><div class="shade"></div>'
                 + stage(f'<div class="kicker">{E(" · ".join(x for x in [c.get("date"), c.get("location")] if x))}</div>'
                         f'<div class="h1 ev">{W(c["event"])}</div><div class="chip rc">Recap</div>'))
            js += [f'kenburns("#{sid} .ph", {t(st)}, {t(d)}, 0);', f'enter("#{sid} .kicker", {t(st + 0.1)}, "mask");',
                   words_in(f"#{sid} .ev", st + 0.3, 0.1, "slam", 0.45), f'enter("#{sid} .rc", {t(st + 0.9)}, "pop");']
        elif sid.startswith("s-p"):
            k = int(sid[3:]); p = c["photos"][k]
            h = (f'<div class="media"><img class="ph" src="{ctx["media"](p["src"])}" alt=""></div><div class="shade sh2"></div>'
                 + stage(f'<div class="h2 pc">{W(p.get("caption", ""))}</div>', "pst"))
            js += [f'kenburns("#{sid} .ph", {t(st)}, {t(d)}, {k});', words_in(f"#{sid} .pc", st + 0.25, 0.07)]
        elif sid == "s-stats":
            cells = "".join(f'<div class="stc st{k}"><div class="h1 sn">{rollnum(x["value"])}</div><div class="body sl">{E(x["label"])}</div></div>'
                            for k, x in enumerate(c["stats"]))
            h = stage(f'<div class="kicker">{E(c["event"])} in numbers</div><div class="stats">{cells}</div>')
            js += [f'enter("#{sid} .kicker", {t(st + 0.05)}, "mask");']
            for k in range(len(c["stats"])):
                js += [f'enter("#{sid} .st{k}", {t(st + 0.15 + k * 0.25)}, "rise");', f'roll("#{sid} .st{k}", {t(st + 0.2 + k * 0.25)}, 1.6);']
            js.append(f'drift("#{sid} .stats", {t(st)}, {t(d)}, {{to: 1.04}});')
        else:
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"), c["event"])
            js += j
        js += cut_js(s, i, scenes, ctx, "fade", wipe=not (i + 1 < len(scenes) and scenes[i + 1]["id"].startswith("s-p")))
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    v = ctx["vertical"]
    css = f"""
.ev {{ font-size: calc(var(--h1) * 1.3); text-shadow: 0 .5vmin 3vmin rgba(0,0,0,.5); }}
.pst {{ justify-content: flex-end; }}
.pc {{ text-shadow: 0 .4vmin 2.4vmin rgba(0,0,0,.7); }}
.stats {{ display: flex; flex-direction: {"column" if v else "row"}; gap: {"3vmin" if v else "7vmin"}; justify-content: center; }}
.stc {{ display: flex; flex-direction: column; align-items: center; gap: .6vmin; }}
.sn {{ font-size: calc(var(--h1) * {1.25 if v else 1.7}); color: var(--fg); }}
.rc {{ font-size: var(--kicker); font-weight: 600; letter-spacing: .14em; text-transform: uppercase; }}
.sl {{ color: var(--muted); text-transform: uppercase; letter-spacing: .12em; font-size: var(--kicker); }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
