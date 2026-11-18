#!/usr/bin/env python3
"""Check dependencies for Reelsmith renders before the first job on a new machine.

Usage: python3 scripts/doctor.py [--hyperframes]

Checks Python version, ffmpeg/ffprobe (and the encoders and filters the pipeline uses: libx264, aac,
loudnorm, ebur128, alimiter, xfade, drawtext), Python packages (numpy, scipy, Pillow, librosa),
Node/npx for HyperFrames, and fonts. --hyperframes also pings npx to verify the HyperFrames version
(downloads it on first run). Exits 1 if core dependencies are missing. Approach after coleam00/skills
edit-video doctor.py (MIT). See THIRD_PARTY_NOTICES.md.
"""
import importlib, os, re, shutil, subprocess, sys
from pathlib import Path

if any(a in ("-h", "--help") for a in sys.argv[1:]): sys.exit(print(__doc__.strip()))

ROWS, MISSING = [], []

def row(state, name, detail, fix=""):
    ROWS.append((state, name, detail, fix))
    if state == "MISSING": MISSING.append(name)

def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return -1, str(e)

def main():
    v = sys.version_info
    row("OK" if (3, 10) <= v[:2] < (4, 0) else "WARN", "python", f"{v.major}.{v.minor}.{v.micro}",
        "" if (3, 10) <= v[:2] < (4, 0) else "Reelsmith is tested on Python 3.10+")
    
    for tool in ("ffmpeg", "ffprobe"):
        code, out = sh([tool, "-version"])
        row("OK" if code == 0 else "MISSING", tool, out.splitlines()[0][:70] if code == 0 else "not on PATH",
            "" if code == 0 else "install ffmpeg (a full build: libx264, libfreetype) and put it on PATH")
    
    if shutil.which("ffmpeg"):
        _, enc = sh(["ffmpeg", "-hide_banner", "-encoders"]); _, flt = sh(["ffmpeg", "-hide_banner", "-filters"])
        for name, hay, why in (("libx264", enc, "every render"), ("aac", enc, "every export")):
            row("OK" if re.search(rf"\b{name}\b", hay) else "MISSING", f"ffmpeg {name}", why)
        for name, why in (("loudnorm", "loudness"), ("ebur128", "level matching + review.py"), ("alimiter", "peak limit"),
                         ("xfade", "transitions"), ("drawtext", "lower-third cards (needs libfreetype)")):
            ok = re.search(rf"\b{name}\b", flt) is not None
            row("OK" if ok else ("MISSING" if name in ("loudnorm", "ebur128", "alimiter") else "WARN"), f"ffmpeg {name}", why)
    
    pkgs = {"numpy": "core", "scipy": "core", "PIL": "frame sheets", "librosa": "beat detection (optional)"}
    for mod, why in pkgs.items():
        try:
            m = importlib.import_module(mod); ver = getattr(m, "__version__", "")
            row("OK" if mod != "librosa" else "INFO", mod, f"{ver} ({why})")
        except Exception as e:
            lvl = "INFO" if mod == "librosa" else "MISSING"
            row(lvl, mod, f"{why}: {str(e)[:60]}", "" if mod == "librosa" else "install via pip or conda")
    
    node = shutil.which("node"); npx = shutil.which("npx") or shutil.which("npx.cmd")
    if node:
        _, nv_ = sh([node, "--version"]); major = int(re.findall(r"\d+", nv_)[0]) if re.findall(r"\d+", nv_) else 0
        row("OK" if major >= 18 else "WARN", "node", nv_.strip(), "" if major >= 18 else "HyperFrames needs Node 18+")
    else:
        row("INFO", "node", "not found: HyperFrames/OpenMotion renders unavailable (templates still work)")
    row("OK" if npx else "INFO", "npx", npx or "not found (install Node to get npx)")
    
    pin = os.environ.get("HYPERFRAMES_VERSION")
    row("OK" if pin else "INFO", "HYPERFRAMES_VERSION", pin or "unset: renders use the latest release",
        "" if pin else "set it per project so a new release cannot change a render mid-edit")
    
    if "--hyperframes" in sys.argv and npx:
        code, out = sh([npx, "-y", f"hyperframes@{pin}" if pin else "hyperframes", "--version"], timeout=300)
        row("OK" if code == 0 else "WARN", "hyperframes", out.strip().splitlines()[-1][:70] if out.strip() else "no output")
    
    # Font check: look for a common sans and a mono font
    font_dirs = ["/usr/share/fonts", "/System/Library/Fonts", "C:\\Windows\\Fonts", str(Path.home() / ".fonts")]
    found_sans, found_mono = False, False
    for d in font_dirs:
        if Path(d).exists():
            for f in Path(d).rglob("*.ttf"):
                fn = f.name.lower()
                if "dejavu" in fn or "liberation" in fn or "arial" in fn:
                    found_sans = True
                if "mono" in fn or "courier" in fn:
                    found_mono = True
    row("OK" if found_sans else "WARN", "sans font", "found" if found_sans else "not found", 
        "" if found_sans else "install DejaVu or Liberation fonts for HyperFrames captions")
    row("OK" if found_mono else "INFO", "mono font", "found" if found_mono else "not found")
    
    w = max(len(r[1]) for r in ROWS)
    for state, name, detail, fix in ROWS:
        print(f"{state:8} {name:{w}} {detail}" + (f"\n{'':8} {'':{w}} fix: {fix}" if fix and state != "OK" else ""))
    
    have = lambda n: n not in MISSING
    print("\nWhat works here:")
    core = all(have(n) for n in ("ffmpeg", "ffprobe", "numpy", "scipy", "PIL"))
    ffmpeg_ok = have("ffmpeg libx264") and have("ffmpeg aac") and have("ffmpeg loudnorm") and have("ffmpeg ebur128")
    print(f" core renders + review.py : {'yes' if core and ffmpeg_ok else 'NO'}")
    print(f" HyperFrames / OpenMotion  : {'yes' if node and npx else 'no (needs Node + npx)'}")
    print(f" beat detection (beats.py) : {'yes' if have('librosa') or any(r[1] == 'librosa' and r[0] == 'INFO' for r in ROWS) else 'no (install librosa)'}")
    sys.exit(1 if not (core and ffmpeg_ok) else 0)

if __name__ == "__main__":
    main()
