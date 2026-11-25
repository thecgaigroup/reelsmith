import pytest

import finish_pass as fp


@pytest.mark.parametrize("mean,std,source,expected", [
    (15, 20, 10, False), (30, 11, 20, False), (18.8, 20, 20, False), (19, 12, 20, True),
])
def test_frame_zero_gate(mean, std, source, expected):
    assert fp.cover_passes({"mean": mean, "stddev": std}, {"mean": source}) is expected


def test_cover_replaces_only_frame_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "yes")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i",
              "testsrc2=s=160x160:r=12:d=2,drawbox=c=black:t=fill:enable='lt(n,3)'",
              "-f", "lavfi", "-i", "sine=f=480:r=48000:d=2",
              "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    assert report["cover"]["frame"] >= 3
    assert report["cover"]["hold_frames"] == 1
    assert report["frame0"]["pass"]
    assert fp.gray_frames(out, 160, 160, 2)[1].mean() < 10
    before, after = fp.probe(src), fp.probe(out)
    assert before["frames"] == after["frames"] == 24
    assert before["duration"] == after["duration"] == 2
