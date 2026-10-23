"""Shared Python helpers for Reelsmith HyperFrames templates (HTML strings + GSAP calls on RS.*)."""
import json

def J(v):
    return json.dumps(v)

def stage(inner, cls=""):
    return f'<div class="stage {cls}">{inner}</div>'

def t(x):
    return f"{x:.3f}"

def cut_js(s, i, scenes, ctx, exit_kind="blur", wipe=True):
    """Exit at the end of a scene + a brand wipe across the cut. In loop mode the last scene also exits so the
    final frame matches the (empty) first frame."""
    sid, end = s["id"], s["start"] + s["dur"]
    last = i == len(scenes) - 1
    js = []
    if not last or ctx.get("loop"):
        js.append(f'exit("#{sid} .stage", {t(end - 0.34)}, "{exit_kind}", {{duration: 0.32}});')
        if not last and wipe:
            js.append(f"wipe({t(end)});")
    return js

def endcard(ctx, s, cta, url, kicker=None):
    sid = s["id"]
    html = stage(
        f'<div class="ec-logo" style="width:{"62%" if ctx["vertical"] else "34%"}">{ctx["logo"]}</div>'
        + (f'<div class="kicker ec-k">{ctx["esc"](kicker)}</div>' if kicker else "")
        + (f'<div class="cta ec-cta">{ctx["esc"](cta)}</div>' if cta else "")
        + (f'<div class="url ec-url">{ctx["esc"](url)}</div>' if url else ""))
    st = s["start"]
    js = [f'enter("#{sid} .ec-logo", {t(st + 0.1)}, "pop", {{duration: 0.7}});',
          f'enter("#{sid} .ec-k", {t(st + 0.45)}, "rise");',
          f'enter("#{sid} .ec-cta", {t(st + 0.6)}, "pop");',
          f'enter("#{sid} .ec-url", {t(st + 0.85)}, "fade");',
          f'drift("#{sid} .stage", {t(st)}, {t(s["dur"])}, {{to: 1.04}});',
          f'tl.fromTo("#{sid} .ec-cta", {{boxShadow: "0 0 0 0vmin var(--primary)"}}, {{boxShadow: "0 0 0 2.2vmin rgba(0,0,0,0)", duration: 1.2, repeat: {max(0, int((s["dur"] - 1.6) / 1.2) - 1)}, ease: "power1.out"}}, {t(st + 1.3)});']
    return html, js

def words_in(sel, start, stagger=0.07, kind="rise", dur=0.5):
    return f'tl.fromTo("{sel} .w", {{y: "4vmin", opacity: 0}}, {{y: 0, opacity: 1, duration: {dur}, stagger: {stagger}, ease: "back.out(1.6)"}}, {t(start)});' if kind == "rise" else \
           f'tl.fromTo("{sel} .w", {{scale: 1.6, opacity: 0}}, {{scale: 1, opacity: 1, duration: {dur}, stagger: {stagger}, ease: "power4.out"}}, {t(start)});'

def rollnum(value, spins=1):
    """Slot-machine number markup for RS.roll: '1,250+' -> digit strips + static punctuation."""
    out = []
    for ch in str(value):
        if ch.isdigit():
            d = int(ch); steps = spins * 10 + d
            cells = "".join(f"<span>{k % 10}</span>" for k in range(steps + 1))
            out.append(f'<span class="rs-digit"><span class="rs-strip" data-to="{d}" data-spins="{spins}">{cells}</span></span>')
        else:
            out.append(f"<span>{ch}</span>")
    return f'<span class="rs-num">{"".join(out)}</span>'

def attach_vo(scenes, content):
    vo = content.get("vo") or {}
    for s in scenes:
        if vo.get(s["id"]) and not s.get("vo"):
            s["vo"] = vo[s["id"]]
    return scenes
