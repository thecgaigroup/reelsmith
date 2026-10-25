#!/usr/bin/env python3
"""Reelsmith: render a parameterized template (text + media + brand.json) into one or more aspects.

  reelsmith.py list
  reelsmith.py sample TEMPLATE                      # print the template's sample content JSON
  reelsmith.py render --template product-launch --content c.json [--brand brand.json]
                      [--aspect 16x9,9x16,1x1] --out DIR [--music track.mp3|synth|none]
                      [--vo auto|none|kokoro|espeak|elevenlabs|openai] [--allow-paid] [--draft]
                      [--captions auto|burn|sidecar|none] [--loop] [--dry-run] [--quality looks]

Pipeline (one spec drives everything; the resolved spec is saved as DIR/job.json):
  brand bundle -> capabilities -> content contract check -> script lint (warn) -> pronunciation dictionary ->
  per-scene voiceover (free/local by default, cached by text hash so visual iterations never re-voice) ->
  music (user track | synth bed) trimmed to first downbeat -> scene timing = max(template length, VO + 0.5 s)
  snapped to the music grid -> one premixed audio bed (VO normalised, music ducked under VO, two-pass loudnorm)
  -> HyperFrames HTML per aspect -> lint -> render -> captions (SRT/VTT sidecars, optional burn-in) -> job.json.

Paid voice (ElevenLabs/OpenAI) is used only when named with --vo AND --allow-paid AND the key exists;
otherwise a quote is printed and the free path runs. Keys are never printed.
"""
import argparse, hashlib, html, importlib.util, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
TPL = PKG / "templates"
sys.path.insert(0, str(HERE))
import brand as brandlib  # noqa: E402
import beats as beatlib  # noqa: E402
import captions as caplib  # noqa: E402

ASPECTS = {
    # safe = fraction of the frame kept clear of platform UI (top, bottom, left, right)
    "16x9": {"W": 1920, "H": 1080, "safe": (0.075, 0.09, 0.065, 0.065), "h1": 8.8, "h2": 6.2, "body": 3.5, "kicker": 2.4, "ratio": "16:9"},
    "9x16": {"W": 1080, "H": 1920, "safe": (0.13, 0.32, 0.08, 0.11), "h1": 10.5, "h2": 7.6, "body": 4.6, "kicker": 3.3, "ratio": "9:16"},
    "1x1":  {"W": 1080, "H": 1080, "safe": (0.08, 0.09, 0.08, 0.08), "h1": 8.6, "h2": 6.4, "body": 4.0, "kicker": 2.8, "ratio": "1:1"},
}
ENERGY = {"calm": (96, "calm", "bar"), "medium": (112, "bright", "bar"), "high": (124, "bright", "half")}
HF = os.environ.get("REELSMITH_HF", "npx --yes hyperframes@0.8.197").split()
CACHE = Path(os.environ.get("REELSMITH_CACHE", Path.home() / ".cache" / "reelsmith"))

# ---------------------------------------------------------------- utils
def sh(cmd, **kw):
    kw.setdefault("check", True)
    return subprocess.run(cmd, **kw)

def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)

def esc(t):
    return html.escape(str(t or ""), quote=True)

def words_html(text, cls="w"):
    """'Ship *faster* today' -> per-word spans; *word* gets the accent colour (emphasis words)."""
    out = []
    for tok in str(text or "").split():
        acc = tok.startswith("*") and tok.rstrip(".,!?:;").endswith("*")
        clean = tok.replace("*", "")
        out.append(f'<span class="{cls}{" acc" if acc else ""}">{esc(clean)}</span>')
    return " ".join(out)

def plain(text):
    return str(text or "").replace("*", "")

def load_template(name):
    d = TPL / name
    spec = importlib.util.spec_from_file_location(f"tpl_{name.replace('-', '_')}", d / "build.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    meta = json.loads((d / "template.json").read_text())
    return m, meta, d

def templates():
    return sorted(p.name for p in TPL.iterdir() if (p / "template.json").exists())

# ---------------------------------------------------------------- contract (budgets are per template)
def _collect(obj, parts):
    """Resolve a dotted budget path; lists are walked item-by-item ('item' = the list element itself)."""
    if not parts:
        return [obj]
    if isinstance(obj, list):
        return [n for x in obj for n in _collect(x, parts)]
    if parts[0] == "item":
        return _collect(obj, parts[1:])
    if isinstance(obj, dict) and parts[0] in obj:
        return _collect(obj[parts[0]], parts[1:])
    return []

def contract(content, meta):
    """Content contract (borrowed idea: manifest validation before render). Errors stop the render; warnings don't."""
    errs, warns = [], []
    for k in meta.get("required", []):
        if not content.get(k):
            errs.append(f"missing required field '{k}'")
    for path, lim in meta.get("budgets", {}).items():
        nodes = _collect(content, path.split("."))
        if isinstance(lim, dict):
            for n in nodes:
                if not isinstance(n, list):
                    continue
                if "max_items" in lim and len(n) > lim["max_items"]:
                    errs.append(f"{path}: {len(n)} items > {lim['max_items']}")
                if "min_items" in lim and len(n) < lim["min_items"]:
                    errs.append(f"{path}: {len(n)} items < {lim['min_items']}")
            continue
        for v in [x for n in nodes for x in (n if isinstance(n, list) else [n])]:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                v = str(v)
            if isinstance(v, str) and len(plain(v)) > lim:
                warns.append(f"{path}: '{plain(v)[:40]}...' is {len(plain(v))} chars (budget {lim}); it may wrap or shrink")
    return errs, warns

# ---------------------------------------------------------------- pronunciation (applied to TTS text only)
BUILTIN_SAY = {"GIF": "jif", "SQL": "sequel", "SaaS": "sass", "GUI": "gooey", "JSON": "jason", "nginx": "engine x",
               "macOS": "mac oh ess", "iOS": "eye oh ess", "UI": "you eye", "UX": "you ex", "e.g.": "for example",
               "i.e.": "that is", "vs.": "versus", "&": "and", "%": " percent"}
KEEP_ACRONYMS = {"AI", "OK", "US", "UK", "TV", "PM", "AM", "CEO", "NASA", "FAQ", "ID"}

def say(text, extra=None):
    t = plain(text)
    for k, v in sorted({**BUILTIN_SAY, **(extra or {})}.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(r"(?<![\w])" + re.escape(k) + r"(?![\w])" if k[0].isalnum() else re.escape(k), v, t)
    def spell(m):
        w = m.group(0)
        return w if w in KEEP_ACRONYMS or (extra and w in extra) else " ".join(w) + " "
    t = re.sub(r"\b[A-Z]{2,6}\b", spell, t)
    return re.sub(r"\s+", " ", t).strip()

# ---------------------------------------------------------------- voiceover
def caps():
    import capabilities
    return capabilities

def vo_provider(req, allow_paid, notes, dry=False):
    have = caps().has_key
    simulated = bool(os.environ.get("REELSMITH_SIMULATE_KEYS"))
    kok = caps().kokoro_python()
    if req == "none":
        return None
    if req in ("elevenlabs", "openai"):
        keys = {"elevenlabs": ["ELEVENLABS_API_KEY", "TTS_VOICE_ID"], "openai": ["OPENAI_API_KEY"]}[req]
        if all(have(k) for k in keys) and allow_paid and (dry or not simulated):
            return req
        why = ("key not set" if not all(have(k) for k in keys) else "paid generation needs --allow-paid" if not allow_paid
               else "keys are simulated; only --dry-run can use them")
        notes.append(f"voiceover: {req} skipped ({why}); using free local voice")
    if kok:
        return "kokoro"
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return "espeak"
    notes.append("voiceover: no local TTS found (install kokoro-onnx or espeak-ng); rendering without VO")
    return None

def quote_paid(chars):
    # list prices checked 2026-10; see references/capabilities-and-keys.md. Quote only.
    return {"elevenlabs_usd_est": round(chars / 1000 * 0.30, 2), "openai_tts_usd_est": round(chars / 1_000_000 * 15, 4), "chars": chars}

def tts(text, provider, voice, out):
    key = hashlib.sha256(f"{provider}|{voice}|{text}".encode()).hexdigest()[:20]
    cached = CACHE / "vo" / f"{key}.wav"
    if cached.exists() and cached.stat().st_size > 1000:
        shutil.copy(cached, out); return True, True
    cached.parent.mkdir(parents=True, exist_ok=True)
    raw = cached.with_suffix(".raw.wav")
    if provider == "kokoro":
        env = dict(os.environ, HYPERFRAMES_PYTHON=caps().kokoro_python() or "")
        r = subprocess.run(HF + ["tts", text, "-o", str(raw), "--voice", voice or "af_heart"], capture_output=True, text=True, env=env)
        if r.returncode or not raw.exists():
            return False, False
    elif provider == "espeak":
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        sh([exe, "-v", "en-us+f3", "-s", "160", "-w", str(raw), text], capture_output=True)
    elif provider in ("elevenlabs", "openai"):
        # PAID. Reached only with --vo NAME --allow-paid and real keys. Keys are read from env, never logged.
        import urllib.request
        if provider == "elevenlabs":
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ['TTS_VOICE_ID']}?output_format=mp3_44100_128",
                data=json.dumps({"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")}).encode(),
                headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        else:
            req = urllib.request.Request("https://api.openai.com/v1/audio/speech",
                data=json.dumps({"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"), "voice": os.environ.get("OPENAI_TTS_VOICE", "alloy"),
                                 "input": text, "response_format": "wav"}).encode(),
                headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"], "Content-Type": "application/json"})
        try:
            raw.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            print(f"paid TTS failed ({type(e).__name__}); falling back"); return False, False
    else:
        return False, False
    # per-segment two-pass loudness normalisation to -16 LUFS, trimmed of leading/trailing silence
    norm(raw, cached, -16, pre="silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,")
    raw.unlink(missing_ok=True)
    shutil.copy(cached, out)
    return True, False

def norm(src, dst, lufs, pre="", tp=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", f"{pre}loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"{pre}loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", af, "-ar", "48000", "-ac", "2", str(dst)])

# ---------------------------------------------------------------- timing
def snap_scenes(scenes, grid, offset, unit, loop):
    """Each scene: target seconds + hard minimum (VO). Cuts land on grid points (music time minus offset)."""
    pts = {"bar": grid["downbeats"], "beat": grid["beats"],
           "half": sorted(set(grid["downbeats"] + grid["beats"][::2]))}[unit]
    pts = [round(p - offset, 3) for p in pts if p - offset > 0.05]
    t = 0.0
    for s in scenes:
        target, need = s["seconds"], s.get("min", 0)
        lo = t + max(need, 0.7 * target)
        cands = [p for p in pts if p >= lo - 1e-3]
        nxt = min(cands, key=lambda p: abs(p - (t + max(target, need)))) if cands else t + max(target, need)
        s["start"], s["dur"] = round(t, 3), round(nxt - t, 3)
        t = nxt
    if loop:  # loop: total must land on a downbeat so the music seam is on the bar line
        bars = [round(p - offset, 3) for p in grid["downbeats"] if p - offset >= t - 1e-3]
        if bars:
            scenes[-1]["dur"] = round(bars[0] - scenes[-1]["start"], 3); t = bars[0]
    return round(t, 3)

# ---------------------------------------------------------------- audio
def music_bed(args, meta, brand, total_hint, work):
    energy = (brand.get("motion") or {}).get("energy") or meta.get("energy", "medium")
    energy = meta.get("energy", energy)
    bpm, mood, unit = ENERGY.get(energy, ENERGY["medium"])
    unit = meta.get("unit", unit)
    src = args.music or (brand.get("music") or {}).get("file") or "synth"
    if src == "none":
        return None, beatlib.grid_fixed(bpm, total_hint + 60), 0.0, unit, {"music": "none"}
    if src == "synth":
        p = work / f"synth-{bpm}-{mood}.mp3"
        if not p.exists():
            beatlib.synth(str(p), bpm=bpm, seconds=int(total_hint + 40), mood=mood)
        return p, beatlib.grid_fixed(bpm, total_hint + 40), 0.0, unit, {"music": "synth bed (generated)", "bpm": bpm, "license": "generated, no third-party rights"}
    p = Path(src)
    gj = p.with_suffix(".beatgrid.json")
    grid = json.loads(gj.read_text()) if gj.exists() else beatlib.make_grid(str(p))
    off = grid["downbeats"][0] if grid.get("downbeats") and grid["downbeats"][0] < 6 else 0.0
    cred = {}
    cj = p.parent / "credits.json"
    if cj.exists():
        for c in json.loads(cj.read_text()):
            if c.get("file") in (p.name, str(p)) or Path(str(c.get("file", ""))).name == p.name:
                cred = c
    return p, grid, off, unit, {"music": p.name, "bpm": round(grid.get("bpm", 0), 2), "trim_to_first_downbeat_s": off, "credit": cred}

def premix(music, offset, vo, total, loop, out, lufs=-14):
    """One stereo bed: music (ducked under VO with 0.25 s ramps) + VO clips at their offsets -> two-pass loudnorm."""
    ins, fl, labels = [], [], []
    if music:
        ins += ["-i", str(music)]
        if vo:
            r = 0.25
            terms = [f"clip(min((t-{a - r:.3f})/{r},({b + r:.3f}-t)/{r}),0,1)" for a, b in ((v["at"], v["at"] + v["dur"]) for v in vo)]
            duck = terms[0]
            for tt in terms[1:]:
                duck = f"max({duck},{tt})"
            vol = f"volume='0.55-0.39*{duck}':eval=frame"
        else:
            vol = "volume=1.0"
        fades = (f"afade=t=in:d=0.01,afade=t=out:st={total - 0.02:.3f}:d=0.02" if loop else
                 f"afade=t=in:d=0.4,afade=t=out:st={max(0, total - 2.0):.3f}:d=2.0")
        fl.append(f"[0:a]atrim=start={offset:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                  f"atrim=end={total:.3f},{vol},{fades}[m]")
        labels.append("[m]")
    for i, v in enumerate(vo):
        k = len(ins) // 2
        ins += ["-i", str(v["file"])]
        ms = int(v["at"] * 1000)
        fl.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]")
        labels.append(f"[v{i}]")
    if not labels:
        return None
    fl.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=end={total:.3f}[mix]")
    tmp = out.with_suffix(".pre.wav")
    sh(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[mix]", "-ar", "48000", str(tmp)])
    norm(tmp, out, lufs)
    tmp.unlink(missing_ok=True)
    return out

# ---------------------------------------------------------------- HTML assembly
def layout_css(a):
    t, b, l, r = a["safe"]
    return (f":root{{--W:{a['W']}px;--H:{a['H']}px;--safe-t:{t*100:.1f}%;--safe-b:{b*100:.1f}%;--safe-l:{l*100:.1f}%;"
            f"--safe-r:{r*100:.1f}%;--h1:{a['h1']}vmin;--h2:{a['h2']}vmin;--body:{a['body']}vmin;--kicker:{a['kicker']}vmin;}}")

def page(a, total, scenes_html, js, css, data, audio_rel, brand_css_rel, title):
    clips = []
    for s in scenes_html:
        clips.append(f'<div class="scene clip" id="{s["id"]}" data-start="{s["start"]:.3f}" data-duration="{s["dur"]:.3f}" '
                     f'data-track-index="{s.get("track", 1)}">{s["html"]}</div>')
    audio = (f'<audio class="clip" id="rs-audio" src="{audio_rel}" data-start="0" data-duration="{total:.3f}" '
             f'data-track-index="9" data-volume="1"></audio>') if audio_rel else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{esc(title)}</title>
<link rel="stylesheet" href="{brand_css_rel}">
<link rel="stylesheet" href="base.css">
<style>{layout_css(a)}
{css}</style>
<script src="gsap.min.js"></script>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{a['W']}" data-height="{a['H']}">
<div id="rs-bg"></div><div class="rs-blob" id="rs-blob1"></div><div class="rs-blob" id="rs-blob2"></div><div class="rs-blob" id="rs-blob3"></div><div id="rs-grid"></div>
{chr(10).join(clips)}
<div id="rs-wipe"></div>
{audio}
</div>
<script id="rs-data" type="application/json">{json.dumps(data)}</script>
<script src="rs.js"></script>
<script>
(function(){{ const {{D, tl, enter, exit, drift, kenburns, roll, wipe, bgDrift, finish, has, camera}} = RS;
bgDrift({total:.3f});
{js}
finish(); }})();
</script>
</body></html>
"""

def prep_media(src, proj, maxpx=2400):
    """Copy an image into the project, downscaled to <= maxpx on the long side. Returns relative path."""
    src = Path(src)
    if not src.is_absolute():
        src = (Path.cwd() / src)
    dst = proj / "media" / (hashlib.sha1(str(src).encode()).hexdigest()[:10] + src.suffix.lower())
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        if src.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf",
                f"scale='if(gt(iw,ih),min({maxpx},iw),-2)':'if(gt(iw,ih),-2,min({maxpx},ih))'", "-q:v", "3", str(dst)])
        else:
            shutil.copy(src, dst)
    return "media/" + dst.name

# ---------------------------------------------------------------- render
def render(args):
    t_start = time.time()
    mod, meta, tdir = load_template(args.template)
    content = json.loads(Path(args.content).read_text()) if args.content else json.loads((tdir / "sample.json").read_text())
    cbase = Path(args.content).resolve().parent if args.content else tdir
    bpath = Path(args.brand or PKG / "brand" / "sample-brand.json")
    brand = brandlib.load(bpath)
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    work = out / "_work"; work.mkdir(exist_ok=True)
    notes = []
    errs, warns = contract(content, meta)
    for w in warns: print("WARN", w)
    if errs:
        for e in errs: print("ERROR", e)
        raise SystemExit("content contract failed (see template.json budgets)")
    # resolve media paths relative to the content file
    def media_abs(p):
        if not p: return None
        q = Path(p)
        return q if q.is_absolute() else (cbase / q).resolve()
    ctx = {"brand": brand, "content": content, "media_abs": media_abs, "esc": esc, "words": words_html, "plain": plain}
    scenes = mod.plan(content, ctx)   # [{id, seconds, vo?, kind}]
    # ---- voiceover
    want_vo = args.vo if args.vo != "auto" else ("auto" if any(s.get("vo") for s in scenes) else "none")
    provider = vo_provider("kokoro" if want_vo == "auto" else want_vo, args.allow_paid, notes, args.dry_run) if want_vo != "none" else None
    pron = {**((brand.get("voice") or {}).get("pronunciations") or {}), **(content.get("pronunciations") or {})}
    voice = (brand.get("voice") or {}).get("tts_voice") or "af_heart"
    chars = sum(len(plain(s.get("vo", ""))) for s in scenes)
    vo_files = {}
    if provider and not args.dry_run:
        for s in scenes:
            if not s.get("vo"): continue
            f = work / f"vo-{s['id']}.wav"
            ok, hit = tts(say(s["vo"], pron), provider, voice if provider == "kokoro" else None, f)
            if ok:
                vo_files[s["id"]] = f
                d = dur(f)
                s["vo_dur"] = round(d, 3)
                s["min"] = round(d + 0.25 + 0.5, 3)   # 0.25 s lead-in + 0.5 s tail pad
                s["vo_cached"] = hit
            else:
                notes.append(f"voiceover failed for scene {s['id']}; continuing without it")
    # ---- music + grid + timing
    hint = sum(max(s["seconds"], s.get("min", 0)) for s in scenes)
    music, grid, offset, unit, mcred = music_bed(args, meta, brand, hint, work)
    total = snap_scenes(scenes, grid, offset, unit, args.loop)
    vo_list = [{"file": vo_files[s["id"]], "at": s["start"] + 0.25, "dur": s["vo_dur"], "id": s["id"], "text": plain(s["vo"])}
               for s in scenes if s["id"] in vo_files]
    for v in vo_list:  # narration-sync guard (borrowed QA rule): VO may not run past its scene end
        sc = next(s for s in scenes if s["id"] == v["id"])
        if v["at"] + v["dur"] > sc["start"] + sc["dur"] + 0.05:
            notes.append(f"narration overflow in {v['id']}")
    job = {"version": 1, "template": args.template, "engine": meta.get("engine", "hyperframes"), "brand": brand.get("name"),
           "total_seconds": total, "loop": bool(args.loop), "scenes": [{k: s[k] for k in s if k not in ("html",)} for s in scenes],
           "voiceover": {"provider": provider, "voice": voice if provider == "kokoro" else ("(env)" if provider else None),
                         "chars": chars, "paid_quote": quote_paid(chars) if chars else None},
           "music": mcred, "capabilities": caps().snapshot() if hasattr(caps(), "snapshot") else None,
           "notes": notes, "warnings": warns, "outputs": {}}
    if args.dry_run:
        (out / "job.json").write_text(json.dumps(job, indent=2, default=str))
        print(json.dumps({"dry_run": True, "total_seconds": total, "vo_provider": provider, "scenes": len(scenes), "notes": notes}, indent=2))
        return job
    audio = premix(music, offset, vo_list, total, args.loop, work / "mix.wav") if (music or vo_list) else None
    # credits (stock/music) collected from content media + music
    credits = list(content.get("credits", []))
    if mcred.get("credit"): credits.append(mcred["credit"])
    for m in mod.media(content) if hasattr(mod, "media") else []:
        q = media_abs(m)
        if q and (q.parent / "credits.json").exists():
            for c in json.loads((q.parent / "credits.json").read_text()):
                if Path(str(c.get("file", ""))).name == q.name and c not in credits:
                    credits.append(c)
    (out / "credits.json").write_text(json.dumps(credits, indent=2))
    # captions from VO (approximate timings: syllable-weighted spread inside each VO clip, not forced alignment)
    words = []
    for v in vo_list:
        words += caplib.estimate(v["text"], v["at"], v["at"] + v["dur"])
    for aspect in args.aspect.split(","):
        a = ASPECTS[aspect]
        proj = work / f"proj-{aspect}"
        if proj.exists(): shutil.rmtree(proj)
        proj.mkdir(parents=True)
        brandlib.bundle(str(bpath), str(proj))
        for f in ("rs.js", "base.css"):
            shutil.copy(TPL / "_shared" / f, proj / f)
        shutil.copy(PKG / "hyperframes-example" / "assets" / "gsap.min.js", proj / "gsap.min.js")
        audio_rel = None
        if audio:
            shutil.copy(audio, proj / "mix.wav"); audio_rel = "mix.wav"
        actx = dict(ctx, aspect=aspect, A=a, W=a["W"], H=a["H"], vertical=a["H"] > a["W"], square=a["H"] == a["W"],
                    media=lambda p: prep_media(media_abs(p), proj), logo=logo_html(proj, brand), total=total, loop=args.loop,
                    vo_provider=provider if vo_list else None, vo_scenes={v["id"] for v in vo_list},
                    burn_captions=bool(vo_list) and (args.captions == "burn" or (args.captions == "auto" and a["H"] >= a["W"])))
        built = mod.build(content, actx, scenes)
        if vo_list and content.get("ai_voice_disclosure", True):
            # visible AI-narration disclosure (borrowed publication rule): small, persistent, inside the safe area
            label = content.get("ai_voice_label") or "Narration: AI-generated voice"
            built["scenes"].append({"id": "rs-disclosure", "start": 0, "dur": total, "track": 8,
                                    "html": f'<div class="rs-ai">{esc(label)}</div>'})
        data = {"seed": 11, "ease": (brand.get("motion") or {}).get("ease", "power3.out"), "loop": bool(args.loop), "total": total}
        (proj / "index.html").write_text(page(a, total, built["scenes"], built["js"], built.get("css", ""), data, audio_rel,
                                              "brand/brand.css", content.get("title") or args.template))
        (proj / "hyperframes.json").write_text(json.dumps({"name": f"{args.template}-{aspect}"}))
        (proj / "meta.json").write_text(json.dumps({"id": f"{args.template}-{aspect}", "name": f"{args.template} {aspect}"}))
        lint = subprocess.run(HF + ["lint", str(proj), "--json"], capture_output=True, text=True)
        lint_errors = None
        try:
            lj = json.loads(lint.stdout[lint.stdout.index("{"):])
            lint_errors = lj.get("errorCount", len([i for i in lj.get("issues", lj.get("findings", [])) if i.get("severity") == "error"]))
        except Exception:
            pass
        raw = work / f"raw-{aspect}.mp4"
        q = "draft" if args.draft else args.quality
        r = subprocess.run(HF + ["render", str(proj), "-o", str(raw), "-q", q, "-f", "30", "-w", str(args.workers)], capture_output=True, text=True)
        if r.returncode or not raw.exists():
            print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit(f"render failed for {aspect}")
        final = out / f"{args.template}-{aspect}.mp4"
        cap_mode = args.captions if args.captions != "auto" else ("burn" if words and a["H"] >= a["W"] else ("sidecar" if words else "none"))
        if words and cap_mode in ("burn", "sidecar"):
            cues = caplib.build_cues(words, "social" if cap_mode == "burn" else "netflix")
            stem = out / f"{args.template}-{aspect}"
            Path(f"{stem}.srt").write_text(caplib.to_srt(caplib.build_cues(words, "netflix")))
            Path(f"{stem}.vtt").write_text(caplib.to_vtt(caplib.build_cues(words, "netflix")))
            if cap_mode == "burn":
                ass = work / f"cap-{aspect}.ass"
                ass.write_text(caplib.to_ass(cues, a["ratio"], meta.get("caption_style", "boxed"), brand))
                caplib.burn(str(raw), str(ass), str(final), fontsdir=str(proj / "brand" / "fonts"))
            else:
                strip(raw, final)
        else:
            strip(raw, final)
        job["outputs"][aspect] = {"file": final.name, "seconds": round(dur(final), 3), "captions": cap_mode,
                                  "lint_errors": lint_errors}
        print(f"wrote {final} ({dur(final):.2f}s)")
    job["render_seconds"] = round(time.time() - t_start, 1)
    (out / "job.json").write_text(json.dumps(job, indent=2, default=str))
    return job

def strip(src, dst):
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-map", "0", "-c", "copy", "-map_metadata", "-1",
        "-movflags", "+faststart", str(dst)])

def logo_html(proj, brand):
    lp = proj / "brand"
    for name in ("logo.svg", "logo.png", "logo.webp"):
        if (lp / name).exists():
            return f'<img class="logo-img" src="brand/{name}" alt="">'
    return f'<div class="h2">{esc(brand.get("name", ""))}</div>'

# ---------------------------------------------------------------- loop export (kiosk / booth / room display)
def loop_export(args):
    """Repeat a loop-rendered video N times (stream copy) for players without a loop setting, and report the seam."""
    v = Path(args.video); out = Path(args.out)
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{v.resolve()}'\n" for _ in range(args.times)))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])
    lst.unlink()
    print(json.dumps(seam(v), indent=2)); print(f"wrote {out} ({dur(out):.1f}s)")

def seam(v):
    """Compare first and last frame (PSNR) and audio level at the seam. High PSNR = invisible loop point."""
    d = dur(v)
    a, b = Path("/tmp/rs_first.png"), Path("/tmp/rs_last.png")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-frames:v", "1", str(a)])
    sh(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.05", "-i", str(v), "-update", "1", "-frames:v", "1", str(b)])
    r = subprocess.run(["ffmpeg", "-i", str(a), "-i", str(b), "-lavfi", "psnr", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"average:([\d.inf]+)", r)
    psnr = m.group(1) if m else "?"
    try: ok = psnr == "inf" or float(psnr) >= 30
    except ValueError: ok = False
    return {"video": str(v), "seconds": round(d, 3), "first_vs_last_psnr_db": psnr, "seamless_visual": ok}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list")
    p = sp.add_parser("sample"); p.add_argument("template")
    p = sp.add_parser("render")
    p.add_argument("--template", required=True); p.add_argument("--content"); p.add_argument("--brand")
    p.add_argument("--aspect", default="16x9,9x16,1x1"); p.add_argument("--out", required=True)
    p.add_argument("--music"); p.add_argument("--vo", default="auto", choices=["auto", "none", "kokoro", "espeak", "elevenlabs", "openai"])
    p.add_argument("--allow-paid", action="store_true"); p.add_argument("--draft", action="store_true")
    p.add_argument("--quality", default="looks"); p.add_argument("--workers", type=int, default=2)
    p.add_argument("--captions", default="auto", choices=["auto", "burn", "sidecar", "none"])
    p.add_argument("--loop", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("loop"); p.add_argument("video"); p.add_argument("--times", type=int, default=10); p.add_argument("-o", "--out", required=True)
    p = sp.add_parser("seam"); p.add_argument("video")
    a = ap.parse_args()
    if a.cmd == "list":
        for t in templates():
            m = json.loads((TPL / t / "template.json").read_text())
            print(f"{t:22s} {m.get('engine','hyperframes'):12s} {m.get('summary','')}")
    elif a.cmd == "sample":
        print((TPL / a.template / "sample.json").read_text())
    elif a.cmd == "render":
        if a.template not in templates():
            raise SystemExit(f"unknown template {a.template}; try: {', '.join(templates())}")
        m = json.loads((TPL / a.template / "template.json").read_text())
        if m.get("engine") == "remotion":
            raise SystemExit(f"{a.template} is a Remotion template: see templates/{a.template}/README.md (render.sh)")
        render(a)
    elif a.cmd == "loop":
        loop_export(a)
    elif a.cmd == "seam":
        print(json.dumps(seam(Path(a.video)), indent=2))

if __name__ == "__main__":
    main()
