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
