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
    import json
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
    first, second = fp.gray_frames(out, delivered["width"], delivered["height"], 2)
    original = fp.gray_frames(src, 160, 160, 1)[0]
    assert original.mean() < 10
    assert fp.cover_passes(fp.luma(first), fp.luma(original))
    assert second.mean() < 10
    report = json.loads((delivery / "export-report.json").read_text())[0]
    assert report["file"] == str(out)
    assert report["frame0"] == {"source": fp.luma(original), "output": fp.luma(first), "pass": True}


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


def test_export_rejects_opening_luma_lost_to_crop(monkeypatch, tmp_path):
    import sys

    import export

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, delivery = tmp_path / "src.mp4", tmp_path / "delivery"
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i",
              "color=c=black:s=160x160:r=30:d=1,drawbox=x=0:y=0:w=24:h=160:c=white:t=fill",
              "-f", "lavfi", "-i", "sine=f=480:r=48000:d=1",
              "-c:v", "libx264", "-c:a", "aac", src)
    original = fp.luma(fp.gray_frames(src, 160, 160, 1)[0])
    assert fp.cover_passes(original, original)
    export_one = export.export_one
    measured = []

    def inspect_delivery(*args, **kwargs):
        result = export_one(*args, **kwargs)
        opening = fp.gray_frames(result["file"], result["w"], result["h"], 1)[0]
        measured.append(fp.luma(opening))
        return result

    monkeypatch.setattr(export, "export_one", inspect_delivery)
    monkeypatch.setattr(sys, "argv", ["export.py", "run", str(src), "--preset", "reels",
                                      "--out", str(delivery), "--fit", "crop", "--unreviewed"])
    with pytest.raises(SystemExit, match="delivered frame 0"):
        export.main()
    assert measured and measured[0]["mean"] < 1
    assert not (delivery / "src-reels.mp4").exists()
    assert not (delivery / "export-report.json").exists()


def test_checker_rejects_interrupted_publish_in_either_order(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("src.mp4", "out.mp4"))
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=12:d=1",
              "-f", "lavfi", "-i", "sine=f=480:r=48000:d=1",
              "-c:v", "libx264", "-c:a", "aac", src)
    fp.run(src, out)
    assert fp.check(out, src)["pass"]
    report = fp.sidecar(out)
    old_video, old_report = out.read_bytes(), report.read_bytes()
    fp.run(src, out, cover_hold=0.2)
    assert fp.check(out, src)["pass"]
    new_video, new_report = out.read_bytes(), report.read_bytes()
    assert old_video != new_video and old_report != new_report

    for video, metadata in ((old_video, new_report), (new_video, old_report)):
        out.write_bytes(video)
        report.write_bytes(metadata)
        result = fp.check(out, src)
        assert not result["pass"]
        assert not result["artifact"]["pass"]
    out.write_bytes(new_video[:-1] + bytes([new_video[-1] ^ 1]))
    report.write_bytes(new_report)
    assert not fp.check(out, src)["artifact"]["pass"]
    report.unlink()
    assert not fp.check(out, src)["pass"]
