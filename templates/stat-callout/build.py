import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in, rollnum, attach_vo  # noqa: E402

def plan(c, ctx):
    sc = [{"id": "s-intro", "seconds": 3.0}] + [{"id": f"s-s{k}", "seconds": 3.4} for k in range(len(c["stats"]))]
    if c.get("chart"): sc.append({"id": "s-chart", "seconds": 2.6 + 0.4 * len(c["chart"]["bars"])})
    sc.append({"id": "s-end", "seconds": 3.4})
    return attach_vo(sc, c)

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    src = f'<div class="src">{E(c["source"])}</div>'
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        if sid == "s-intro":
            h = stage(f'<div class="kicker">{E(c.get("kicker", ""))}</div><div class="h1 ti">{W(c["title"])}</div>')
            js += [f'enter("#{sid} .kicker", {t(st + 0.05)}, "mask");', words_in(f"#{sid} .ti", st + 0.2, 0.1),
                   f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.05}});']
        elif sid.startswith("s-s"):
            x = c["stats"][int(sid[3:])]
            h = stage(f'<div class="big"><span class="px">{E(x.get("prefix", ""))}</span>{rollnum(x["value"])}<span class="sx">{E(x.get("suffix", ""))}</span></div>'
                      f'<div class="h2 lb">{E(x["label"])}</div>{src}')
            js += [f'enter("#{sid} .big", {t(st)}, "pop", {{duration: 0.5}});', f'roll("#{sid} .big", {t(st + 0.1)}, 1.5, 0.08);',
                   f'enter("#{sid} .sx", {t(st + 1.3)}, "pop");', f'enter("#{sid} .lb", {t(st + 0.7)}, "rise");', f'enter("#{sid} .src", {t(st + 1.0)}, "fade");',
                   f'drift("#{sid} .stage", {t(st)}, {t(d)}, {{to: 1.04}});']
        elif sid == "s-chart":
            ch = c["chart"]; mx = max(b["value"] for b in ch["bars"]) or 1; hi = ch.get("highlight")
            bars = "".join(f'<div class="bc"><div class="bv">{b["value"]}{E(ch.get("unit", ""))}</div><div class="bt"><div class="bf{" hi" if k == hi else ""}" style="height:{100 * b["value"] / mx:.1f}%"></div></div>'
                           f'<div class="bl">{E(b["label"])}</div></div>' for k, b in enumerate(ch["bars"]))
            h = stage(f'<div class="h2 ct">{E(ch.get("title", ""))}</div><div class="chart">{bars}</div>{src}')
            js += [f'enter("#{sid} .ct", {t(st + 0.05)}, "rise");',
                   f'tl.fromTo("#{sid} .bf", {{scaleY: 0}}, {{scaleY: 1, duration: 0.8, stagger: 0.18, ease: "power3.out"}}, {t(st + 0.3)});',
                   f'tl.fromTo("#{sid} .bv", {{opacity: 0, y: "2vmin"}}, {{opacity: 1, y: 0, duration: 0.4, stagger: 0.18}}, {t(st + 0.7)});',
                   f'enter("#{sid} .src", {t(st + 1.0)}, "fade");', f'drift("#{sid} .chart", {t(st)}, {t(d)}, {{to: 1.03}});']
            if hi is not None:
                js.append(f'tl.fromTo("#{sid} .hi", {{filter: "brightness(1)"}}, {{filter: "brightness(1.35)", duration: 0.6, repeat: 3, yoyo: true}}, {t(st + 1.3)});')
        else:
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"))
            js += j
        js += cut_js(s, i, scenes, ctx)
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    v = ctx["vertical"]
    css = f"""
.big {{ display: inline-flex; align-items: baseline; font-family: var(--font-heading); font-weight: 700; font-size: calc(var(--h1) * 2.6); line-height: 1; color: var(--primary); }}
.big .rs-num {{ color: var(--fg); }}
.sx, .px {{ color: var(--accent); }}
.lb {{ max-width: {"100%" if v else "70%"}; }}
.src {{ font-size: calc(var(--kicker) * .85); color: var(--muted); margin-top: 1.4vmin; }}
.chart {{ display: flex; align-items: flex-end; gap: {"3vmin" if v else "4vmin"}; height: {"42vh" if v else "46vh"}; width: {"100%" if v else "70%"}; }}
.bc {{ flex: 1; height: 100%; display: flex; flex-direction: column; align-items: center; gap: 1vmin; }}
.bt {{ flex: 1; width: 100%; display: flex; align-items: flex-end; }}
.bf {{ width: 100%; background: var(--surface); border: .3vmin solid var(--muted); border-radius: 1.4vmin 1.4vmin .4vmin .4vmin; transform-origin: bottom; }}
.bf.hi {{ background: linear-gradient(180deg, var(--secondary), var(--primary)); border-color: transparent; }}
.bv {{ font-family: var(--font-heading); font-weight: 700; font-size: var(--body); }}
.bl {{ font-size: var(--kicker); color: var(--muted); }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
