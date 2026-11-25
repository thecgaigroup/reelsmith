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


@pytest.mark.parametrize("video_delay", ["0", "0.375"])
def test_export_delivers_cover_after_downsampling(monkeypatch, tmp_path, video_delay):
    import sys

    import export

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, delivery = tmp_path / "src.mp4", tmp_path / "delivery"
    fp.ffmpeg("-v", "error", "-itsoffset", video_delay, "-f", "lavfi", "-i",
              "testsrc2=s=160x160:r=120:d=1,drawbox=c=black:t=fill:enable='lt(n,24)'",
              "-f", "lavfi", "-i", "sine=f=480:r=48000:d=1",
              "-fps_mode", "passthrough", "-c:v", "libx264", "-c:a", "aac", src)
    monkeypatch.setattr(sys, "argv", ["export.py", "run", str(src), "--preset", "reels",
                                      "--out", str(delivery), "--fit", "crop", "--unreviewed"])
    with pytest.raises(SystemExit, match="^0$"):
        export.main()
    out = delivery / "src-reels.mp4"
    delivered = fp.probe(out)
    assert delivered["fps"] == 30
    lead = delivered["video_start"] - float(delivered["audio"]["start_time"])
    assert lead == pytest.approx(float(video_delay), abs=1/30)
    first, second = fp.gray_frames(out, 90, 160, 2)
    original = fp.gray_frames(src, 90, 160, 1)[0]
    assert original.mean() < 10
    assert fp.cover_passes(fp.luma(first), fp.luma(original))
    assert second.mean() < 10


@pytest.mark.parametrize("failed_file", ["report", "video"])
def test_publish_failure_leaves_existing_pair(monkeypatch, tmp_path, failed_file):
    from pathlib import Path

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=12:d=1",
              "-f", "lavfi", "-i", "sine=f=480:r=48000:d=1",
              "-c:v", "libx264", "-c:a", "aac", src)
    out.write_bytes(b"previous MP4")
    report = fp.sidecar(out)
    report.parent.mkdir()
    report.write_text("previous report")
    replace = Path.replace

    def fail_replace(path, target):
        if target == (report if failed_file == "report" else out):
            raise OSError("injected rename failure")
        return replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="injected rename failure"):
        fp.run(src, out)
    assert out.read_bytes() == b"previous MP4"
    assert report.read_text() == "previous report"
