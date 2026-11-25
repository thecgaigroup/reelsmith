import re
from pathlib import Path

import numpy as np

import finish_pass as fp


def read_rgb(path):
    frame = fp.ffmpeg("-v", "error", "-i", path, "-frames:v", 1,
                      "-pix_fmt", "rgb24", "-f", "rawvideo", "-").stdout
    return np.frombuffer(frame, np.uint8).reshape(320, 180, 3).astype(float)


def edge_energy(patch):
    return np.abs(np.diff(patch, axis=1)).mean()


def test_title_focus_and_cyan_glow(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "on")
    src, out = (tmp_path / name for name in ("source.mp4", "finished.mp4"))
    scene = ("color=c=0x242424:s=180x320:r=12:d=1,"
             "drawgrid=w=4:h=4:t=2:c=white,"
             "drawbox=x=0:y=106:w=180:h=85:c=0x242424:t=fill,"
             "drawbox=x=30:y=140:w=6:h=20:c=white:t=fill,"
             "drawbox=x=42:y=140:w=6:h=20:c=white:t=fill,"
             "drawbox=x=90:y=140:w=40:h=20:c=cyan:t=fill")
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", scene,
              "-f", "lavfi", "-i", "sine=f=440:r=48000:d=1",
              "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    assert {"gblur", "alphamerge", "blend"} <= set(report["filters"])
    assert report["timing"]["source_frames"] == report["timing"]["output_frames"] == 12
    assert report["timing"]["output_size"] == [180, 320]
    before, after = read_rgb(src), read_rgb(out)
    title = np.s_[145:155, 24:55]
    background = np.s_[50:90, 30:150]
    assert 0.9 <= edge_energy(after[title]) / edge_energy(before[title]) <= 1.12
    assert edge_energy(after[background]) < 0.55 * edge_energy(before[background])
    halo = np.s_[144:156, 86:90]
    glow = (after[halo] - before[halo]).mean(axis=(0, 1))
    assert glow @ [0.2126, 0.7152, 0.0722] > 2
    assert min(glow[1:]) > max(4, glow[0] + 3)
    assert abs(glow[1] - glow[2]) <= 4


def test_graph_uses_only_expected_filters(tmp_path):
    info = {"width": 180, "height": 320, "sar": "1:1"}
    title = fp.title_region(fp.layout_path(info), 180, 320)
    graph, _ = fp.video_graph(180, 320, title, tmp_path, "bt709")
    filters = set(re.findall(r"(?:^|[,;\]])([a-z0-9_]+)(?:[=\[;,]|$)", graph))
    assert filters - {"sws_flags"} == {"setpts", "format", "split", "gblur", "crop", "scale", "lut3d",
                       "blend", "alphamerge", "overlay"}
    assert graph.count("lut3d=") == graph.count("lut3d=file=bloom-key.cube:") == 1
    assert "scale=180:320" not in graph


def test_nonvertical_layout_requires_opt_in(tmp_path):
    info = {"width": 160, "height": 90, "sar": "1:1"}
    assert fp.layout_path(info) is None
    graph, inputs = fp.video_graph(160, 90, None, tmp_path, "bt709")
    assert graph == "[0:v:0]setpts=PTS-STARTPTS,format=yuv420p[v]"
    assert inputs == []
    custom = tmp_path / "title.json"
    custom.write_text('{"regions": {"title": [0.25, 0.4, 0.75, 0.6]}}')
    assert fp.title_region(fp.layout_path(info, custom), 160, 90) == fp.Rect(40, 36, 120, 54)


def test_source_stays_in_scope():
    source = Path(fp.__file__).read_text().lower()
    forbidden = ("caption", "erase", "relocat", "cover", "leftover", "safe_zone", "right_rail")
    assert all(word not in source for word in forbidden)
