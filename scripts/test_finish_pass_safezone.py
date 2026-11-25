import re

import pytest

import finish_pass as fp


def test_signal_placement():
    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, 1080, 1920)
    assert fp.placement_passes(plan)
    assert plan["safe"] == fp.Rect(120, 270, 960, 1248)
    assert plan["targets"]["badge"].x0 == plan["safe"].x0
    assert plan["targets"]["pill"].x1 == plan["safe"].x1
    assert plan["targets"]["captions"].y1 == plan["safe"].y1
    assert {"captions"} <= set(plan["right_rail_overlap"])


def test_relocates_pixels_and_erases_edges(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("source.mp4", "finished.mp4"))
    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, 360, 640)
    boxes = [
        f"drawbox=x={r.x0+3}:y={r.y0+3}:w={r.width-6}:h={r.height-6}:color=white:t=fill"
        for name, r in plan["sources"].items() if name == "badge"
    ]
    captions = plan["sources"]["captions"]
    # Include distinct bright glyphs and a dark backing around the lettering.
    boxes.extend(f"drawbox=x={captions.x0+100+x}:y={captions.y0+8}:w=6:h=8:c=white:t=fill"
                 for x in range(0, 45, 9))
    boxes.append("drawbox=x=0:y=200:w=360:h=150:c=0xb8b8b8:t=fill")
    base = "color=c=0x383838:s=360x640:r=12:d=1.5"
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", ",".join([base, *boxes]),
              "-f", "lavfi", "-i", "sine=f=360:r=48000:d=1.5",
              "-c:v", "libx264", "-c:a", "aac", src)
    fp.run(src, out)
    output = fp.gray_frames(out, 360, 640, 1)[0]
    for name in ("badge", "captions"):
        assert plan["targets"][name].crop(output).max() > 210
        assert plan["sources"][name].crop(output).std() < 4
    assert fp.check(out, src)["safe_zone"]["pass"]


def test_filter_graphs_use_lgpl_filters(tmp_path):
    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, 360, 640)
    graph, _ = fp.video_graph(360, 640, plan, 4, 1, tmp_path, "bt709", 30)
    from sfx_cues import DUCK_GRAPH, mastering_filter

    graphs = [graph, DUCK_GRAPH, mastering_filter(5, -1.5)]
    gpl_only = r"(?:^|[;,\]])(?:boxblur|eq|curves|delogo|hqdn3d|noise|vignette|cas|nnedi|smartblur|unsharp)="
    assert not any(re.search(gpl_only, g) for g in graphs)
    assert "gblur" in graph and "all_mode=screen" in graph and "lut3d" in graph


def test_caption_and_pill_mask_follow_ink_instead_of_background(monkeypatch, tmp_path):
    import numpy as np

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("source.mp4", "finished.mp4"))
    w, h = 360, 640
    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, w, h)
    filters = ["color=c=0x363636:s=360x640:r=12:d=2"]

    def box(x, y, width, height, color, active=False):
        enable = ":enable='gte(t,1)'" if active else ""
        filters.append(f"drawbox=x={x}:y={y}:w={width}:h={height}:c={color}:t=fill{enable}")

    # Give the cover a stable tonal range clear of both destination strips.
    box(0, 190, w, 175, "0xb8b8b8")
    for name in ("pill", "captions"):
        area = plan["sources"][name]
        # High-frequency scenery in both source strips, with flat scenery
        # around the destinations so the control's blur has no effect there.
        box(area.x0, area.y0, area.width, area.height, "0x858585")
        for x in range(area.x0 + 2, area.x1 - 3, 6):
            box(x, area.y0, 2, area.height, "0xa0a0a0")
        if name == "captions":
            # Two bright highlights at opposite ends of a caption-free strip.
            for x in (area.x0 + 5, area.x1 - 10):
                filters.append(f"drawbox=x={x}:y={area.y0+8}:w=5:h=6:c=white:t=fill:enable='lt(t,1)'")
        cx, cy = area.x0 + area.width // 2, area.y0 + area.height // 2
        box(cx - 28, cy - 8, 56, 16, "0x111111", active=True)
        for x in range(cx - 20, cx + 20, 8):
            box(x, cy - 3, 4, 6, "white", active=True)
    fp.ffmpeg("-v", "error", "-f", "lavfi", "-i", ",".join(filters),
              "-f", "lavfi", "-i", "sine=f=360:r=48000:d=2",
              "-c:v", "libx264", "-c:a", "aac", src)
    report = fp.run(src, out)
    control_dir = tmp_path / "control"
    control_dir.mkdir()
    control = fp.render_picture(src, control_dir, fp.probe(src), None, report["cover"]["frame"], 1)
    blank, ink = 6, 18  # Far from the opening-frame substitution and the text transition.
    actual = fp.gray_frames(out, w, h, ink + 1)
    baseline = fp.gray_frames(control, w, h, ink + 1)
    for name in ("pill", "captions"):
        area = plan["targets"][name]
        blank_delta = area.crop(actual[blank]).astype(float) - area.crop(baseline[blank])
        assert np.abs(blank_delta).mean() < 3, name
        centre = area.width // 2
        with_ink = area.crop(actual[ink])
        assert np.count_nonzero(with_ink[:, centre - 24:centre + 24] > 200) > 25, name
        # The scenery at both ends of the crop should still be the destination scenery.
        assert np.abs(with_ink[:, :12].astype(float) - area.crop(baseline[ink])[:, :12]).mean() < 3, name
    original_strip = plan["sources"]["captions"].crop(actual[blank])
    for x in (5, original_strip.shape[1] - 10):
        assert original_strip[8:14, x:x + 5].mean() > 180



def test_checker_detects_missing_caption_independently_of_compositing_mask(monkeypatch):
    import numpy as np

    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, 360, 640)
    source = np.full((640, 360), 40, dtype=np.uint8)
    delivered = source.copy()
    caption = plan["sources"]["captions"].crop(source)
    for x in (125, 133, 141, 149):
        caption[8:16, x:x+4] = 240
    monkeypatch.setattr(fp, "text_alpha", lambda gray, *args: np.zeros_like(gray))
    check = fp.anchor_checks(plan, source, delivered)["captions"]
    assert check["present"]
    assert not check["pass"]



@pytest.mark.parametrize("text", ["A", "OK"])
def test_short_caption_relocates_and_missing_ink_fails_check(monkeypatch, tmp_path, text):
    import cv2
    import numpy as np

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    src, out = (tmp_path / name for name in ("source.mp4", "finished.mp4"))
    w, h = 360, 640
    plan = fp.plan_layout(fp.DEFAULT_LAYOUT, w, h)
    source, target = (plan[key]["captions"] for key in ("sources", "targets"))
    frame = np.full((h, w), 56, dtype=np.uint8)
    frame[190:365] = 184
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, 0.45, 1)
    cv2.putText(frame, text, ((source.x0 + source.x1 - tw) // 2,
                             (source.y0 + source.y1 + th) // 2),
                font, 0.45, 240, 1, cv2.LINE_8)
    still = tmp_path / "caption.pgm"
    still.write_bytes(f"P5\n{w} {h}\n255\n".encode() + frame.tobytes())
    fp.ffmpeg("-v", "error", "-loop", "1", "-framerate", 12, "-i", still,
              "-f", "lavfi", "-i", "sine=f=360:r=48000:d=1",
              "-t", 1, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", src)
    report = fp.run(src, out)
    decoded = fp.gray_frames(out, w, h, 2)
    assert all(np.count_nonzero(target.crop(frame) > 170) >= 8 for frame in decoded)
    assert all(source.crop(frame).max() < 120 for frame in decoded)
    assert report["safe_zone"]["frame0_anchor_checks"]["captions"]["present"]
    reference = fp.gray_frames(src, w, h, 1)[0]
    blank = decoded[0].copy()
    monkeypatch.setattr(fp, "text_alpha", lambda gray, *args: np.zeros_like(gray))
    for level in (56, 240):
        target.crop(blank)[:] = level
        result = fp.anchor_checks(plan, reference, blank)["captions"]
        assert result["present"] and not result["pass"]
