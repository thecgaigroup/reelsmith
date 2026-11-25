"""Plan local SFX from cuts and motion, then duck the stem under programme audio."""
import csv
import hashlib
import io
import json
import re
import subprocess
import wave
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "sfx"
SR = 48000
DURATIONS = {"click": 0.035, "latch": 0.125, "whoosh": 0.55, "riser": 1.2, "impact": 1.6}
LICENSE = "CC0-1.0"
LOCAL_PROTOCOLS = ("-protocol_whitelist", "file,pipe")


@dataclass(frozen=True)
class Sound:
    file: str
    sha256: str
    samples: np.ndarray


@dataclass(frozen=True)
class Cue:
    sound: str
    time: float
    gain_db: float


def load_sounds(directory=ASSET_DIR):
    """Validate and decode the same bytes so a changed file cannot enter the mix."""
    records = json.loads((directory / "manifest.json").read_text())["sounds"]
    expected = {f"cgai_{key}_v1.wav": key for key in DURATIONS}
    if sorted(record["file"] for record in records) != sorted(expected):
        raise ValueError("SFX manifest must list exactly the five bundled sounds")
    sounds = {}
    for record in records:
        name = record["file"]
        if record["license"] != LICENSE:
            raise ValueError(f"{name}: license must be {LICENSE}")
        data = (directory / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != record["sha256"]:
            raise ValueError(f"{name}: sha256 mismatch")
        key = expected[name]
        with wave.open(io.BytesIO(data)) as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) != (
                1, 2, SR, round(DURATIONS[key] * SR)
            ):
                raise ValueError(f"{name}: unexpected WAV format or duration")
            samples = np.frombuffer(wav.readframes(wav.getnframes()), "<i2") / 32767.0
        sounds[key] = Sound(name, digest, samples)
    return sounds


def plan_cues(duration, cuts, motion):
    """Use timed [seconds, motion strength] events in chronological order."""
    tail = [event for event in motion if event[0] >= duration * 0.88]
    impact = max(tail, key=lambda event: event[1])[0] if tail else (
        cuts[-1][0] if cuts else max(0, duration - 3)
    )
    strongest = {t for t, _ in sorted(cuts, key=lambda event: -event[1])[:2]}
    cues = []
    for t, _ in cuts:
        if abs(t - impact) < 0.5:
            continue
        if t in strongest:
            cues.append(Cue("riser", round(t - DURATIONS["riser"] * 0.98, 3), -6.0))
        else:
            cues.append(Cue("whoosh", round(t - DURATIONS["whoosh"] * 0.62, 3), -4.0))
    threshold = np.percentile([strength for _, strength in motion], 75) if motion else 0
    budget = Counter()
    for t, strength in motion:
        window = int(t // 10)
        if abs(t - impact) < 0.6 or t > duration - 0.5 or budget[window] >= 3:
            continue
        budget[window] += 1
        cues.append(Cue("latch", round(t, 3), -10.0) if strength > threshold else
                    Cue("click", round(t, 3), -11.0))
    cues.append(Cue("impact", round(impact, 3), -7.0))
    return sorted(cues, key=lambda cue: cue.time)


def local_file(path):
    raw = str(path)
    resolved = Path(path).expanduser().resolve()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw) or not resolved.is_file():
        raise ValueError(f"{raw}: expected an existing local regular file")
    return resolved


def ffmpeg_command(*args):
    command = ["ffmpeg", "-nostdin"]
    for arg in args:
        if arg == "-i":
            command.extend(LOCAL_PROTOCOLS)
        command.append(str(arg))
    return command


def ffmpeg(*args, cwd=None):
    result = subprocess.run(ffmpeg_command(*args), capture_output=True, cwd=cwd)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    return result


def cut_times(video, scenes=None):
    if scenes:
        with local_file(scenes).open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
        if not rows or not any(field.strip() for field in rows[0]):
            raise ValueError(f"{scenes}: scene CSV needs a non-blank first row")
        if rows[0][0] == "Timecode List:":
            return [sum(float(x) * unit for x, unit in zip(t.split(":"), (3600, 60, 1)))
                    for t in rows[0][1:] if t]
        header = rows[0].index("Start Time (seconds)")
        return [float(row[header]) for row in rows[2:] if row]
    result = ffmpeg("-hide_banner", "-nostats", "-i", local_file(video),
                    "-vf", "setpts=PTS-STARTPTS,scdet=threshold=10:sc_pass=1,metadata=print", "-an", "-f", "null", "-")
    return [float(t) for t in re.findall(rb"lavfi\.scd\.time=([\d.]+)", result.stderr)]


def motion_deltas(video):
    size = 136 * 240
    command = ffmpeg_command("-v", "error", "-i", local_file(video), "-map", "0:v:0",
                             "-vf", "scale=136:240:flags=area,format=gray",
                             "-fps_mode", "passthrough", "-f", "rawvideo", "-")
    deltas = [0.0]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder:
        previous = decoder.stdout.read(size)
        if len(previous) != size:
            raise ValueError("cannot decode motion analysis frames")
        previous = np.frombuffer(previous, np.uint8).astype(np.int16)
        while frame := decoder.stdout.read(size):
            if len(frame) != size:
                raise ValueError("incomplete motion analysis frame")
            current = np.frombuffer(frame, np.uint8).astype(np.int16)
            deltas.append(float(np.abs(current - previous).mean()))
            previous = current
        if decoder.wait():
            raise ValueError("motion analysis decode failed")
    return deltas


def frame_times(video):
    source = local_file(video)
    result = subprocess.run(
        ["ffprobe", "-v", "error", *LOCAL_PROTOCOLS, "-select_streams", "v:0",
         "-show_entries", "stream=start_time:frame=best_effort_timestamp_time,pts_time,pkt_pts_time",
         "-of", "json", str(source)], capture_output=True, text=True,
    )
    if result.returncode:
        raise ValueError(f"cannot read video frame timestamps: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    try:
        start = float(data["streams"][0]["start_time"])
        times = [next(float(frame[key]) for key in ("best_effort_timestamp_time", "pts_time", "pkt_pts_time")
                      if frame.get(key) not in (None, "N/A")) - start for frame in data.get("frames", [])]
    except (IndexError, KeyError, StopIteration, ValueError) as error:
        raise ValueError("motion analysis needs a presentation timestamp for every video frame") from error
    if not np.isfinite(times).all() or any(a > b for a, b in zip(times, times[1:])):
        raise ValueError("motion analysis needs video timestamps in presentation order")
    return times


def cue_events(video, duration, fps, scenes=None):
    # CSV and scene-detector cut times are already relative to picture start.
    cuts = [t for t in cut_times(video, scenes) if 0 < t < duration]
    delta = motion_deltas(video)
    times = frame_times(video)
    if len(times) != len(delta):
        raise ValueError(f"motion analysis decoded {len(delta)} frames but found {len(times)} frame timestamps")

    def cut_strength(t):
        right = min(bisect_left(times, t), len(times) - 1)
        left = max(0, right - 1)
        return delta[left if t - times[left] <= times[right] - t else right]

    threshold = max(0.25, (np.median(delta) + 1e-3) * 3)
    motion = []
    for i, strength in enumerate(delta[1:-1], start=1):
        t = times[i]
        if strength <= threshold or strength < delta[i - 1] or strength <= delta[i + 1]:
            continue
        if delta[i - 1] >= strength * 0.85 or any(abs(t - c) < 0.45 for c in cuts):
            continue
        if motion and round(t - motion[-1][0], 6) < 0.9:
            if strength > motion[-1][1]:
                motion[-1] = [t, strength]
        else:
            motion.append([t, strength])
    return {"duration": duration, "cuts": [[t, cut_strength(t)] for t in cuts], "motion": motion}


def render_stem(path, duration, cue_path, sounds, *, picture_duration, offset=0):
    stem = np.zeros(round(duration * SR), dtype=np.float32)
    rendered, skipped = [], []
    for record in json.loads(local_file(cue_path).read_text())["cues"]:
        cue = Cue(**record)
        # A lead-in planned for an opening cut can start at the first frame.
        cue_start = round((max(0, cue.time) + offset) * SR)
        samples = sounds[cue.sound].samples
        end = cue_start + len(samples)
        if cue.time >= picture_duration or cue_start < 0 or end > len(stem):
            skipped.append(record)
            continue
        stem[cue_start:end] += samples * 10 ** (cue.gain_db / 20)
        rendered.append(record)
    # Float PCM keeps overlapping hits intact before the single mastering stage.
    stem.astype("<f4").tofile(path)
    return rendered, skipped


DUCK_GRAPH = (
    "[0:a:0]asetpts=PTS-STARTPTS,aresample=48000:first_pts=0,aformat=channel_layouts=stereo,apad,asplit[prog][key];"
    "[1:a:0]pan=stereo|c0=c0|c1=c0[sfx];"
    "[sfx][key]sidechaincompress=threshold=0.125:ratio=2:attack=10:release=250:makeup=1[duck];"
    "[prog][duck]amix=inputs=2:normalize=0:duration=first[mix]"
)


def premix(video, stem, out, has_audio, duration, *, programme_delay=0):
    raw = ["-f", "f32le", "-ar", SR, "-ac", 1, "-i", local_file(stem)]
    graph = DUCK_GRAPH
    if programme_delay:
        graph = graph.replace("apad,asplit", f"adelay={round(programme_delay * SR)}S:all=1,apad,asplit")
    args = ["-i", local_file(video), *raw, "-filter_complex", graph, "-map", "[mix]"] if has_audio else raw
    ffmpeg("-v", "error", "-y", *args, "-t", f"{duration:.9f}", "-ac", 2, "-c:a", "pcm_f32le", out)


def loudness(path, audio_index=0):
    result = ffmpeg("-hide_banner", "-nostats", "-i", local_file(path), "-map", f"0:a:{audio_index}",
                    "-af", "ebur128=peak=true", "-f", "null", "-")
    summary = result.stderr.decode().rsplit("Summary:", 1)[-1]
    stats = {}
    for label, key in (("I", "I_LUFS"), ("LRA", "LRA_LU"), ("Peak", "TP_dBTP")):
        match = re.search(rf"{label}:\s+(-?[\d.]+|-inf)", summary)
        if not match:
            raise ValueError(f"FFmpeg did not report {label} for {path}")
        value = float(match[1])
        stats[key] = value if np.isfinite(value) else None
    return stats


def mastering_filter(gain, ceiling):
    return (f"volume={gain:.4f}dB,aresample=192000,"
            f"alimiter=limit={10 ** (ceiling / 20):.8f}:attack=1:release=50:level=0:latency=1,aresample=48000")
