import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from kit import stage, t, cut_js, endcard, words_in
from safe_zones import SafeZones

def media(c):
    return [c.get("hero")] if c.get("hero") else []

def plan(c, ctx):
    10|    """Plan scenes for Signal Short: title reveal + 2-3 key points + end card."""
    vo = c.get("vo") or {}
    sc = [
        {"id": "s-title", "seconds": 3.0},
        {"id": "s-key1", "seconds": 2.5},
        {"id": "s-key2", "seconds": 2.5},
    ]
    if c.get("key3"):
        sc.append({"id": "s-key3", "seconds": 2.5})
    sc.append({"id": "s-end", "seconds": 3.0})
    
    20|    for s in sc:
        if vo.get(s["id"]):
            s["vo"] = vo[s["id"]]
    return sc

def build(c, ctx, scenes):
    E, W = ctx["esc"], ctx["words"]
    out, js = [], []
    
    # Safe layout flag from context
    safe_layout = ctx.get("safe_layout", False)
    
    30|    # Initialize safe zones if enabled
    if safe_layout and ctx["vertical"]:
        zones = SafeZones(1080, 1920, enabled=True)
        badge_x, badge_y = zones.get_badge_position()
        # Pill: right-align to end at x=770 (safe zone right edge)
        # With right margin of 310px, available right edge is 1080-310=770
        pill_right_margin = 310  # px from right edge
    else:
        # Legacy positions (top corners, no safe margins)
        badge_x, badge_y = 40, 40
        pill_right_margin = 40  # px from right edge (legacy)
    
    # Brand elements that appear on every scene
    40|    badge_html = f'<div class="badge" style="left: {badge_x}px; top: {badge_y if safe_layout and ctx["vertical"] else 40}px;"><img src="{ctx.get("badge_url", "")}" alt="badge" style="width: 80px; height: 80px;"></div>' if ctx.get("badge_url") else ""
    pill_html = f'<div class="pill" style="right: {pill_right_margin}px; top: {badge_y if safe_layout and ctx["vertical"] else 40}px;">{E(c.get("pill_text", "THE SIGNAL"))}</div>'
    
    for i, s in enumerate(scenes):
        sid, st, d = s["id"], s["start"], s["dur"]
        
        if sid == "s-title":
            # Hero art background + title reveal with center line
            hero_bg = f'<div class="media"><img class="hero" src="{ctx["media"](c["hero"])}" alt=""></div><div class="shade"></div>' if c.get("hero") else ""
    50|            
            # Center line with keyword highlights (cyan/purple)
            title_parts = c["title"].split()
            title_html = " ".join(f'<span class="w kw{(i % 2) + 1}">{E(w)}</span>' for i, w in enumerate(title_parts))
            
            h = (hero_bg + badge_html + pill_html +
                 stage(f'<div class="centerline"><div class="h1 title">{title_html}</div>'
                       f'<div class="bar"></div></div>'))
            
            # Animation: hold for 6 frames (0.25s at 24fps) then animate
            hold_time = 0.25
    60|            js += [
                f'tl.set("#{sid} .badge, #{sid} .pill", {{opacity: 1}}, {t(st)});',
                f'tl.fromTo("#{sid} .bar", {{scaleX: 0}}, {{scaleX: 1, duration: 0.8, ease: "power4.inOut"}}, {t(st + hold_time)});',
                words_in(f"#{sid} .title", st + hold_time + 0.3, 0.12, "rise", 0.5),
            ]
            if c.get("hero"):
                js.append(f'kenburns("#{sid} .hero", {t(st)}, {t(d)}, 1);')
        
        elif sid.startswith("s-key"):
            # Key point with hero background
            key_num = int(sid[-1]) - 1
    70|            key_text = c.get(f"key{key_num + 1}", "")
            
            hero_bg = f'<div class="media"><img class="hero" src="{ctx["media"](c["hero"])}" alt=""></div><div class="shade sh2"></div>' if c.get("hero") else ""
            
            h = (hero_bg + badge_html + pill_html +
                 stage(f'<div class="h2 keypoint">{W(key_text)}</div>'))
            
            js += [
                f'tl.set("#{sid} .badge, #{sid} .pill", {{opacity: 1}}, {t(st)});',
                words_in(f"#{sid} .keypoint", st + 0.1, 0.08),
    80|            ]
            if c.get("hero"):
                js.append(f'kenburns("#{sid} .hero", {t(st)}, {t(d)}, {key_num});')
        
        else:  # s-end
            h, j = endcard(ctx, s, c.get("cta"), c.get("url"), c.get("title"))
            js += j
        
        js += cut_js(s, i, scenes, ctx)
        out.append({"id": sid, "start": st, "dur": d, "html": h})
    
    90|    # Constrain content width in safe layout mode
    safe_width_pct = "60%" if safe_layout and ctx["vertical"] else "100%"
    
    css = f"""
.badge {{ position: absolute; z-index: 100; opacity: 0; }}
.pill {{ position: absolute; background: linear-gradient(90deg, var(--primary), var(--secondary)); color: #111; 
        font-family: var(--font-heading); font-weight: 700; padding: 1.2vmin 2.8vmin; border-radius: 99px; 
        font-size: var(--kicker); letter-spacing: .1em; text-transform: uppercase; opacity: 0; z-index: 100; white-space: nowrap; }}
.centerline {{ display: flex; flex-direction: column; align-items: center; gap: 2vmin; text-align: center; max-width: {safe_width_pct}; margin: 0 auto; }}
.bar {{ width: 50%; height: 1.2vmin; background: #FFFFFF; border-radius: 1vmin; transform-origin: center; }}
.title {{ font-size: calc(var(--h1) * 1.2); line-height: 1.1; word-wrap: break-word; }}
.kw1 {{ color: #22D3EE; }}
.kw2 {{ color: #A78BFA; }}
   100|.keypoint {{ font-size: calc(var(--h2) * 1.1); text-align: center; max-width: {safe_width_pct}; margin: 0 auto; word-wrap: break-word; }}
.sh2 {{ background: rgba(0,0,0,0.65); }}
"""
    return {"scenes": out, "js": "\n".join(js), "css": css}
