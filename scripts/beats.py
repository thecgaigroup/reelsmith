#!/usr/bin/env python3
"""Music helper: beat grid, cut snapping, synthetic fallback bed, fit-to-length.

  beats.py grid  track.mp3 -o beatgrid.json          # bpm, beats, downbeats, bars, sections
  beats.py snap  beatgrid.json --durations 3,2.5,4,3 [--unit bar|beat|half]
                                                     # scene lengths -> cut times on the grid
  beats.py synth -o bed.mp3 --bpm 120 --seconds 30 [--mood bright|dark|calm]
  beats.py fit   track.mp3 --seconds 22 -o fitted.mp3 [--grid beatgrid.json]
                                                     # trim to a bar line, fade out, loudness-safe
  beats.py lock  beatgrid.json cuts.json [--tol 0.07] [--offset 0]
                                                     # share of cuts on a beat vs chance (beat-synced edit?)
Engines, in order: librosa (pip install librosa soundfile) -> `hyperframes beats` -> fixed BPM (--bpm).
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile
from pathlib import Path

def ffprobe_duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def grid_librosa(path):
    import numpy as np, librosa
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, frames = librosa.beat.beat_track(onset_envelope=onset, sr=sr, units="frames")
    tempo = float(np.atleast_1d(tempo)[0])
    beats = librosa.frames_to_time(frames, sr=sr).tolist()
    # Downbeat phase (assume 4/4): the phase whose beats carry the most low-end onset energy.
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    low = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S[:40]), sr=sr)
    strength = [float(low[min(f, len(low) - 1)]) for f in frames]
    phase = max(range(4), key=lambda k: sum(strength[k::4]) / max(1, len(strength[k::4])))
    downbeats = beats[phase::4]
    # Coarse sections from RMS energy, 8-bar windows: lets templates put the drop on a hero shot.
    rms = librosa.feature.rms(y=y)[0]
    t_rms = librosa.frames_to_time(range(len(rms)), sr=sr)
    sections = []
    for i in range(0, len(downbeats), 8):
        a = downbeats[i]; b = downbeats[i + 8] if i + 8 < len(downbeats) else float(t_rms[-1])
        m = rms[(t_rms >= a) & (t_rms < b)]
        sections.append({"start": round(a, 3), "end": round(b, 3), "energy": round(float(m.mean()) if len(m) else 0, 4)})
    if sections:
        mx = max(s["energy"] for s in sections) or 1
        for s in sections:
            s["energy"] = round(s["energy"] / mx, 3)
    return {"engine": "librosa", "bpm": round(tempo, 2), "beats": [round(b, 3) for b in beats],
            "downbeats": [round(b, 3) for b in downbeats], "sections": sections,
            "duration": round(len(y) / sr, 3)}

def grid_hyperframes(path):
    hf = os.environ.get("HF")
    if not hf:
        raise RuntimeError("HF not set (source hfenv.sh)")
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(path, Path(d) / Path(path).name)
        (Path(d) / "index.html").write_text(f'<html><body><audio class="clip" src="{Path(path).name}" data-start="0"></audio></body></html>')
        r = subprocess.run(hf.split() + ["beats", d, "--json"], capture_output=True, text=True, timeout=300)
        js = json.loads(r.stdout[r.stdout.find("{"):])
        beats = js.get("beats") or js.get("result", {}).get("beats") or []
        bpm = js.get("bpm") or js.get("tempo") or (60 / ((beats[-1] - beats[0]) / (len(beats) - 1)) if len(beats) > 1 else 120)
        return {"engine": "hyperframes", "bpm": round(float(bpm), 2), "beats": beats, "downbeats": beats[::4],
                "sections": [], "duration": ffprobe_duration(path)}

def grid_fixed(bpm, duration, offset=0.0):
    step = 60 / bpm
    beats = [round(offset + i * step, 3) for i in range(int((duration - offset) / step) + 1)]
    return {"engine": "fixed-bpm", "bpm": bpm, "beats": beats, "downbeats": beats[::4], "sections": [], "duration": duration}

def make_grid(track, bpm=None, engine="auto"):
    errors = []
    order = ["librosa", "hyperframes", "fixed"] if engine == "auto" else [engine]
    for e in order:
        try:
            if e == "librosa":
                return grid_librosa(track)
            if e == "hyperframes":
                return grid_hyperframes(track)
            if e == "fixed":
                return grid_fixed(bpm or 120, ffprobe_duration(track) if track else 60)
        except Exception as ex:
            errors.append(f"{e}: {ex.__class__.__name__}: {str(ex)[:120]}")
    raise SystemExit("no beat engine worked:\n" + "\n".join(errors))

def snap(grid, durations, unit="bar", start=0.0):
    """Turn rough scene lengths into cut times that land on the grid. Returns list of {start,end,dur}."""
    pts = {"bar": grid["downbeats"], "beat": grid["beats"],
           "half": grid["downbeats"] + [b for i, b in enumerate(grid["beats"]) if i % 2 == 0]}[unit]
    pts = sorted(set(p for p in pts if p >= start))
    if not pts:
        raise SystemExit("grid has no points")
    cuts, t = [], pts[0]
    out = []
    for d in durations:
        target = t + d
        nxt = min((p for p in pts if p > t + 0.6 * d), key=lambda p: abs(p - target), default=target)
        out.append({"start": round(t, 3), "end": round(nxt, 3), "dur": round(nxt - t, 3)})
        t = nxt
    return out

def beat_lock(beats, cuts, tol=0.07, offset=0.0, min_cuts=4):
    """How many picture cuts land on a beat, against what chance would give.

    beats: beat times in seconds (music clock). cuts: cut times in seconds (picture clock), or review.py
    cuts.json rows (only kind == "cut" counts; flashes and fast moves are not shots). offset: where the music
    starts in the picture (cut time - offset = music time). Chance is the share of the cut span that lies within
    tol of some beat, so a dense grid is not mistaken for a locked edit. Approach after JuneYaooo/rea-video
    (Apache-2.0), re-implemented here.
    """
    beats = sorted(float(b) for b in beats)
    times = []
    for c in cuts:
        if isinstance(c, dict):
            if c.get("kind", "cut") != "cut":
                continue
            c = c["t"]
        times.append(float(c) - offset)
    times.sort()
    res = {"cuts": len(times), "tol": tol, "on_beat": 0, "ratio": 0.0, "chance": 0.0,
           "median_offset_ms": None, "locked": False, "verdict": "not enough cuts"}
    if not beats or not times:
        res["verdict"] = "no beats" if not beats else "no cuts"
        return res
    def nearest(t):
        return min(beats, key=lambda b: abs(b - t))
    signed = [t - nearest(t) for t in times]
    on = [d for d in signed if abs(d) <= tol]
    lo, hi = times[0], times[-1]
    if hi - lo < 1e-6:
        lo, hi = beats[0], beats[-1]
    span = max(hi - lo, 1e-6)
    covered, cur_a, cur_b = 0.0, None, None
    for b in beats:
        a, z = max(b - tol, lo), min(b + tol, hi)
        if z <= a:
            continue
        if cur_b is not None and a <= cur_b:
            cur_b = max(cur_b, z)
        else:
            if cur_b is not None:
                covered += cur_b - cur_a
            cur_a, cur_b = a, z
    if cur_b is not None:
        covered += cur_b - cur_a
    chance = min(1.0, covered / span)
    ratio = len(on) / len(times)
    srt = sorted(on)
    res.update(on_beat=len(on), ratio=round(ratio, 3), chance=round(chance, 3),
               median_offset_ms=round(1000 * srt[len(srt) // 2], 1) if srt else None)
    if len(times) < min_cuts:
        return res
    res["locked"] = ratio >= 0.5 and ratio >= 1.8 * chance
    res["verdict"] = "beat-synced edit" if res["locked"] else "cuts not locked to the beat"
    return res

SYN = {
    "bright": {"root": 220.0, "chord": [1, 1.25, 1.5], "hat": 0.10},
    "dark": {"root": 110.0, "chord": [1, 1.2, 1.5], "hat": 0.07},
    "calm": {"root": 196.0, "chord": [1, 1.26, 1.68], "hat": 0.0},
}

def synth(out, bpm=120, seconds=30, mood="bright"):
    """Royalty-free synthetic bed (generated, no samples): kick on beats, hats on off-beats, soft pad."""
    m = SYN.get(mood, SYN["bright"])
    b = 60 / bpm
    kick = f"0.9*sin(2*PI*(50+90*exp(-30*mod(t,{b})))*mod(t,{b}))*exp(-9*mod(t,{b}))"
    hat = f"{m['hat']}*(random(0)*2-1)*exp(-60*mod(t+{b/2},{b}))"
    pad = "+".join(f"0.06*sin(2*PI*{m['root']*k}*t)" for k in m["chord"])
    lfo = f"(0.6+0.4*sin(2*PI*t/{b*8}))"
    expr = f"({kick})+({hat})+({pad})*{lfo}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"aevalsrc='{expr}|{expr}':s=48000:d={seconds}",
                    "-af", f"afade=t=in:d=0.3,afade=t=out:st={max(0, seconds - 1.5)}:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-b:a", "192k", str(out)], check=True)
    meta = {"file": Path(out).name, "bpm": bpm, "seconds": seconds, "mood": mood, "license": "generated by Reelsmith; no third-party rights", "attribution": None}
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2))
    print(f"wrote {out} ({bpm} BPM, {seconds}s, {mood})")

def fit(track, seconds, out, grid=None):
    end = seconds
    if grid:
        g = json.loads(Path(grid).read_text())
        cands = [d for d in g["downbeats"] if d <= seconds + 0.01]
        if cands and seconds - cands[-1] < 2.5:
            end = cands[-1] + (seconds - cands[-1])  # keep length; fade lands after last bar line
    fade = min(2.0, max(0.5, seconds * 0.08))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(track), "-map", "0:a:0", "-vn", "-map_metadata", "-1", "-t", f"{end:.3f}",
                    "-af", f"afade=t=in:d=0.05,afade=t=out:st={end - fade:.3f}:d={fade:.3f}",
                    "-ar", "48000", "-b:a", "192k", str(out)], check=True)
    print(f"wrote {out} ({end:.2f}s, {fade:.1f}s fade)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("grid"); p.add_argument("track"); p.add_argument("-o", "--out"); p.add_argument("--bpm", type=float); p.add_argument("--engine", default="auto", choices=["auto", "librosa", "hyperframes", "fixed"])
    p = sp.add_parser("snap"); p.add_argument("grid"); p.add_argument("--durations", required=True); p.add_argument("--unit", default="bar", choices=["bar", "beat", "half"])
    p = sp.add_parser("synth"); p.add_argument("-o", "--out", required=True); p.add_argument("--bpm", type=float, default=120); p.add_argument("--seconds", type=float, default=30); p.add_argument("--mood", default="bright")
    p = sp.add_parser("fit"); p.add_argument("track"); p.add_argument("--seconds", type=float, required=True); p.add_argument("-o", "--out", required=True); p.add_argument("--grid")
    p = sp.add_parser("lock"); p.add_argument("grid"); p.add_argument("cuts"); p.add_argument("--tol", type=float, default=0.07); p.add_argument("--offset", type=float, default=0.0)
    a = ap.parse_args()
    if a.cmd == "grid":
        g = make_grid(a.track, a.bpm, a.engine)
        g["source"] = Path(a.track).name
        out = a.out or str(Path(a.track).with_suffix(".beatgrid.json"))
        Path(out).write_text(json.dumps(g, indent=1))
        print(f"{g['engine']}: {g['bpm']} BPM, {len(g['beats'])} beats, {len(g['downbeats'])} bars, {len(g['sections'])} sections -> {out}")
    elif a.cmd == "snap":
        print(json.dumps(snap(json.loads(Path(a.grid).read_text()), [float(x) for x in a.durations.split(",")], a.unit), indent=1))
    elif a.cmd == "synth":
        synth(a.out, a.bpm, a.seconds, a.mood)
    elif a.cmd == "fit":
        fit(a.track, a.seconds, a.out, a.grid)
    elif a.cmd == "lock":
        r = beat_lock(json.loads(Path(a.grid).read_text())["beats"], json.loads(Path(a.cuts).read_text()), a.tol, a.offset)
        print(json.dumps(r, indent=1))
        print(f"{r['on_beat']}/{r['cuts']} cuts within {int(a.tol * 1000)} ms of a beat ({r['ratio']:.0%}; chance {r['chance']:.0%}): {r['verdict']}")

if __name__ == "__main__":
    main()
