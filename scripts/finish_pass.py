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
AUDIO_DURATION_TOLERANCE = 1024 / 48000 + 0.002


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
    return {
        "width": video["width"], "height": video["height"],
        "duration": float(video.get("duration", data["format"].get("duration", 0))),
        "frames": int(frames),
        "fps": Fraction(video["r_frame_rate"]),
        "video_start": stream_start(video),
        "format_duration": float(data["format"]["duration"]),
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


def stream_offsets(info):
    """Place the first presentation of either stream at zero."""
    video = info["video_start"]
    audio = stream_start(info["audio"])
    if video is None or (info["audio"] and audio is None):
        raise ValueError("finish pass needs known stream start timestamps")
    if audio is None:
        return 0.0, 0.0
    origin = min(video, audio)
    return video - origin, audio - origin


def mix_duration(info, starts):
    length = info["duration"]
    video_start, audio_start = starts
    audio_length = (info["audio"] or {}).get("duration")
    # A full-length staggered programme can include one AAC priming frame.
    if video_start != audio_start and audio_length not in (None, "N/A"):
        if abs(float(audio_length) - length) <= AUDIO_DURATION_TOLERANCE:
            return float(audio_length)
    picture_end = video_start + length
    return picture_end - audio_start if picture_end > audio_start else length


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


def encode_audio(premix_path, target, gain, ceiling, *, trim=0, duration=None):
    from sfx_cues import mastering_filter

    audio_filter = mastering_filter(gain, ceiling)
    if trim:
        audio_filter += f",atrim=start={trim:.9f},asetpts=PTS-STARTPTS"
    limit = ["-t", f"{duration:.9f}"] if duration is not None else []
    ffmpeg("-v", "error", "-y", "-i", premix_path, "-af", audio_filter,
           "-c:a", "aac", "-b:a", "256k", "-ar", "48000", *limit, target)


def without_priming(encoded):
    # Away from zero, MP4 would otherwise present the AAC priming packet.
    trimmed = encoded.with_name(f"{encoded.stem}-without-priming.m4a")
    ffmpeg("-v", "error", "-y", "-i", encoded, "-ss", 0, "-c:a", "copy", trimmed)
    return trimmed


def master(picture, premix_path, output, before, starts):
    from sfx_cues import loudness, mastering_filter

    gain = -14 - before["I_LUFS"]
    ceiling = -1.45
    video_start, audio_start = starts
    best = None
    saved = output.with_name("best.mp4")
    previous_error = None
    # Each attempt starts from the unmastered mix. The video is stream-copied.
    for attempt in range(1, 11):
        encode = ["-af", mastering_filter(gain, ceiling), "-c:a", "aac",
                  "-b:a", "256k", "-ar", "48000"]
        audio_input = premix_path
        if audio_start:
            encoded = premix_path.with_name("encoded.m4a")
            encode_audio(premix_path, encoded, gain, ceiling)
            audio_input = without_priming(encoded)
            encode = ["-c:a", "copy"]
        ffmpeg("-v", "error", "-y", "-copyts",
               "-itsoffset", f"{video_start:.9f}", "-i", picture,
               "-itsoffset", f"{audio_start:.9f}", "-i", audio_input, "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", *encode, "-movflags", "+faststart", output)
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


def retain_programme_start(candidate, premix_path, mastering, audio_start, duration):
    """Keep the source-aligned track first and select the complete mix by default."""
    aligned = candidate.with_name("aligned.m4a")
    encode_audio(premix_path, aligned, mastering["static_gain_db"], mastering["limiter_ceiling_db"],
                 trim=audio_start, duration=duration)
    combined = candidate.with_name("combined.mp4")
    audio_input = without_priming(aligned) if audio_start else aligned
    ffmpeg("-v", "error", "-y", "-copyts", "-i", candidate, "-itsoffset", f"{audio_start:.9f}",
           "-i", audio_input, "-map", "0:v:0", "-map", "1:a:0", "-map", "0:a:0",
           "-disposition:a:0", "0", "-disposition:a:1", "default",
           "-c", "copy", "-movflags", "+faststart", combined)
    combined.replace(candidate)


def measure(out, reference, *, mix_start=None, mix_length=None):
    from sfx_cues import loudness

    source, result = probe(reference), probe(out)
    source_starts, result_starts = stream_offsets(source), stream_offsets(result)
    source_offset, result_offset = (video - audio for video, audio in (source_starts, result_starts))
    tracks = result["audio_tracks"]
    mix_index = next((i for i, track in enumerate(tracks) if track["disposition"]["default"]), 0)
    mix = tracks[mix_index] if tracks else None
    stats = loudness(out, mix_index) if mix else None
    audio_ok = bool(stats and audio_passes(stats) and mix["codec_name"] == "aac"
                    and mix["sample_rate"] == "48000")
    # MP4 edits and AAC framing can quantize the normalized starts and audio length.
    start_tolerance = 0.002
    duration_tolerance = AUDIO_DURATION_TOLERANCE
    expected_audio_length = mix_duration(source, source_starts)
    mix_start = source_starts[1] if mix_start is None else mix_start
    mix_length = expected_audio_length if mix_length is None else mix_length
    if mix_index == 0:
        expected_audio_length = mix_length
    expected_end = max(source_starts[0] + source["duration"], source_starts[1] + expected_audio_length)
    expected_end = max(expected_end, mix_start + mix_length)
    sync_ok = bool(result["audio"]) and abs(source_starts[0] - result_starts[0]) <= start_tolerance
    if source["audio"] and result["audio"]:
        sync_ok = (sync_ok and abs(source_offset - result_offset) <= start_tolerance and
                   abs(source_starts[1] - result_starts[1]) <= start_tolerance)
    if result["audio"]:
        result_audio_length = result["audio"].get("duration")
        if result_audio_length not in (None, "N/A"):
            sync_ok = sync_ok and abs(expected_audio_length - float(result_audio_length)) <= duration_tolerance
    if mix:
        sync_ok = (sync_ok and abs(stream_start(mix) - mix_start) <= start_tolerance and
                   abs(float(mix["duration"]) - mix_length) <= duration_tolerance)

    source_size, result_size = ([item["width"], item["height"]] for item in (source, result))
    timing = {
        "source_video_start": source["video_start"], "output_video_start": result["video_start"],
        "source_audio_start": stream_start(source["audio"]), "output_audio_start": stream_start(result["audio"]),
        "mix_audio_start": stream_start(mix),
        "source_av_offset": source_offset if source["audio"] else None,
        "output_av_offset": result_offset if result["audio"] else None,
        "source_frames": source["frames"], "output_frames": result["frames"],
        "source_seconds": source["duration"], "output_seconds": result["duration"],
        "source_container_seconds": source["format_duration"], "output_container_seconds": result["format_duration"],
        "source_fps": str(source["fps"]), "output_fps": str(result["fps"]),
        "source_size": source_size, "output_size": result_size,
        "pass": (sync_ok and source_size == result_size and source["fps"] == result["fps"] and
                 source["frames"] == result["frames"] and abs(source["duration"] - result["duration"]) < 0.001 and
                 abs(expected_end - result["format_duration"]) <= duration_tolerance),
    }
    return {"loudness": {"after": stats, "pass": audio_ok}, "timing": timing,
            "pass": audio_ok and timing["pass"]}


def check(out, reference):
    from sfx_cues import local_file

    out, reference = local_file(out), local_file(reference)
    metadata = sidecar(out)
    if not metadata.is_file():
        return {"artifact": {"pass": False, "error": "missing finish report"}, "pass": False}
    recorded = json.loads(metadata.read_text())
    artifact = verify_artifact(out, recorded)
    if not artifact["pass"]:
        return {"artifact": artifact, "pass": False}
    rendered = Counter(cue["sound"] for cue in recorded.get("cues_rendered", []))
    counts = {name: rendered[name] for name in recorded["cue_counts"]}
    cues_ok = counts == recorded["cue_counts"] and sum(counts.values()) == sum(rendered.values())
    result = measure(out, reference, **recorded.get("mix_timeline", {}))
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

    from sfx_cues import SR, cue_events, load_sounds, local_file, loudness, plan_cues, premix, render_stem

    video, out = local_file(video), Path(out).resolve()
    scenes = local_file(scenes) if scenes else None
    layout = local_file(layout) if layout else None
    if {out, sidecar(out).resolve()} & {video, scenes, layout}:
        raise ValueError("output paths must differ from input paths")
    info = probe(video)
    width, height = info["width"], info["height"]
    if min(width, height) < 8 or width % 2 or height % 2 or not info["fps"] or not info["duration"] > 0:
        raise ValueError("finish pass needs even video dimensions and a valid frame rate and duration")
    if info["duration"] < 1.0:
        raise ValueError("finish pass needs at least 1.0 s of picture")
    starts = stream_offsets(info)
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
        cue_path = work / "cues.json"
        planned = [asdict(cue) for cue in cues]
        cue_path.write_text(json.dumps({"cues": planned}))
        video_start, audio_start = starts
        duration = info["duration"]
        in_picture = [cue for cue in cues if cue.time < duration]
        early = any(video_start + max(0, cue.time) < audio_start for cue in in_picture)
        mix_start = min(starts) if early else audio_start
        cue_offset = video_start - mix_start
        programme_length = mix_duration(info, starts)
        programme_end = audio_start - mix_start + programme_length
        picture_end = duration + cue_offset
        cue_ends = (round((max(0, cue.time) + cue_offset) * SR) + len(sounds[cue.sound].samples)
                    for cue in in_picture)
        mix_length = max(round(max(programme_end, picture_end) * SR), max(cue_ends, default=0)) / SR
        rendered, skipped = render_stem(stem, mix_length, cue_path, sounds,
                                        picture_duration=duration, offset=cue_offset)
        premix(video, stem, mix, bool(info["audio"]), mix_length, programme_delay=audio_start - mix_start)
        before = loudness(mix)
        if before["I_LUFS"] is None or before["I_LUFS"] <= -70:
            raise ValueError("cannot master a silent mix: no loudness blocks above the -70 LUFS gate")
        picture, filters = render_picture(video, work, info, title, keep_sharp)
        mastering = master(picture, mix, candidate, before, (video_start, mix_start))
        if video_start != audio_start and (early or mix_length > programme_length + 1 / SR):
            retain_programme_start(candidate, mix, mastering, audio_start, programme_length)
        mix_timeline = {"mix_start": mix_start, "mix_length": mix_length}
        report = measure(candidate, video, **mix_timeline)
        counts = Counter(cue["sound"] for cue in rendered)
        report.update({
            "artifact": artifact_identity(candidate),
            "flag": os.environ["REELSMITH_FINISH_PASS"],
            "layout": str(layout) if layout else None,
            "filters": filters,
            "mix_timeline": mix_timeline,
            "cue_counts": {name: counts[name] for name in sounds},
            "cues_planned": planned,
            "cues_rendered": rendered,
            "cues_skipped": skipped,
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
    except (ValueError, KeyError, TypeError, OSError, ImportError) as error:
        print(f"finish pass: {error}", file=sys.stderr)
        return 1
    if report is not None:
        print(json.dumps(report, indent=2))
    return 0 if report is None or report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
