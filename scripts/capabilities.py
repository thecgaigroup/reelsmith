#!/usr/bin/env python3
"""Reelsmith capability check. Run at the start of every job.

Reports which optional features are ON (key or tool present) or OFF (falls back
to a free local option). It checks only whether an env var is non-empty. It never
prints, logs, hashes or measures a key value.

  python3 capabilities.py                 # table
  python3 capabilities.py --json          # machine-readable (used by other scripts)
  python3 capabilities.py --simulate PEXELS_API_KEY,FAL_KEY   # pretend these exist (testing only)
  python3 capabilities.py --simulate all
  python3 capabilities.py --no-keys       # ignore all keys (free path)
  python3 capabilities.py --mcp fal,higgsfield   # the agent has these MCP connectors

Other scripts import it:  from capabilities import detect, has_key
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SIM: set = set(filter(None, os.environ.get("REELSMITH_SIMULATE_KEYS", "").split(",")))

# Every optional service: env vars that switch it on, what it adds, the free fallback,
# and where to get a key. Add new services here; nothing else needs to change.
SERVICES = [
    {"id": "pexels", "feature": "Stock video + photos (Pexels)", "env": ["PEXELS_API_KEY"],
     "paid": False, "fallback": "Openverse CC images (no key), user media, or typographic scenes",
     "tier": "Free. 200 requests/hour, 20,000/month. Credit Pexels + photographer.",
     "signup": "https://www.pexels.com/api/new/"},
    {"id": "pixabay", "feature": "Stock video + photos (Pixabay)", "env": ["PIXABAY_API_KEY"],
     "paid": False, "fallback": "Openverse CC images (no key), user media, or typographic scenes",
     "tier": "Free. 100 requests/60 s; cache results 24 h; download, don't hotlink.",
     "signup": "https://pixabay.com/api/docs/"},
    {"id": "unsplash", "feature": "Stock photos (Unsplash)", "env": ["UNSPLASH_ACCESS_KEY"],
     "paid": False, "fallback": "Pexels/Pixabay if set, else Openverse or user media",
     "tier": "Free. Demo apps 50 requests/hour. Credit 'Photo by X on Unsplash'.",
     "signup": "https://unsplash.com/oauth/applications"},
    {"id": "elevenlabs", "feature": "Premium voiceover with word timings (ElevenLabs)",
     "env": ["ELEVENLABS_API_KEY", "TTS_VOICE_ID"], "paid": True,
     "fallback": "OpenAI TTS if set, else Kokoro (local, free) or espeak-ng",
     "tier": "Free tier about 10k characters/month (check current plan). Paid plans for commercial use.",
     "signup": "https://elevenlabs.io/app/settings/api-keys"},
    {"id": "openai", "feature": "Voiceover (OpenAI TTS) + cloud transcription", "env": ["OPENAI_API_KEY"],
     "paid": True, "fallback": "Kokoro or espeak-ng voice; local Whisper via hyperframes transcribe",
     "tier": "Pay as you go, no free tier. Quote cost before use.",
     "signup": "https://platform.openai.com/api-keys"},
    {"id": "polly", "feature": "Voiceover (Amazon Polly)", "env": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
     "paid": True, "fallback": "Kokoro or espeak-ng voice",
     "tier": "AWS free tier covers a monthly character allowance for 12 months (check current terms).",
     "signup": "https://aws.amazon.com/polly/"},
    {"id": "fal", "feature": "AI b-roll / image / music generation (Fal)", "env": ["FAL_KEY"], "mcp": "fal",
     "paid": True, "fallback": "Stock footage, user media, or motion-graphics scenes",
     "tier": "Paid per generation. Reelsmith only QUOTES; you approve each spend.",
     "signup": "https://fal.ai/dashboard/keys"},
    {"id": "higgsfield", "feature": "AI video / avatars (Higgsfield)", "env": ["HIGGSFIELD_API_KEY"], "mcp": "higgsfield",
     "paid": True, "fallback": "Stock footage, user media, or motion-graphics scenes",
     "tier": "Paid credits. Reelsmith only QUOTES; you approve each spend.",
     "signup": "https://higgsfield.ai/"},
]

def has_key(name: str) -> bool:
    """True if env var is set and non-empty (or simulated). Never returns the value."""
    if "all" in _SIM or name in _SIM:
        return True
    if os.environ.get("REELSMITH_IGNORE_KEYS") == "1":
        return False
    return bool(os.environ.get(name, "").strip())

def _run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None

def _node_major():
    for node in [os.environ.get("REELSMITH_NODE"), "/workspace/tools/node22/bin/node", shutil.which("node")]:
        if node and Path(node).exists():
            r = _run([node, "--version"])
            if r and r.returncode == 0:
                try:
                    return int(r.stdout.strip().lstrip("v").split(".")[0])
                except ValueError:
                    pass
    return 0

def _py_has(mod):
    venv = os.environ.get("REELSMITH_AUDIO_PY", "/workspace/reelsmith-tests/venv-audio/bin/python")
    for py in [venv, sys.executable]:
        if py and Path(py).exists():
            r = _run([py, "-c", f"import {mod}"], timeout=60)
            if r and r.returncode == 0:
                return py
    return None

def kokoro_python():
    """Python that has kokoro-onnx (HyperFrames `tts` needs it). Set HYPERFRAMES_PYTHON to point at a venv."""
    cands = [os.environ.get("HYPERFRAMES_PYTHON"), shutil.which("python3"),
             str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python")]
    for py in [c for c in cands if c and Path(c).exists()]:
        r = _run([py, "-c", "import kokoro_onnx, soundfile"], timeout=60)
        if r and r.returncode == 0:
            return py
    return None

def local_tools():
    ff = shutil.which("ffmpeg")
    filters = ""
    if ff:
        r = _run([ff, "-hide_banner", "-filters"])
        filters = r.stdout if r else ""
    kokoro_cache = any(Path(p).expanduser().exists() for p in [
        "~/.cache/hyperframes/tts", "~/.cache/hyperframes/kokoro", "~/.cache/kokoro"])
    rv = os.environ.get("REELSMITH_REMOTION_DIR", "/workspace/remotion-video")
    kpy = kokoro_python()
    return {
        "ffmpeg": bool(ff),
        "ffmpeg_subtitles": " subtitles " in filters or " ass " in filters,
        "ffmpeg_loudnorm": "loudnorm" in filters,
        "ffprobe": bool(shutil.which("ffprobe")),
        "espeak_ng": bool(shutil.which("espeak-ng")),
        "node22": _node_major() >= 22,
        "kokoro_cached": kokoro_cache,
        "kokoro": _node_major() >= 22 and bool(kpy),
        "librosa": bool(_py_has("librosa")),
        "pillow": bool(_py_has("PIL")),
        "remotion_project": (Path(rv) / "node_modules" / "remotion").exists(),
    }

def detect(mcp=()):
    mcp = set(mcp)
    services = []
    for s in SERVICES:
        present = [e for e in s["env"] if has_key(e)]
        on = len(present) == len(s["env"]) or (s.get("mcp") in mcp)
        simulated = bool(present) and all(("all" in _SIM or e in _SIM) for e in present)
        via = "simulated" if (on and simulated) else "mcp" if (s.get("mcp") in mcp and len(present) != len(s["env"])) else ("env" if on else None)
        services.append({"id": s["id"], "feature": s["feature"], "on": on, "via": via, "paid": s["paid"],
                         "missing": [e for e in s["env"] if e not in present] if not on else [],
                         "fallback": s["fallback"], "tier": s["tier"], "signup": s["signup"]})
    tools = local_tools()
    on = {s["id"]: s["on"] for s in services}
    vo = ("elevenlabs" if on["elevenlabs"] else "openai" if on["openai"] else "polly" if on["polly"]
          else "kokoro" if tools["kokoro"] else "espeak" if tools["espeak_ng"] else "none")
    free_vo = "kokoro" if tools["kokoro"] else "espeak" if tools["espeak_ng"] else "none"
    stock = [p for p in ("pexels", "pixabay", "unsplash") if on[p]] + ["openverse"]
    beats = "librosa" if tools["librosa"] else "hyperframes" if tools["node22"] else "fixed-bpm"
    plan = {
        "voiceover": vo + (" (paid: quote + confirm first)" if vo in ("elevenlabs", "openai", "polly") else ""),
        "voiceover_free": free_vo,
        "stock_providers": stock,
        "ai_generation": [p for p in ("fal", "higgsfield") if on[p]],  # quote-only
        "beat_detection": beats,
        "music": "user track or licensed track; synthetic bed fallback",
        "captions_burn_in": tools["ffmpeg_subtitles"],
        "engines": [e for e, ok in (("hyperframes", tools["node22"]), ("remotion", tools["remotion_project"]), ("ffmpeg", tools["ffmpeg"])) if ok],
    }
    return {"services": services, "tools": tools, "plan": plan, "simulated": sorted(_SIM)}

def snapshot():
    """On/off only (never values) for job.json manifests."""
    d = detect()
    return {"services": {s["id"]: s["on"] for s in d["services"]}, "voiceover_free": d["plan"]["voiceover_free"],
            "engines": d["plan"]["engines"]}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--simulate", default="", help="comma list of env names (or 'all') to treat as present")
    ap.add_argument("--no-keys", action="store_true", help="ignore every env key (test the free path)")
    ap.add_argument("--mcp", default="", help="comma list of connected MCP services, e.g. fal,higgsfield")
    a = ap.parse_args()
    if a.no_keys:
        os.environ["REELSMITH_IGNORE_KEYS"] = "1"
    if a.simulate:
        _SIM.update(x.strip() for x in a.simulate.split(",") if x.strip())
        os.environ["REELSMITH_SIMULATE_KEYS"] = ",".join(sorted(_SIM))
    caps = detect([m.strip() for m in a.mcp.split(",") if m.strip()])
    if a.json:
        print(json.dumps(caps, indent=2)); return
    if caps["simulated"]:
        print(f"SIMULATED keys (testing only, use --dry-run): {', '.join(caps['simulated'])}\n")
    print("Optional services (key values are never shown)")
    for s in caps["services"]:
        mark = "ON " if s["on"] else "off"
        extra = f"via {s['via']}" if s["on"] else f"needs {' + '.join(s['missing'])} -> fallback: {s['fallback']}"
        paid = " [paid: quote first]" if s["paid"] else ""
        print(f"  [{mark}] {s['feature']}{paid}  {extra}")
    print("\nLocal tools")
    for k, v in caps["tools"].items():
        print(f"  [{'ON ' if v else 'off'}] {k}")
    print("\nThis job will use")
    for k, v in caps["plan"].items():
        print(f"  {k}: {', '.join(v) if isinstance(v, list) else v}")
    off = [s for s in caps["services"] if not s["on"]]
    if off:
        print("\nOptional: keys that would improve results (never required)")
        for s in off:
            print(f"  {' + '.join(s['missing'])}: {s['feature']}. {s['tier']} {s['signup']}")

if __name__ == "__main__":
    main()
