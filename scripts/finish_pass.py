#!/usr/bin/env python3
"""Finish a flat master offline, or recheck the rendered file against its source."""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

from finish_pass_flag import enabled

SCRIPTS = Path(__file__).resolve().parent
DEFAULT_LAYOUT = SCRIPTS.parent / "references" / "finish-pass-layouts" / "signal-9x16.json"
SWS = "accurate_rnd+full_chroma_int"
DISABLED = "finish pass disabled (REELSMITH_FINISH_PASS not set)"
AUDIO_DURATION_TOLERANCE = 0.025


class UnsupportedInput(ValueError):
    def __init__(self, reason):
        super().__init__(f"finish pass supports CFR, aligned A/V only: {reason}")


@dataclass(frozen=True)
class Rect:
    """Half-open pixel coordinates."""
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self):
        return self.x1 - self.x0

    @property
    def height(self):
        return self.y1 - self.y0

    def filter(self):
        return f"crop={self.width}:{self.height}:{self.x0}:{self.y0}:exact=1"


def layout_rect(bounds, width, height, name):
    if len(bounds) != 4 or any(type(n) not in (int, float) or not 0 <= n <= 1 for n in bounds):
        raise ValueError(f"{name} region needs four fractions between zero and one")
    x0, y0, x1, y1 = bounds
    if x0 >= x1 or y0 >= y1:
        raise ValueError(f"{name} region needs positive width and height")
    return Rect(math.floor(x0 * width), math.floor(y0 * height),
                math.ceil(x1 * width), math.ceil(y1 * height))


def layout_regions(path, width, height):
    regions = json.loads(path.read_text())["regions"]
    title = layout_rect(regions["title"], width, height, "title")
    keep_sharp = [layout_rect(bounds, width, height, "keep_sharp")
                  for bounds in regions.get("keep_sharp", [])]
    return title, keep_sharp


def ffmpeg(*args, **kwargs):
    # OFF CLI and flag-only callers can run without NumPy.
    from sfx_cues import ffmpeg as invoke

    return invoke(*args, **kwargs)


def probe(path):
    from sfx_cues import LOCAL_PROTOCOLS, local_file

    path = local_file(path)
    command = ["ffprobe", "-v", "error", *LOCAL_PROTOCOLS]
    result = subprocess.run([*command, "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip())
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if not video:
        raise ValueError(f"{path}: no video stream")
    frames = video.get("nb_frames", "")
    if not frames.isdigit():
        counted = subprocess.run([*command, "-count_frames", "-select_streams", "v:0",
                                  "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
                                 capture_output=True, text=True)
        frames = counted.stdout.strip()
        if counted.returncode or not frames.isdigit():
            raise ValueError(f"{path}: could not count video frames")
    fps = video["r_frame_rate"]
    fps = Fraction(fps) if fps != "0/0" else Fraction(0)
    video_duration = video.get("duration", "N/A")
    duration = (int(frames) / float(fps) if fps else 0) if video_duration == "N/A" else float(video_duration)
    format_duration = data["format"].get("duration", "N/A")
    return {
        "width": video["width"], "height": video["height"],
        "duration": duration,
        "frames": int(frames),
        "fps": fps,
        "avg_fps": video["avg_frame_rate"],
        "time_base": video["time_base"],
        "video_start": stream_start(video),
        "format_duration": duration if format_duration == "N/A" else float(format_duration),
        "audio": next((s for s in data["streams"] if s["codec_type"] == "audio"), None),
        "audio_tracks": [s for s in data["streams"] if s["codec_type"] == "audio"],
        "matrix": {"bt709": "bt709", "bt470bg": "bt601", "smpte170m": "bt601",
                   "smpte240m": "smpte240m", "bt2020nc": "bt2020"}.get(
                       video.get("color_space"), "bt601"),
        "color_tags": {k: video[k] for k in ("color_space", "color_transfer", "color_primaries")
                       if video.get(k) not in (None, "unknown")},
        "sar": video.get("sample_aspect_ratio", "1:1"),
    }


def stream_start(stream):
    start = (stream or {}).get("start_time", "N/A")
    return None if start == "N/A" else float(start)


def require_supported_input(info, ticks):
    fps = info["fps"]
    if fps <= 0 or info["avg_fps"] == "0/0":
        raise UnsupportedInput("unknown frame rate")
    if fps != Fraction(info["avg_fps"]):
        raise UnsupportedInput("variable frame rate")
    if not ticks or len(ticks) != info["frames"] or not all(type(tick) is int for tick in ticks):
        raise UnsupportedInput("missing frame presentation timestamps")
    frame_ticks = 1 / (fps * Fraction(info["time_base"]))
    if frame_ticks.denominator != 1:
        # Floor/ceil deltas must follow one rounding phase across the clip.
        # The residuals from the exact cadence can span at most one tick.
        numerator, denominator = frame_ticks.numerator, frame_ticks.denominator
        residuals = [tick * denominator - index * numerator for index, tick in enumerate(ticks)]
        low, high = min(residuals), max(residuals)
        # Ties-to-even (possibly shifted by a stream offset) use one parity.
        rounded_cfr = high - low < denominator or (
            high - low == denominator and
            len({tick % 2 for tick, residual in zip(ticks, residuals) if residual in (low, high)}) == 1)
        constant_rate = rounded_cfr and all(a < b for a, b in zip(ticks, ticks[1:]))
    else:
        constant_rate = all(b - a == frame_ticks for a, b in zip(ticks, ticks[1:]))
    if not constant_rate:
        raise UnsupportedInput("variable frame rate")
    if info["audio"]:
        frame_duration = 1 / float(fps)
        video, audio = info["video_start"], stream_start(info["audio"])
        if video is None or audio is None or not all(map(math.isfinite, (video, audio))):
            raise UnsupportedInput("unknown audio or video start")
        delta = audio - video
        # ffprobe reports starts rounded to microseconds.
        if abs(delta) > frame_duration + 0.000001:
            first, last = ("audio", "video") if delta < 0 else ("video", "audio")
            raise UnsupportedInput(f"{last} starts {abs(delta):.6f} s after {first}")


def write_mask(path, outer, inner):
    import numpy as np

    def ramp(positions, start, end, low, high):
        # Pixel-centre distances feather only the padding around the preserved region.
        a = np.clip((positions - start) / max(1, low - start), 0, 1) if low > start else np.ones_like(positions)
        b = np.clip((end - positions) / max(1, end - high), 0, 1) if high < end else np.ones_like(positions)
        m = np.minimum(a, b)
        return m * m * (3 - 2 * m)

    x = np.arange(outer.x0, outer.x1) + 0.5
    y = np.arange(outer.y0, outer.y1) + 0.5
    alpha = np.rint(255 * np.outer(ramp(y, outer.y0, outer.y1, inner.y0, inner.y1),
                                   ramp(x, outer.x0, outer.x1, inner.x0, inner.x1)))
    path.write_bytes(f"P5\n{outer.width} {outer.height}\n255\n".encode() + alpha.astype("uint8").tobytes())


def bloom_key(path):
    """Make a colour-preserving key, with lower thresholds for saturated highlights."""
    import numpy as np

    b, g, r = np.meshgrid(*([np.linspace(0, 1, 17)] * 3), indexing="ij")
    # In a .cube table red varies fastest, then green, then blue.
    rgb = np.stack((r, g, b), axis=-1).reshape(-1, 3)
    high, low = rgb.max(axis=1), rgb.min(axis=1)
    saturation = (high - low) / np.maximum(high, 1e-6)
    luminance = rgb @ [0.2126, 0.7152, 0.0722]
    key = np.clip((luminance + 0.24 * saturation - 0.53) / 0.34, 0, 1)
    colors = rgb * (key ** 2 * (3 - 2 * key))[:, None]
    with path.open("w") as handle:
        handle.write("LUT_3D_SIZE 17\n")
        np.savetxt(handle, colors, fmt="%.6f")


def video_graph(width, height, title, work, matrix, keep_sharp=()):
    start = "[0:v:0]setpts=PTS-STARTPTS"
    if title is None:
        return start + ",format=yuv420p[v]", []

    def scale(w, h, method):
        return f"scale={w}:{h}:flags={method}+{SWS}"

    amount = max(6, math.ceil(width * 0.02))

    def padded(rect):
        return Rect(max(0, rect.x0 - amount), max(0, rect.y0 - amount),
                    min(width, rect.x1 + amount), min(height, rect.y1 + amount))

    outer = padded(title)
    mask = work / "focus.pgm"
    write_mask(mask, outer, title)
    bloom_key(work / "bloom-key.cube")
    soft = max(1.4, width * 0.006)
    tight = max(1, width * 0.0045)
    wide = max(1, width * 0.018 / 4)
    # Work in 4:4:4 for the crops and composites.
    inputs = ["-i", mask]
    sharp_streams = "".join(f"[keep{i}]" for i in range(len(keep_sharp)))
    graph = [
        f"sws_flags={SWS}",
        start + f",format=yuv444p,split={2 + len(keep_sharp)}[bg][title]{sharp_streams}",
        f"[bg]gblur=sigma={soft:.2f}:steps=2[blurred]",
    ]
    background = "blurred"
    for i, rect in enumerate(keep_sharp):
        keep_outer = padded(rect)
        mask = work / f"keep-{i}.pgm"
        write_mask(mask, keep_outer, rect)
        inputs.extend(["-i", mask])
        graph.extend([
            f"[keep{i}]{keep_outer.filter()}[crop{i}]",
            f"[crop{i}][{i + 2}:v:0]alphamerge[sharp{i}]",
            f"[{background}][sharp{i}]overlay={keep_outer.x0}:{keep_outer.y0}:format=yuv444[restored{i}]",
        ])
        background = f"restored{i}"
    graph.extend([
        f"[title]{outer.filter()},scale=in_color_matrix={matrix}:flags={SWS},format=gbrp,split[sharp][highlights]",
        "[highlights]lut3d=file=bloom-key.cube:interp=tetrahedral,split[tight][wide]",
        f"[tight]gblur=sigma={tight:.2f}:steps=2[inner]",
        f"[wide]{scale(max(2, outer.width//4), max(2, outer.height//4), 'area')},"
        f"gblur=sigma={wide:.2f}:steps=2,{scale(outer.width, outer.height, 'bicubic')}[halo]",
        "[sharp][inner]blend=all_mode=screen:all_opacity=0.19[glow]",
        f"[glow][halo]blend=all_mode=screen:all_opacity=0.15,scale=out_color_matrix={matrix}:"
        f"out_range=tv:flags={SWS},format=yuv444p[bloom]",
        "[bloom][1:v:0]alphamerge[focus]",
        f"[{background}][focus]overlay={outer.x0}:{outer.y0}:format=yuv444,format=yuv420p[v]",
    ])
    return ";".join(graph), inputs


def layout_path(info, custom=None):
    if custom:
        from sfx_cues import local_file

        return local_file(custom)
    display_ratio = Fraction(info["width"], info["height"])
    if ":" in info["sar"]:
        display_ratio *= Fraction(info["sar"].replace(":", "/"))
    return DEFAULT_LAYOUT if abs(display_ratio - Fraction(9, 16)) < 0.005 else None


def sidecar(out):
    return Path(f"{out}.finish") / "report.json"


def artifact_identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"sha256": digest.hexdigest(), "size_bytes": size}


def verify_artifact(path, recorded):
    expected = recorded.get("artifact")
    return {"expected": expected, "pass": expected is not None and artifact_identity(path) == expected}


def audio_passes(stats):
    peak = stats["TP_dBTP"]
    level = stats["I_LUFS"]
    return level is not None and abs(level + 14) <= 0.5 and peak is not None and peak <= -1.0


def master(picture, premix_path, output, before):
    from sfx_cues import loudness, mastering_filter

    gain = -14 - before["I_LUFS"]
    ceiling = -1.45
    best = None
    saved = output.with_name("best.mp4")
    previous_error = None
    # Each attempt starts from the unmastered mix. The video is stream-copied.
    for attempt in range(1, 11):
        encode = ["-af", mastering_filter(gain, ceiling), "-c:a", "aac",
                  "-b:a", "256k", "-ar", "48000"]
        ffmpeg("-v", "error", "-y", "-copyts", "-i", picture, "-i", premix_path,
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", *encode, "-movflags", "+faststart", output)
        measured = loudness(output)
        level = measured["I_LUFS"]
        error = -14 - level if level is not None else 56.0
        peak = measured["TP_dBTP"]
        passes = audio_passes(measured)
        settings = {"static_gain_db": round(gain, 4), "limiter_ceiling_db": round(ceiling, 4)}
        if passes and abs(error) <= 0.2 + 1e-9:
            return {"attempts": attempt, **settings}
        overshoot = max(0, peak + 1) if peak is not None else math.inf
        score = (not passes, abs(error) + overshoot)
        if best is None or score < best[0]:
            best = score, measured, settings
            if passes:
                output.replace(saved)
        if 0 < overshoot < math.inf:
            ceiling -= peak + 1.2
        # Dampen reversals. On a limiter plateau, a larger positive step can
        # lift quiet passages whose peaks are still below the limiter ceiling.
        if previous_error is not None and error * previous_error < 0:
            gain += error * 0.5
        elif previous_error is not None and error > 0 and previous_error - error < 0.25:
            gain += max(2, error)
        else:
            gain += error
        previous_error = error
    if saved.exists():
        saved.replace(output)
        return {"attempts": attempt, **best[2]}
    level, peak = best[1]["I_LUFS"], best[1]["TP_dBTP"]
    raise ValueError(f"cannot reach encoded loudness target after {attempt} attempts "
                     f"(best: {level} LUFS, {peak} dBTP)")


def measure(out, reference):
    from sfx_cues import loudness

    source, result = probe(reference), probe(out)
    track_count = len(result["audio_tracks"])
    mix = result["audio"]
    stats = loudness(out) if track_count == 1 else None
    audio_ok = bool(stats and audio_passes(stats) and mix["codec_name"] == "aac"
                    and mix["sample_rate"] == "48000")
    source_audio_start = stream_start(source["audio"])
    output_audio_start = stream_start(mix)
    audio_duration = (mix or {}).get("duration", "N/A")
    output_audio_length = None if audio_duration == "N/A" else float(audio_duration)
    sync_ok = (track_count == 1 and output_audio_start is not None and result["video_start"] is not None
               and abs(output_audio_start) <= 0.002 and abs(result["video_start"]) <= 0.002
               and output_audio_length is not None
               and abs(output_audio_length - source["duration"]) <= AUDIO_DURATION_TOLERANCE)
    duration_ok = (abs(result["duration"] - source["duration"]) <= 0.000001 and
                   result["format_duration"] <= source["format_duration"] + AUDIO_DURATION_TOLERANCE)

    source_size, result_size = ([item["width"], item["height"]] for item in (source, result))
    timing = {
        "source_video_start": source["video_start"], "output_video_start": result["video_start"],
        "source_audio_start": source_audio_start, "output_audio_start": output_audio_start,
        "source_av_offset": source["video_start"] - source_audio_start if source_audio_start is not None else None,
        "output_av_offset": result["video_start"] - output_audio_start if sync_ok else None,
        "output_audio_tracks": track_count, "output_audio_seconds": output_audio_length,
        "source_frames": source["frames"], "output_frames": result["frames"],
        "source_seconds": source["duration"], "output_seconds": result["duration"],
        "source_container_seconds": source["format_duration"], "output_container_seconds": result["format_duration"],
        "source_fps": str(source["fps"]), "output_fps": str(result["fps"]),
        "source_size": source_size, "output_size": result_size,
        "pass": (sync_ok and source_size == result_size and source["fps"] == result["fps"] and
                 source["frames"] == result["frames"] and duration_ok),
    }
    return {"loudness": {"after": stats, "pass": audio_ok}, "timing": timing,
            "pass": audio_ok and timing["pass"]}


def check(out, reference):
    from sfx_cues import Cue, DURATIONS, local_file

    out, reference = local_file(out), local_file(reference)
    metadata = sidecar(out)
    if not metadata.is_file():
        return {"artifact": {"pass": False, "error": "missing finish report"}, "pass": False}
    recorded = json.loads(metadata.read_text())
    artifact = verify_artifact(out, recorded)
    if not artifact["pass"]:
        return {"artifact": artifact, "pass": False}
    planned, rendered, skipped = (
        Counter(Cue(**cue) for cue in recorded[key])
        for key in ("cues_planned", "cues_rendered", "cues_skipped")
    )
    result = measure(out, reference)
    picture_end = result["timing"]["source_seconds"]
    counts = dict.fromkeys(DURATIONS, 0)
    counts.update(Counter(cue.sound for cue in rendered.elements()))
    cues_ok = (bool(planned) and planned == rendered + skipped and all(n == 1 for n in planned.values())
               and all(cue.sound in DURATIONS and math.isfinite(cue.time) and math.isfinite(cue.gain_db)
                       for cue in planned)
               and all(cue.time < picture_end for cue in rendered)
               and all(cue.time >= picture_end for cue in skipped)
               and counts == recorded["cue_counts"])
    return {"artifact": artifact, "cue_counts": counts, "cue_counts_pass": cues_ok,
            **result, "pass": result["pass"] and cues_ok}


def render_picture(video, work, info, title, keep_sharp):
    graph, masks = video_graph(info["width"], info["height"], title, work, info["matrix"], keep_sharp)
    color_flags = {"color_space": "-colorspace", "color_transfer": "-color_trc", "color_primaries": "-color_primaries"}
    tags = [arg for name, tag in info["color_tags"].items() for arg in (color_flags[name], tag)]
    if title:
        tags += ["-color_range", "tv"]
    picture = work / "picture.mp4"
    ffmpeg("-v", "error", "-y", "-i", video, *masks, "-filter_complex_threads", 3,
           "-filter_complex", graph, "-map", "[v]", "-c:v", "libx264", "-preset", "fast",
           "-crf", 17, "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", *tags, picture, cwd=work)
    filters = sorted(set(re.findall(r"(?:^|[,;\]])([a-z0-9_]+)(?:[=\[;,]|$)", graph)) - {"sws_flags"})
    return picture, filters


def run(video, out, *, layout=None, scenes=None):
    if not enabled():
        print(DISABLED, file=sys.stderr)
        return None

    from sfx_cues import cue_events, frame_times, load_sounds, local_file, loudness, plan_cues, premix, render_stem

    video, out = local_file(video), Path(out).resolve()
    scenes = local_file(scenes) if scenes else None
    layout = local_file(layout) if layout else None
    if {out, sidecar(out).resolve()} & {video, scenes, layout}:
        raise ValueError("output paths must differ from input paths")
    info = probe(video)
    try:
        ticks = frame_times(video)
    except (ValueError, TypeError) as error:
        raise UnsupportedInput(str(error)) from error
    require_supported_input(info, ticks)
    width, height = info["width"], info["height"]
    if min(width, height) < 8 or width % 2 or height % 2 or not info["duration"] > 0:
        raise ValueError("finish pass needs even video dimensions and a valid frame rate and duration")
    if info["duration"] < 1.0:
        raise ValueError("finish pass needs at least 1.0 s of picture")
    layout = layout_path(info, layout)
    if layout is None:
        print("finish pass: no layout for this aspect, skipping title effects", file=sys.stderr)
    title, keep_sharp = layout_regions(layout, width, height) if layout else (None, [])
    sounds = load_sounds()
    cues = plan_cues(**cue_events(video, info["duration"], float(info["fps"]), scenes))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".finish-pass-", dir=out.parent) as temporary:
        work = Path(temporary)
        stem, mix, candidate = (work / name for name in ("stem.f32", "premix.wav", "finished.mp4"))
        duration = info["duration"]
        rendered, skipped = render_stem(stem, duration, cues, sounds)
        premix(video, stem, mix, bool(info["audio"]), duration)
        before = loudness(mix)
        if before["I_LUFS"] is None or before["I_LUFS"] <= -70:
            raise ValueError("cannot master a silent mix: no loudness blocks above the -70 LUFS gate")
        picture, filters = render_picture(video, work, info, title, keep_sharp)
        mastering = master(picture, mix, candidate, before)
        report = measure(candidate, video)
        counts = Counter(cue.sound for cue in rendered)
        report.update({
            "artifact": artifact_identity(candidate),
            "flag": os.environ["REELSMITH_FINISH_PASS"],
            "layout": str(layout) if layout else None,
            "filters": filters,
            "cue_counts": {name: counts[name] for name in sounds},
            "cues_planned": [asdict(cue) for cue in cues],
            "cues_rendered": [asdict(cue) for cue in rendered],
            "cues_skipped": [asdict(cue) for cue in skipped],
            "sound_sha256": {sound.file: sound.sha256 for sound in sounds.values()},
        })
        report["loudness"].update({"before": before,
                                   "source": loudness(video) if info["audio"] else None, **mastering})
        report_path = sidecar(out)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        prepared = work / "report.json"
        prepared.write_text(json.dumps(report, indent=2) + "\n")
        if not report["pass"]:
            if not out.exists():
                prepared.replace(report_path)
            raise ValueError("finish pass gates failed: " + json.dumps(report))
        previous_video = work / "previous.mp4"
        if out.is_file():
            os.link(out, previous_video)
        # Replace the media first so an interruption leaves a detectable missing
        # or mismatched identity.
        candidate.replace(out)
        try:
            prepared.replace(report_path)
        except OSError:
            if previous_video.exists():
                previous_video.replace(out)
            else:
                out.unlink()
            raise
        if not verify_artifact(out, json.loads(report_path.read_text()))["pass"]:
            raise ValueError("finished MP4 does not match finish report")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("run")
    render.add_argument("video")
    render.add_argument("--out", required=True, type=Path)
    render.add_argument("--scenes", type=Path, help="optional PySceneDetect CSV")
    render.add_argument("--layout", type=Path, help="fractional title region")
    verify = sub.add_parser("check")
    verify.add_argument("video")
    verify.add_argument("--reference", required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            report = run(args.video, args.out, layout=args.layout, scenes=args.scenes)
        else:
            report = check(args.video, args.reference)
    except UnsupportedInput as error:
        print(error, file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, OSError, ImportError) as error:
        print(f"finish pass: {error}", file=sys.stderr)
        return 1
    if report is not None:
        print(json.dumps(report, indent=2))
    return 0 if report is None or report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
