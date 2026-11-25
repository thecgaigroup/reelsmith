import json
import subprocess
import sys
from fractions import Fraction

import numpy as np
import pytest

import finish_pass as fp
import sfx_cues
from sfx_cues import loudness


def test_encoded_mp4_meets_loudness_and_peak(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "true")
    src, out = (tmp_path / name for name in ("source.mp4", "master.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x160:r=12:d=2",
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=2", "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    measured = loudness(out)
    assert report["cue_counts"]["impact"] == 1
    assert report["loudness"]["after"] == measured
    assert -14.5 <= measured["I_LUFS"] <= -13.5
    assert measured["TP_dBTP"] <= -1.0
    assert fp.probe(out)["audio"]["sample_rate"] == "48000"


@pytest.mark.parametrize("programme", ["sine=f=440:r=48000:d=3", "anullsrc=r=48000:cl=stereo:d=3"])
def test_late_cue_survives_short_programme(monkeypatch, tmp_path, programme):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out, scenes = (tmp_path / name for name in ("source.mp4", "master.mp4", "scenes.csv"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "color=s=96x96:r=12:d=9",
              "-f", "lavfi", "-i", programme, "-c:v", "libx264", "-c:a", "aac", src)
    scenes.write_text("Timecode List:,00:00:06.000\n")
    report = fp.run(src, out, scenes=scenes)
    assert report["cue_counts"]["impact"] == 1
    assert fp.check(out, src)["pass"]
    assert float(fp.probe(out)["audio"]["duration"]) == pytest.approx(9, abs=0.022)
    late = fp.ffmpeg("-v", "error", "-ss", "6", "-i", out, "-map", "0:a:0",
                     "-t", "0.5", "-f", "f32le", "-").stdout
    samples = np.frombuffer(late, "<f4")
    assert samples.size > 0
    assert np.sqrt(np.mean(samples ** 2)) > 0.01


@pytest.mark.parametrize("timestamps", [[0, 1/30, 0.1], [0, 1/30, 1/30], [0, 1/30], [0, 1/30, float("nan")]])
def test_guard_checks_timestamps_even_when_rate_metadata_agrees(timestamps):
    info = {"fps": Fraction(30), "avg_fps": "30/1", "frames": 3,
            "time_base": "1/30000", "audio": None}
    fp.require_supported_input(info, [0, 0.033333, 0.066667])
    with pytest.raises(fp.UnsupportedInput, match="variable frame rate|missing frame"):
        fp.require_supported_input(info, timestamps)


@pytest.mark.parametrize("rate", [24000, 30000, 60000])
def test_guard_allows_regular_ntsc_timestamp_rounding(rate):
    fps = Fraction(rate, 1001)
    info = {"fps": fps, "avg_fps": str(fps), "frames": 121,
            "time_base": "1/1000", "audio": None}
    ticks_per_frame = 1000 / fps
    ticks = [round(i * ticks_per_frame) for i in range(info["frames"])]
    fp.require_supported_input(info, [tick / 1000 for tick in ticks])
    fp.require_supported_input(info, [(tick + 5) / 1000 for tick in ticks])
    # Moving one timestamp by one tick can leave both adjacent deltas within
    # floor/ceil but break the single rounding pattern across the clip.
    ticks[1] = int(ticks_per_frame) if ticks[1] > int(ticks_per_frame) else ticks[1] + 1
    with pytest.raises(fp.UnsupportedInput, match="variable frame rate"):
        fp.require_supported_input(info, [tick / 1000 for tick in ticks])


def assert_run_refused(src, tmp_path, reason):
    out = tmp_path / "new-directory" / "finished.mp4"
    before = set(tmp_path.rglob("*"))
    run = subprocess.run([sys.executable, fp.__file__, "run", str(src), "--out", str(out)],
                         capture_output=True, text=True)
    assert run.returncode != 0
    assert run.stderr.startswith("finish pass supports CFR, aligned A/V only")
    assert reason in run.stderr
    assert set(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("selection", ["not(eq(n,15))", "gte(n,30)+not(mod(n,15))"])
def test_vfr_is_refused_without_output(monkeypatch, tmp_path, selection):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src = tmp_path / "vfr.mp4"
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=30:d=1.5",
              "-vf", f"select='{selection}'", "-fps_mode", "passthrough", "-c:v", "libx264", src)
    assert_run_refused(src, tmp_path, "variable frame rate")


def test_submillisecond_vfr_is_refused_without_output(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src = tmp_path / "jitter.mp4"
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=30:d=3",
              "-f", "lavfi", "-i", "sine=f=440:r=44100:d=3",
              "-vf", r"settb=1/30000,setpts=N*1000+15*eq(mod(N\,3)\,1)",
              "-fps_mode", "passthrough", "-enc_time_base", "1:30000",
              "-video_track_timescale", "30000", "-bf", "0", "-c:v", "libx264", "-c:a", "aac", src)
    info = fp.probe(src)
    assert info["fps"] == 30 and Fraction(info["avg_fps"]) == 30
    ticks = [round(t * 30000) for t in sfx_cues.frame_times(src)]
    assert {b - a for a, b in zip(ticks, ticks[1:])} == {985, 1000, 1015}
    assert_run_refused(src, tmp_path, "variable frame rate")


@pytest.mark.parametrize("delayed_stream", ["video", "audio"])
@pytest.mark.parametrize("delay", ["0.375", "0.033333"])
def test_alignment_limit(monkeypatch, tmp_path, delayed_stream, delay):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    offset = ["-itsoffset", delay]
    fp.ffmpeg("-v", "error", *(offset if delayed_stream == "video" else []),
              "-f", "lavfi", "-i", "color=s=96x96:r=30:d=1.5",
              *(offset if delayed_stream == "audio" else []),
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=1.5",
              "-fps_mode", "passthrough", "-c:v", "libx264", "-c:a", "aac", src)
    info = fp.probe(src)
    delta = fp.stream_start(info["audio"]) - info["video_start"]
    assert (delta > 0) == (delayed_stream == "audio")
    if delay == "0.375":
        assert abs(delta) > 1 / 30
        assert_run_refused(src, tmp_path, "starts")
    else:
        assert 0 < abs(delta) <= 1 / 30
        report = fp.run(src, out)
        assert report["timing"]["output_av_offset"] == pytest.approx(0, abs=0.002)
        assert fp.check(out, src)["pass"]


@pytest.mark.parametrize("fps,timescale", [("30", 30), ("30000/1001", 30000)])
def test_cfr_timebases_and_cue_only_mix(monkeypatch, tmp_path, fps, timescale):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", f"color=s=96x96:r={fps}:d=1.3",
              "-c:v", "libx264", "-video_track_timescale", timescale, src)
    report = fp.run(src, out)
    assert report["cue_counts"]["impact"] == 1
    assert report["loudness"]["source"] is None
    assert report["timing"]["source_frames"] == report["timing"]["output_frames"] == 39
    assert len(fp.probe(out)["audio_tracks"]) == 1
    assert fp.check(out, src)["pass"]


def test_33_frame_ntsc_cue_only_mix_allows_aac_container_padding(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "color=s=96x96:r=30000/1001:d=1.1",
              "-c:v", "libx264", src)
    source = fp.probe(src)
    assert source["frames"] == 33
    fp.run(src, out)
    result = fp.probe(out)
    assert result["frames"] == 33
    assert result["duration"] == source["duration"]
    assert [track["codec_name"] for track in result["audio_tracks"]] == ["aac"]
    assert result["format_duration"] <= source["format_duration"] + 0.025
    assert fp.audio_passes(loudness(out))
    assert fp.check(out, src)["pass"]


def test_report_binding_rejects_missing_or_modified_video(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("source.mp4", "finished.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=12:d=1",
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=1", "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    assert report["timing"]["source_frames"] == report["timing"]["output_frames"] == 12
    assert report["timing"]["source_seconds"] == report["timing"]["output_seconds"] == 1
    assert fp.check(out, src)["pass"]
    with out.open("ab") as handle:
        handle.write(b"changed")
    assert not fp.check(out, src)["artifact"]["pass"]
    fp.sidecar(out).unlink()
    assert not fp.check(out, src)["pass"]


def test_cue_tails_are_trimmed_and_check_rejects_tampering(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out, extra_track = (tmp_path / name for name in ("src.mp4", "out.mp4", "extra.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "color=s=96x96:r=30:d=2",
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=2",
              "-c:v", "libx264", "-c:a", "aac", src)
    impact = sfx_cues.Cue("impact", 1.65, -7)
    late = sfx_cues.Cue("click", 2.0, -11)
    monkeypatch.setattr(sfx_cues, "plan_cues", lambda **events: [impact, late])

    report = fp.run(src, out)
    assert report["cue_counts"]["impact"] == 1
    assert [cue["time"] for cue in report["cues_rendered"]] == [impact.time]
    assert [cue["time"] for cue in report["cues_skipped"]] == [late.time]
    assert len(report["cues_planned"]) == 2
    audio = fp.ffmpeg("-v", "error", "-ss", str(impact.time), "-i", out, "-vn",
                      "-t", "0.25", "-f", "f32le", "-").stdout
    assert np.sqrt(np.mean(np.frombuffer(audio, "<f4") ** 2)) > 0.01
    source, result = fp.probe(src), fp.probe(out)
    assert len(result["audio_tracks"]) == 1
    assert result["format_duration"] <= source["format_duration"]
    assert result["duration"] <= source["duration"]
    assert float(result["audio"]["duration"]) <= float(source["audio"]["duration"]) + 0.025
    assert fp.check(out, src)["pass"]

    moved_counts = {**report["cue_counts"], "impact": 0}
    for edits in (
        {"cues_planned": []},
        {"cues_rendered": [], "cues_skipped": report["cues_planned"], "cue_counts": moved_counts},
        {"cue_counts": {**report["cue_counts"], "click": 1}},
        {"cues_skipped": [*report["cues_skipped"], *report["cues_skipped"]]},
        {"cues_planned": [*report["cues_planned"], *report["cues_skipped"]],
         "cues_skipped": [*report["cues_skipped"], *report["cues_skipped"]]},
        {"cues_skipped": [{**report["cues_skipped"][0], "gain_db": 0}]},
    ):
        fp.sidecar(out).write_text(json.dumps({**report, **edits}))
        assert not fp.check(out, src)["pass"], edits

    fp.ffmpeg("-v", "error", "-i", out, "-map", "0:v:0", "-map", "0:a:0",
              "-map", "0:a:0", "-c", "copy", extra_track)
    fp.sidecar(extra_track).parent.mkdir()
    fp.sidecar(extra_track).write_text(json.dumps({**report, "artifact": fp.artifact_identity(extra_track)}))
    checked = fp.check(extra_track, src)
    assert checked["artifact"]["pass"]
    assert checked["timing"]["output_audio_tracks"] == 2
    assert not checked["pass"]


def test_sparse_programme_reaches_encoded_targets(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "color=s=96x96:r=12:d=9",
              "-f", "lavfi", "-i", r"aevalsrc=0.9*sin(2*PI*600*t)*lt(mod(t\,0.5)\,0.01):s=48000:d=9",
              "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    assert report["loudness"]["attempts"] >= 1
    assert fp.audio_passes(loudness(out))


@pytest.mark.parametrize("seconds,message", [(0.25, "at least 1.0 s"), (1, "silent mix.*-70 LUFS")])
def test_short_and_silent_input_have_explicit_diagnostics(monkeypatch, tmp_path, capsys, seconds, message):
    import re

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    audio = ["-f", "lavfi", "-i", "anullsrc=r=48000:d=1", "-c:a", "aac"] if seconds == 1 else []
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", f"color=s=96x96:r=12:d={seconds}",
              *audio, "-c:v", "libx264", src)
    if seconds == 1:
        # Exercise the loudness gate even though the mix has a finite peak.
        monkeypatch.setattr(sfx_cues, "plan_cues", lambda **events: [sfx_cues.Cue("impact", 0, -120)])
    monkeypatch.setattr(sys, "argv", ["finish_pass", "run", str(src), "--out", str(out)])
    assert fp.main() == 1
    assert re.search(message, capsys.readouterr().err)
    assert not out.exists()
