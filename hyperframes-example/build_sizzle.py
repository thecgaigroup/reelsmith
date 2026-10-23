"""Build the test sizzle index.html for a given resolution (16:9 / 9:16) from the plan + VO manifest."""
import json, sys, os, subprocess
proj, W, H, res = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
with_vo = os.path.isdir(os.path.join(proj, "assets/vo"))
BPM = 120; BEAT = 60 / BPM
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode())
man = json.load(open(os.path.join(proj,"assets/vo/manifest.json"))) if with_vo else {"scenes":[]}
plan = [  # (id, beats, vo_index or None, html)
 ("s1", 4, 0, '<div class="big">Your story,<br><span class="acc">told faster.</span></div>'),
 ("s2", 4, 1, '<div class="big">Every frame,<br><span class="acc">on brand.</span></div>'),
 ("s3", 4, None, '<div class="slam"><span class="w">Kinetic.</span> <span class="w">Type.</span> <span class="w acc">Motion.</span></div>'),
 ("s4", 6, None, '<div class="big small"><span class="ar">16:9</span> <span class="ar">9:16</span> <span class="ar">1:1</span></div><div class="sub">One source, every aspect.</div>'),
 ("s5", 7, None, '<div class="logo"><div class="mark"></div><div class="brand" id="brand"></div></div><div class="sub" id="cta"></div>'),
]
import math
t = 0; scenes = []
for sid, beats, vi, html in plan:
    vo = None
    if vi is not None and with_vo:
        f = f"assets/vo/scene-0{vi+1}.mp3"; d = dur(os.path.join(proj, f))
        beats = max(beats, math.ceil((d + 0.4) / BEAT)); vo = (f, d, man["scenes"][vi]["captions"])
    L = beats * BEAT; scenes.append((sid, t, L, vo, html)); t += L
TOTAL = t
clips, audio, caps, tw = [], [], [], []
for i,(sid, st, L, vo, html) in enumerate(scenes):
    clips.append(f'<section id="{sid}" class="clip scene" data-start="{st:g}" data-duration="{L:g}" data-track-index="1">{html}</section>')
    if vo:
        f, d, cap = vo
        audio.append(f'<audio id="vo{i}" class="clip" data-start="{st:g}" data-duration="{d:.3f}" data-track-index="3" data-volume="1" src="{f}"></audio>')
        words = "".join(f'<span class="cw" id="{sid}w{j}">{c["text"]}</span> ' for j,c in enumerate(cap))
        caps.append(f'<div id="{sid}cap" class="clip caption" data-start="{st:g}" data-duration="{L:g}" data-track-index="2">{words}</div>')
        for j,c in enumerate(cap):
            tw.append(f'tl.to("#{sid}w{j}", {{color:"#ffd166", opacity:1, duration:0.08, overwrite:"auto"}}, {st + c["startMs"]/1000:.3f});')
    # scene in/out
    tw.append(f'tl.from("#{sid} > *", {{y:"6vmin", opacity:0, duration:{BEAT*0.6:.2f}, stagger:{BEAT/4:.3f}, ease:"power3.out"}}, {st:.3f});')
    if i < len(scenes)-1:
        tw.append(f'tl.to("#{sid} > *", {{opacity:0, scale:1.06, duration:{BEAT*0.4:.2f}, ease:"power2.in"}}, {st+L-BEAT*0.4:.3f});')
# beat-synced slams in s3 and aspect chips in s4
s3 = scenes[2]; s4 = scenes[3]; s5 = scenes[4]
tw.append(f'tl.from("#s3 .w", {{scale:2.2, opacity:0, duration:0.18, stagger:{BEAT}, ease:"back.out(2)"}}, {s3[1]:.3f});')
tw.append(f'tl.from("#s4 .ar", {{yPercent:120, opacity:0, duration:0.25, stagger:{BEAT}, ease:"power4.out"}}, {s4[1]:.3f});')
tw.append(f'tl.from("#s5 .mark", {{rotation:-180, scale:0, duration:{BEAT*2}, ease:"back.out(1.6)"}}, {s5[1]:.3f});')
tw.append(f'tl.from("#brand", {{x:"-8vmin", scale:0.8, opacity:0, duration:{BEAT*2}, ease:"power3.out"}}, {s5[1]+BEAT:.3f});')
tw.append(f'tl.to("#bg", {{backgroundPosition:"100% 50%", duration:{TOTAL:g}, ease:"none"}}, 0);')
html = f'''<!doctype html>
<html lang="en" data-resolution="{res}" data-composition-variables='[{{"id":"brand","type":"string","label":"Brand","default":"Reelsmith"}},{{"id":"cta","type":"string","label":"Call to action","default":"Make it move."}},{{"id":"accent","type":"color","label":"Accent","default":"#ffd166"}}]'>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="assets/gsap.min.js"></script>
<style>
:root {{ --ink:#fff; --acc:#ffd166; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#0b0f1a; }}
#root {{ width:100%; height:100%; position:relative; font-family:"DejaVu Sans", Arial, sans-serif; color:var(--ink); }}
#bg {{ position:absolute; inset:0; background:linear-gradient(120deg,#0b0f1a,#1b2a4a,#3a1c5c,#0b0f1a); background-size:300% 300%; background-position:0% 50%; }}
.scene {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 8vmin; gap:3vmin; }}
.big {{ font-size:{11 if W>H else 13}vmin; font-weight:800; line-height:1.05; letter-spacing:-0.02em; }}
.big.small {{ font-size:{12 if W>H else 14}vmin; }}
.acc {{ color:var(--acc); }}
.slam {{ font-size:{13 if W>H else 12}vmin; font-weight:900; }}
.slam .w, .ar {{ display:inline-block; }}
.ar {{ margin:0 2vmin; border:0.6vmin solid var(--acc); border-radius:2vmin; padding:0 3vmin; }}
.sub {{ font-size:5vmin; opacity:.85; }}
.logo {{ display:flex; align-items:center; gap:4vmin; }}
.mark {{ width:14vmin; height:14vmin; border-radius:3vmin; background:conic-gradient(var(--acc),#ef476f,#118ab2,var(--acc)); }}
.brand {{ font-size:12vmin; font-weight:900; }}
.caption {{ position:absolute; left:8vmin; right:8vmin; bottom:{14 if W>H else 16}%; text-align:center; font-size:{4.5 if W>H else 5.5}vmin; font-weight:700; }}
.cw {{ opacity:.45; color:#fff; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:g}" data-width="{W}" data-height="{H}">
<div id="bg" class="clip" data-start="0" data-duration="{TOTAL:g}" data-track-index="0"></div>
{chr(10).join(clips)}
{chr(10).join(caps)}
<audio id="music" class="clip" data-start="0" data-duration="{TOTAL:g}" data-track-index="4" data-volume="0.45" data-fade-in="0.5" data-fade-out="1.5" src="assets/music/bed-120bpm.mp3"></audio>
{chr(10).join(audio)}
</div>
<script>
const v = window.__hyperframes.getVariables();
document.getElementById("brand").textContent = v.brand;
document.getElementById("cta").textContent = v.cta;
document.documentElement.style.setProperty("--acc", v.accent);
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tw)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>'''
open(os.path.join(proj,"index.html"),"w").write(html)
print("total", TOTAL, [(s[0], s[1], s[2]) for s in scenes])
