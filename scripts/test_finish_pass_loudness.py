import pytest

import finish_pass as fp
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


@pytest.mark.parametrize("delayed_stream", ["video", "audio"])
def test_staggered_stream_start_is_preserved_and_checked(monkeypatch, tmp_path, delayed_stream):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out, shifted = (tmp_path / name for name in ("src.mp4", "out.mp4", "shifted.mp4"))
    delay = ["-itsoffset", "0.375"]
    fp.ffmpeg("-v", "error", *(delay if delayed_stream == "video" else []),
              "-f", "lavfi", "-i", "testsrc2=s=96x96:r=120:d=1",
              *(delay if delayed_stream == "audio" else []),
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=1",
              "-fps_mode", "passthrough", "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    timing = report["timing"]
    assert abs(timing["source_av_offset"]) > 0.3
    assert timing["output_av_offset"] == pytest.approx(timing["source_av_offset"], abs=1/120)
    assert fp.check(out, src)["timing"]["pass"]
    source_audio = fp.probe(src)["audio"]
    finished_audio = fp.probe(out)["audio"]
    assert float(finished_audio["duration"]) == pytest.approx(float(source_audio["duration"]), abs=1/120)

    # Add a delay to the stream that already starts last, leaving the
    # picture rate, frame count and coded duration untouched.
    stream = delayed_stream[0]
    fp.ffmpeg("-v", "error", "-i", out, *delay, "-i", out,
              "-map", f"{int(stream == 'v')}:v:0", "-map", f"{int(stream == 'a')}:a:0",
              "-c", "copy", shifted)
    assert not fp.measure(shifted, src)["timing"]["pass"]


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
