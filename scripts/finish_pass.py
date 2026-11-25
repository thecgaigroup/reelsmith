#!/usr/bin/env python3
"""Finish a flat master offline, or recheck the rendered file against its source."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import astuple, dataclass
from fractions import Fraction
from pathlib import Path

from finish_pass_flag import enabled

SCRIPTS = Path(__file__).resolve().parent
DEFAULT_LAYOUT = SCRIPTS.parent / "references" / "finish-pass-layouts" / "signal-9x16.json"
ANCHORS = ("badge", "pill", "captions")
TEXT_ANCHORS = ("pill", "captions")
SWS = "accurate_rnd+full_chroma_int"
DISABLED = "finish pass disabled (REELSMITH_FINISH_PASS not set)"


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

    def contains(self, other):
        return self.x0 <= other.x0 < other.x1 <= self.x1 and self.y0 <= other.y0 < other.y1 <= self.y1

    def overlaps(self, other):
        return (self.x0 < other.x1 and self.x1 > other.x0 and
                self.y0 < other.y1 and self.y1 > other.y0)

    def crop(self, frame):
        return frame[self.y0:self.y1, self.x0:self.x1]

    def filter(self):
        return f"crop={self.width}:{self.height}:{self.x0}:{self.y0}:exact=1"


def even_down(n):
    return 2 * math.floor(n / 2)


def even_up(n):
    return 2 * math.ceil(n / 2)


def fit(rect, width, height):
    factor = min(1, width / rect.width, height / rect.height)
    result = even_down(rect.width * factor), even_down(rect.height * factor)
    if min(result) < 2:
        raise ValueError("layout has insufficient safe space for an anchor")
    return result


def plan_layout(layout, width, height):
    regions = json.loads(Path(layout).read_text())["regions"]
    if set(regions) != {*ANCHORS, "title"}:
        raise ValueError("layout must define badge, pill, captions and title")
    frame = Rect(0, 0, width, height)
    sources = {}
    for name, (x0, y0, x1, y1) in regions.items():
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError(f"invalid fractional source rectangle for {name}")
        # Stabilize decimal coordinates at their intended pixel boundaries.
        x0, y0, x1, y1 = (round(v * d, 4) for v, d in zip((x0, y0, x1, y1), (width, height, width, height)))
        rect = Rect(even_down(x0), even_down(y0), even_up(x1), even_up(y1))
        if not frame.contains(rect) or any(rect.overlaps(other) for other in sources.values()):
            raise ValueError(f"invalid or overlapping source rectangle for {name}")
        sources[name] = rect

    presets = json.loads((SCRIPTS / "presets.json").read_text())["presets"]
    reels, tiktok = (presets[name]["safe"] for name in ("reels", "tiktok"))
    left, top, right, bottom = (max(reels[k], tiktok[k]) for k in ("left", "top", "right", "bottom"))
    safe = Rect(even_up(left * width), even_up(top * height),
                even_down((1 - right) * width), even_down((1 - bottom) * height))
    title = sources["title"]
    # The two top corners share one row. Fit each above or beside the title.
    badge, pill = (sources[k] for k in ("badge", "pill"))
    top_width_scale = min(1, safe.width / (badge.width + pill.width))

    def fit_corner(rect, left_corner):
        max_width = rect.width * top_width_scale
        if not title.overlaps(safe):
            return fit(rect, max_width, safe.height)
        beside = title.x0 - safe.x0 if left_corner else safe.x1 - title.x1
        slots = [(max_width, title.y0 - safe.y0), (min(max_width, beside), safe.height)]
        available = [(w, h) for w, h in slots if w >= 2 and h >= 2]
        if not available:
            raise ValueError("layout has insufficient safe space for the top corners")
        w, h = max(available, key=lambda slot: min(1, slot[0] / rect.width, slot[1] / rect.height))
        return fit(rect, w, h)

    bw, bh = fit_corner(badge, True)
    pw, ph = fit_corner(pill, False)
    targets = {
        "badge": Rect(safe.x0, safe.y0, safe.x0 + bw, safe.y0 + bh),
        "pill": Rect(safe.x1 - pw, safe.y0, safe.x1, safe.y0 + ph),
    }

    row_end = safe.y0 + max(bh, ph)
    # Use the lowest full-width slot once an anchor fits at native size.
    slots = [(row_end, safe.y1)]
    if title.overlaps(safe):
        slots = [(max(row_end, title.y1), safe.y1), (row_end, min(title.y0, safe.y1))]
    caption = sources["captions"]
    usable = [(lo, hi) for lo, hi in slots if hi - lo >= 2]
    if not usable:
        raise ValueError("layout has insufficient safe space for captions")
    lo, hi = max(usable, key=lambda slot: min(1, safe.width / caption.width,
                                              (slot[1] - slot[0]) / caption.height))
    cw, ch = fit(caption, safe.width, hi - lo)
    cx = safe.x0 + even_down((safe.width - cw) / 2)
    rail = tiktok["right_rail"]
    right_rail = Rect(math.floor(width * rail["x"]), math.floor(height * rail["y"]), width, height)
    # Prefer the rail-free slot when it retains at least 70% on both axes.
    rail_width = even_down(right_rail.x0 - max(2, even_up(width * 0.006))) - safe.x0
    if hi > right_rail.y0 and rail_width >= 0.7 * caption.width and cx + cw > right_rail.x0:
        rw, rh = fit(caption, min(safe.width, rail_width), hi - lo)
        if min(rw / caption.width, rh / caption.height) >= 0.7:
            cx, cw, ch = safe.x0, rw, rh
    targets["captions"] = Rect(cx, hi - ch, cx + cw, hi)
    plan = {"sources": sources, "targets": targets, "safe": safe,
            "right_rail_overlap": [k for k, rect in targets.items() if rect.overlaps(right_rail)]}
    if not placement_passes(plan):
        raise ValueError("anchor placement failed the safe-zone gate")
    return plan


def placement_passes(plan):
    rects = list(plan["targets"].values())
    return all(plan["safe"].contains(rect) and not plan["sources"]["title"].overlaps(rect)
               and not any(rect.overlaps(other) for other in rects[:i]) for i, rect in enumerate(rects))


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
        "format_start": stream_start(data["format"]),
        "audio": next((s for s in data["streams"] if s["codec_type"] == "audio"), None),
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


def gray_frames(path, width, height, count, start=0):
    import numpy as np
    from sfx_cues import local_file

    raw = ffmpeg("-v", "error", "-i", local_file(path), "-map", "0:v:0",
                 "-vf", f"trim=start_frame={start},scale={width}:{height}:flags=area+{SWS},format=gray",
                 "-frames:v", count, "-fps_mode", "passthrough", "-f", "rawvideo", "-").stdout
    if not raw:
        raise ValueError(f"{path}: could not decode frame {start}")
    return np.frombuffer(raw, np.uint8).reshape(-1, height, width)


def luma(frame):
    return {"mean": float(frame.mean()), "stddev": float(frame.std())}


def cover_passes(out, source):
    return out["mean"] >= 16 and out["stddev"] >= 12 and out["mean"] >= 0.95 * source["mean"]


def select_cover(path, info, layout, original):
    import numpy as np

    width, height = info["width"], info["height"]
    sw, sh = max(2, width // 4), max(2, height // 4)
    limit = max(1, math.ceil(info["fps"] * min(3, info["duration"])))
    frames = gray_frames(path, sw, sh, limit)
    title = layout["sources"]["title"] if layout else Rect(0, 0, width, height)
    area = Rect(title.x0 * sw // width, title.y0 * sh // height,
                math.ceil(title.x1 * sw / width), math.ceil(title.y1 * sh / height))
    title_frames = np.asarray([area.crop(frame) for frame in frames], dtype=np.float32)
    scores = []
    for i, (frame, patch) in enumerate(zip(frames, title_frames)):
        gradients = (np.diff(patch, axis=axis) for axis in (0, 1) if patch.shape[axis] > 1)
        detail = sum(float(np.abs(gradient).mean()) for gradient in gradients)
        scores.append((cover_passes(luma(frame), original), detail, i))
    passing = [(score, i) for ok, score, i in scores if ok]
    if not passing:
        return max(scores)[2]
    # Require detail to persist across a short window so animated letter
    # edges or a partially decoded reveal don't win on sharpness alone.
    peak = max(score for score, _ in passing)
    span = max(1, round(float(info["fps"]) * 0.1))
    for score, i in passing:
        if score < peak * 0.95:
            continue
        neighbours = title_frames[max(i - span, 0):i + span + 1]
        if np.abs(neighbours - title_frames[i]).mean(axis=(1, 2)).max() <= 2.5:
            return i
    return max(passing, key=lambda candidate: candidate[0])[1]


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


def text_runs(gray, name, width):
    """Locate bright, aligned strokes against the backing of the text band."""
    import cv2
    import numpy as np

    scale = width / 1080
    if name == "captions":
        # A tall letter can fill the band. Measure contrast against nearby
        # darker backing without treating the height as a classifier.
        span = max(3, round(12 * scale)) | 1
        backing = cv2.erode(gray, np.ones((span, span), dtype=np.uint8))
        ink = (gray >= 112) & (gray.astype(np.int16) - backing >= 48)
    else:
        edge = np.concatenate((gray[0], gray[-1], gray[:, 0], gray[:, -1]))
        hist = np.bincount(edge, minlength=256)
        background = np.searchsorted(hist.cumsum(), edge.size * 0.75)
        ink = gray >= max(112, background + 45)
    if not ink.any():
        return ink, (), (), 0
    _, _, components, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), connectivity=8)
    glyphs = sorted((int(x), int(y), int(w), int(h)) for x, y, w, h, area in components[1:]
                    if (name == "captions" or max(3, 9 * scale) <= h <= max(7, 35 * scale))
                    and w <= 1.65 * h and area >= max(4, 12 * scale ** 2))
    if not glyphs:
        return ink, (), (), 0

    # Use the densest baseline band. Glyphs with descenders may extend a
    # little below the line. Separate runs never borrow each other's backing.
    tolerance = max(2, round(7 * scale))
    bottoms = np.array([y + h for _, y, _, h in glyphs])
    histogram = np.bincount(bottoms, minlength=gray.shape[0] + 1)
    votes = np.convolve(histogram, np.ones(2 * tolerance + 1, dtype=int), mode="same")
    baseline = bottoms[votes[bottoms].argmax()]
    line = [glyph for glyph, bottom in zip(glyphs, bottoms) if abs(bottom - baseline) <= tolerance]
    height = float(np.median([h for _, _, _, h in line]))
    bounds = []
    run = [line[0]]
    for glyph in line[1:]:
        if glyph[0] - (run[-1][0] + run[-1][2]) > 1.8 * height:
            bounds.append(run)
            run = []
        run.append(glyph)
    bounds.append(run)

    boxes = []
    for run in bounds:
        x0, y0 = min(x for x, _, _, _ in run), min(y for _, y, _, _ in run)
        x1, y1 = max(x + w for x, _, w, _ in run), max(y + h for _, y, _, h in run)
        if len(run) < 3 and (
            name != "captions"
            or abs((x0 + x1) / 2 - gray.shape[1] / 2) > gray.shape[1] / 6
            or abs((y0 + y1) / 2 - gray.shape[0] / 2) > gray.shape[0] / 4
        ):
            continue
        boxes.append((x0, y0, x1, y1))
    return ink, boxes, components[1:], height


def text_alpha(gray, name, width):
    """Retain the backing around a horizontal run of nearby, aligned glyphs."""
    import numpy as np

    scale = width / 1080
    _, boxes, components, height = text_runs(gray, name, width)
    alpha = np.zeros(gray.shape, dtype=np.float32)
    for x0, y0, x1, y1 in boxes:
        pad_x, pad_y = min(20 * scale, 0.7 * height), 18 * scale
        if name == "pill":
            for x, y, w, h, area in components:
                if (0 < x0 - x <= 1.8 * height and 0 < x + w - x1 <= 1.8 * height
                        and y < y0 < y1 < y + h and h <= 3.5 * height and area < 0.25 * w * h):
                    x0, y0, x1, y1 = x, y, x + w, y + h
                    pad_x = pad_y = 2 * scale
                    break
        x0, x1 = x0 - pad_x, x1 + pad_x
        y0, y1 = y0 - pad_y, y1 + pad_y
        half_w, half_h = (x1 - x0) / 2, (y1 - y0) / 2
        radius = min(half_w, half_h, 12 * scale if name == "captions" else half_h)
        dx = np.abs(np.arange(gray.shape[1]) + 0.5 - (x0 + x1) / 2) - half_w + radius
        dy = np.abs(np.arange(gray.shape[0]) + 0.5 - (y0 + y1) / 2) - half_h + radius
        distance = (np.hypot(np.maximum(dx, 0), np.maximum(dy[:, None], 0)) +
                    np.minimum(np.maximum(dx, dy[:, None]), 0) - radius)
        feather = max(1, 5 * scale)
        np.maximum(alpha, np.clip(0.5 - distance / feather, 0, 1), out=alpha)
    return np.rint(255 * alpha ** 2 * (3 - 2 * alpha)).astype(np.uint8)


def write_text_masks(video, work, info, plan, cover, hold):
    """Decode both luma strips in one pass and write one gray alpha stream per anchor."""
    import numpy as np
    from sfx_cues import ffmpeg_command, local_file

    pill, captions = (plan["sources"][name] for name in TEXT_ANCHORS)
    width = max(pill.width, captions.width)
    height = pill.height + captions.height
    graph = ("[0:v:0]split=2[p][c];"
             f"[p]{pill.filter()},format=gray,pad={width}:{pill.height}:0:0[pill];"
             f"[c]{captions.filter()},format=gray,pad={width}:{captions.height}:0:0[captions];"
             "[pill][captions]vstack=inputs=2[v]")
    command = ffmpeg_command("-v", "error", "-i", local_file(video), "-filter_complex_threads", 2,
                             "-filter_complex", graph, "-map", "[v]", "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-")
    with (work / "pill.gray").open("w+b") as pill_mask, (work / "captions.gray").open("w+b") as caption_mask:
        masks = ((pill_mask, pill, 0), (caption_mask, captions, pill.height))
        count = 0
        with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder, decoder.stdout as frames:
            while raw := frames.read(width * height):
                if len(raw) != width * height:
                    raise ValueError("incomplete text-mask analysis frame")
                gray = np.frombuffer(raw, np.uint8).reshape(height, width)
                for name, (mask, rect, row) in zip(TEXT_ANCHORS, masks):
                    mask.write(text_alpha(gray[row:row + rect.height, :rect.width], name,
                                          info["width"]).tobytes())
                count += 1
            if decoder.wait() or count != info["frames"]:
                raise ValueError(f"text-mask analysis decoded {count} of {info['frames']} frames")
        # Replace masks wherever the picture uses the selected cover instead
        # of the original frame at that timestamp.
        for mask, rect, _ in masks:
            frame_size = rect.width * rect.height
            mask.seek(frame_size * cover)
            cover_alpha = mask.read(frame_size)
            mask.seek(0)
            for _ in range(hold):
                mask.write(cover_alpha)


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


def erase_geometry(rect, width, height):
    def pad(amount):
        return Rect(max(0, rect.x0 - amount), max(0, rect.y0 - amount),
                    min(width, rect.x1 + amount), min(height, rect.y1 + amount))

    shadow = max(2, even_up(width * 0.01))
    feather = max(4, even_up(width * 0.01))
    return pad(shadow), pad(shadow + feather), feather


def video_graph(width, height, plan, cover, hold, work, matrix, fps):
    # Framesync repeats the selected source frame on the opening frames only.
    graph = ["[0:v:0]setpts=PTS-STARTPTS[base]",
             f"[1:v:0]trim=start_frame={cover}:end_frame={cover+1},setpts=0[cover]",
             f"[base][cover]overlay=enable='lt(n,{hold})':format=auto[picture]"]
    inputs = []
    if not plan:
        return ";".join([*graph, "[picture]format=yuv420p[v]"]), inputs

    def text_input(name, source, target):
        inputs.append(["-f", "rawvideo", "-pixel_format", "gray", "-video_size",
                       f"{source.width}x{source.height}", "-framerate", str(fps),
                       "-i", work / f"{name}.gray"])
        label = f"[{len(inputs) + 1}:v:0]"
        if (source.width, source.height) != (target.width, target.height):
            graph.append(f"{label}{scale(target.width, target.height, 'bilinear')},format=gray[{name}mask]")
            label = f"[{name}mask]"
        return label

    def mask(outer, inner, label):
        path = work / f"{label}.pgm"
        write_mask(path, outer, inner)
        inputs.append(["-i", path])
        return f"[{len(inputs) + 1}:v:0]"

    def composite(base, patch, rect, label, alpha=None):
        if alpha:
            graph.append(f"{patch}{alpha}alphamerge[{label}alpha]")
            patch = f"[{label}alpha]"
        graph.append(f"{base}{patch}overlay={rect.x0}:{rect.y0}:format=yuv444[{label}]")
        return f"[{label}]"

    def scale(w, h, method):
        return f"scale={w}:{h}:flags={method}+{SWS}"

    def pad(rect, amount):
        return Rect(max(0, rect.x0 - amount), max(0, rect.y0 - amount),
                    min(width, rect.x1 + amount), min(height, rect.y1 + amount))

    # Process in 4:4:4 to avoid chroma shifts on cropped or rescaled overlays.
    graph.append("[picture]format=yuv444p,split=8[bg][title]" +
                 "".join(f"[{name}src][{name}fill]" for name in ANCHORS))
    soft = max(1.0, width * 0.003)
    graph.append(f"[bg]{scale(width//2, height//2, 'area')},gblur=sigma={soft:.2f}:steps=2,"
                 f"{scale(width, height, 'bicubic')}[blurred]")
    base = "[blurred]"
    text_masks = {name: text_input(name, plan["sources"][name], plan["targets"][name])
                  for name in TEXT_ANCHORS}
    for name in ANCHORS:
        inner, outer, border = erase_geometry(plan["sources"][name], width, height)
        # Average clean strips into two rows. FFmpeg's area upscale gives
        # a linear ramp in the middle half, even for a two-row input.
        top = min(border, outer.y0)
        bottom = min(border, height - outer.y1)
        if top and bottom:
            above = Rect(outer.x0, outer.y0 - top, outer.x1, outer.y0)
            below = Rect(outer.x0, outer.y1, outer.x1, outer.y1 + bottom)
            row = scale(outer.width, 1, "area")
            graph.extend([f"[{name}fill]split[{name}above][{name}below]",
                          f"[{name}above]{above.filter()},{row}[{name}a]",
                          f"[{name}below]{below.filter()},{row}[{name}b]",
                          f"[{name}a][{name}b]vstack=inputs=2,"
                          f"{scale(outer.width, 2 * outer.height, 'area')},"
                          f"crop={outer.width}:{outer.height}:0:{outer.height // 2}[{name}bands]"])
        elif top or bottom:
            band = (Rect(outer.x0, outer.y0 - top, outer.x1, outer.y0) if top else
                    Rect(outer.x0, outer.y1, outer.x1, outer.y1 + bottom))
            graph.append(f"[{name}fill]{band.filter()},{scale(outer.width, 1, 'area')},"
                         f"{scale(outer.width, outer.height, 'bilinear')}[{name}bands]")
        else:
            raise ValueError(f"no neighbouring background to fill {name}")
        graph.append(f"[{name}bands]gblur=sigma={border*0.6:.2f}:steps=2[{name}patch]")
        base = composite(base, f"[{name}patch]", outer, f"{name}erased", mask(outer, inner, name))

    title = plan["sources"]["title"]
    outer = pad(title, max(6, even_up(width * 0.02)))
    tight = max(1.0, width * 0.0045)
    wide = max(1.0, width * 0.018 / 4)
    bloom_key(work / "bloom-key.cube")
    # The key path is fixed. Execute FFmpeg from the scratch directory.
    graph.extend([
        f"[title]{outer.filter()},scale=in_color_matrix={matrix}:flags={SWS},format=gbrp,split[sharp][highlights]",
        "[highlights]lut3d=file=bloom-key.cube:interp=tetrahedral,split[tight][wide]",
        f"[tight]gblur=sigma={tight:.2f}:steps=2[inner]",
        f"[wide]{scale(max(2, outer.width//4), max(2, outer.height//4), 'area')},"
        f"gblur=sigma={wide:.2f}:steps=2,{scale(outer.width, outer.height, 'bicubic')}[halo]",
        "[sharp][inner]blend=all_mode=screen:all_opacity=0.19[glow]",
        f"[glow][halo]blend=all_mode=screen:all_opacity=0.15,scale=out_color_matrix={matrix}:"
        f"out_range=tv:flags={SWS},format=yuv444p[bloom]",
    ])
    base = composite(base, "[bloom]", outer, "focused", mask(outer, title, "focus"))
    for name in ANCHORS:
        source, target = plan["sources"][name], plan["targets"][name]
        resize = (f",{scale(target.width, target.height, 'lanczos')}"
                  if (source.width, source.height) != (target.width, target.height) else "")
        graph.append(f"[{name}src]{source.filter()}{resize}[{name}anchor]")
        base = composite(base, f"[{name}anchor]", target, f"{name}moved", text_masks.get(name))
    graph.append(f"{base}format=yuv420p[v]")
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


def serial_plan(plan):
    return {"safe": astuple(plan["safe"]),
            "sources": {name: astuple(r) for name, r in plan["sources"].items()},
            "targets": {name: astuple(r) for name, r in plan["targets"].items()},
            "right_rail_overlap": plan["right_rail_overlap"]}


def anchor_checks(plan, reference, delivered):
    import numpy as np

    checks = {}
    for name, target in plan["targets"].items():
        source = plan["sources"][name]
        patch = source.crop(reference)
        y = np.minimum((np.arange(target.height) + 0.5) * source.height / target.height,
                       source.height - 1).astype(int)
        x = np.minimum((np.arange(target.width) + 0.5) * source.width / target.width,
                       source.width - 1).astype(int)
        expected = patch[np.ix_(y, x)].astype(np.float32)
        actual = target.crop(delivered).astype(np.float32)
        solid = np.ones(expected.shape, dtype=bool)
        if name == "captions":
            import cv2

            # Detect source strokes without consulting the relocation alpha.
            # Resample the source luma as well as the ink locations to account
            # for thin strokes losing peak brightness during downscaling.
            ink, boxes, _, _ = text_runs(patch, name, reference.shape[1])
            strokes = np.zeros_like(ink)
            for x0, y0, x1, y1 in boxes:
                strokes[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
            solid = strokes[np.ix_(y, x)]
            if patch.shape != expected.shape:
                expected = cv2.resize(patch.astype(np.float32), (target.width, target.height),
                                      interpolation=cv2.INTER_LINEAR)
        elif name == "pill":
            # Check for aligned bright strokes across individual scanlines.
            ink = expected >= max(120, float(np.median(expected)) + 55)
            solid.fill(False)
            left, right = target.width // 18, target.width - target.width // 18
            top, bottom = target.height // 4, target.height - target.height // 4
            gap = max(3, target.height // 2)
            for row in range(top, bottom):
                edges = np.flatnonzero(np.diff(ink[row, left:right], prepend=False, append=False))
                runs = edges.reshape(-1, 2) + left
                for first, second, third in zip(runs, runs[1:], runs[2:]):
                    if second[0] - first[1] <= gap and third[0] - second[1] <= gap:
                        solid[row, first[0]:third[1]] = ink[row, first[0]:third[1]]
        if not solid.any():
            checks[name] = {"present": False, "mean_abs_error": None, "bright_pixel_retention": None, "pass": True}
            continue
        error = np.abs(expected[solid] - actual[solid])
        mae = float(error.mean())
        # Bright anchor pixels must still be bright even when the rest of the crop
        # is mostly dark. A minor scaling and codec error is expected.
        standout = solid & (expected > max(105, float(expected[solid].mean()) + 35))
        if name in TEXT_ANCHORS:
            standout = solid
        required = expected[standout] - 50
        if name == "captions":
            required = np.maximum(required, float(np.median(actual)) + 30)
        visible = float((actual[standout] >= required).mean()) if standout.any() else None
        checks[name] = {"present": True, "mean_abs_error": round(mae, 3),
                        "bright_pixel_retention": None if visible is None else round(visible, 3),
                        "pass": (name in TEXT_ANCHORS or mae <= 12) and (visible is None or visible >= 0.72)}
    return checks


def leftover_checks(path, info, plan):
    """Sample the encoded picture for anchor edges and backing left at source."""
    import numpy as np

    width, height = info["width"], info["height"]
    last = info["frames"] - 1
    times = [n / 10 for n in range(16)] + [3, 20, 45]
    indices = sorted({min(last, round(time * info["fps"])) for time in times})
    select = "+".join(f"eq(n,{index})" for index in indices)
    raw = ffmpeg("-v", "error", "-i", path, "-map", "0:v:0", "-vf",
                 f"select='{select}',format=gray", "-frames:v", len(indices),
                 "-fps_mode", "passthrough", "-f", "rawvideo", "-").stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, height, width)
    if len(frames) != len(indices):
        raise ValueError("incomplete leftover analysis")

    samples = []
    for index, frame in zip(indices, frames):
        anchors = {}
        for name in ANCHORS:
            inner, outer, border = erase_geometry(plan["sources"][name], width, height)
            if any(outer.overlaps(rect) for rect in (*plan["targets"].values(), plan["sources"]["title"])):
                anchors[name] = {"pass": True, "skipped": "overlaps visible artwork"}
                continue
            bands = [frame[lo:hi, inner.x0:inner.x1].astype(np.float32)
                     for lo, hi in ((max(0, outer.y0 - border), outer.y0),
                                    (outer.y1, min(height, outer.y1 + border))) if hi > lo]
            above, below = bands[0].mean(axis=0), bands[-1].mean(axis=0)
            weight = (np.arange(inner.y0, inner.y1) + 0.5 - outer.y0)[:, None] / outer.height
            expected = above * (1 - weight) + below * weight
            actual = inner.crop(frame).astype(np.float32)
            # Ignore single-pixel codec noise, and allow natural contrast in
            # the surrounding strips when scoring a textured background.
            stride = max(1, round(border / 3))

            def edge_energy(patch):
                changes = (patch[stride:] - patch[:-stride], patch[:, stride:] - patch[:, :-stride])
                return max((float(np.quantile(np.abs(diff), 0.95))
                            for diff in changes if diff.size), default=0)

            edge = edge_energy(actual)
            background_edge = max(edge_energy(band) for band in bands)
            residual = np.abs(actual - expected)
            step = float(np.quantile(residual, 0.95))
            background_step = max(float(np.quantile(np.abs(band - band.mean(axis=0)), 0.95))
                                  for band in bands)
            anchors[name] = {"edge": round(edge, 3), "border_edge": round(background_edge, 3),
                             "luma_step": round(step, 3), "border_luma_step": round(background_step, 3),
                             "pass": edge <= background_edge + 6 and step <= background_step + 12}
        samples.append({"frame": index, "time_seconds": float(index / info["fps"]), "anchors": anchors})
    return {"pass": all(anchor["pass"] for sample in samples for anchor in sample["anchors"].values()),
            "samples": samples}


def audio_passes(stats):
    peak = stats["TP_dBTP"]
    return abs(stats["I_LUFS"] + 14) <= 0.5 and peak is not None and peak <= -1.0


def check(out, reference, layout=None, cover_frame=None):
    from sfx_cues import local_file, loudness

    out, reference = local_file(out), local_file(reference)
    metadata = sidecar(out)
    artifact = None
    if metadata.is_file():
        recorded = json.loads(metadata.read_text())
        artifact = verify_artifact(out, recorded)
        if not artifact["pass"]:
            return {"artifact": artifact, "pass": False}
        layout = layout or recorded["layout"]
        if cover_frame is None:
            cover_frame = recorded["cover"]["frame"]
    elif cover_frame is None:
        return {"artifact": {"pass": False, "error": "missing finish report"}, "pass": False}
    source, result = probe(reference), probe(out)
    width, height = source["width"], source["height"]
    same_size = (width, height) == (result["width"], result["height"])
    source_frame0 = gray_frames(reference, width, height, 1)[0]
    output_frame0 = gray_frames(out, result["width"], result["height"], 1)[0]
    original, finished = luma(source_frame0), luma(output_frame0)
    layout = layout_path(source, layout)
    plan = plan_layout(layout, width, height) if layout else None
    if plan and same_size:
        i = select_cover(reference, source, plan, original) if cover_frame is None else cover_frame
        anchor_source = gray_frames(reference, width, height, 1, i)[0] if i else source_frame0
        checks = anchor_checks(plan, anchor_source, output_frame0)
        safe = {"pass": placement_passes(plan) and all(c["pass"] for c in checks.values()),
                **serial_plan(plan), "frame0_anchor_checks": checks}
    else:
        safe = {"pass": same_size, "skipped": plan is None}
    leftovers = leftover_checks(out, result, plan) if plan and same_size else {"pass": same_size, "skipped": True}
    frame0 = {"source": original, "output": finished, "pass": cover_passes(finished, original)}
    stats = loudness(out) if result["audio"] else None
    audio_ok = bool(stats and audio_passes(stats) and result["audio"]["codec_name"] == "aac"
                    and result["audio"]["sample_rate"] == "48000")
    frame_counts = (source["frames"], result["frames"])
    source_starts, result_starts = stream_offsets(source), stream_offsets(result)
    source_offset, result_offset = (video - audio for video, audio in (source_starts, result_starts))
    one_frame = float(1 / source["fps"])
    sync_ok = not source["audio"] or (
        bool(result["audio"]) and abs(source_offset - result_offset) <= one_frame and
        all(abs(a - b) <= one_frame for a, b in zip(source_starts, result_starts))
    )
    timing = {"source_video_start": source["video_start"], "output_video_start": result["video_start"],
              "source_audio_start": stream_start(source["audio"]), "output_audio_start": stream_start(result["audio"]),
              "source_av_offset": source_offset if source["audio"] else None,
              "output_av_offset": result_offset if result["audio"] else None,
              "source_frames": frame_counts[0], "output_frames": frame_counts[1],
              "source_seconds": source["duration"], "output_seconds": result["duration"],
              "source_fps": str(source["fps"]), "output_fps": str(result["fps"]),
              "pass": (sync_ok and same_size and source["fps"] == result["fps"] and
                       frame_counts[0] == frame_counts[1] and
                       abs(source["duration"] - result["duration"]) < 0.001)}
    report = {"frame0": frame0, "safe_zone": safe, "leftovers": leftovers,
              "loudness": {"after": stats, "pass": audio_ok}, "timing": timing,
              "pass": frame0["pass"] and safe["pass"] and leftovers["pass"] and audio_ok and timing["pass"]}
    if artifact is not None:
        report["artifact"] = artifact
    return report


def render_picture(video, work, info, plan, cover, hold):
    width, height = info["width"], info["height"]
    if plan:
        write_text_masks(video, work, info, plan, cover, hold)
    graph, masks = video_graph(width, height, plan, cover, hold, work, info["matrix"], info["fps"])
    cover_limit = (cover + 2) / info["fps"] + max(0, info["video_start"] - (info["format_start"] or 0))
    cmd = ["-v", "error", "-y", "-i", video, "-t", f"{cover_limit:.9f}", "-i", video]
    for mask_args in masks:
        cmd += mask_args
    color_flags = {"color_space": "-colorspace", "color_transfer": "-color_trc", "color_primaries": "-color_primaries"}
    tags = [arg for name, tag in info["color_tags"].items() for arg in (color_flags[name], tag)]
    if plan:
        tags += ["-color_range", "tv"]
    picture = work / "picture.mp4"
    ffmpeg(*cmd, "-filter_complex_threads", 3, "-filter_complex", graph, "-map", "[v]",
           "-c:v", "libx264", "-preset", "fast", "-crf", 17, "-pix_fmt", "yuv420p",
           "-fps_mode", "passthrough", *tags, picture, cwd=work)
    return picture


def master(picture, premix_path, output, before, starts):
    from sfx_cues import loudness, mastering_filter

    gain = -14 - before["I_LUFS"]
    ceiling = -1.45
    video_start, audio_start = starts
    # Each attempt starts from the unmastered mix. The video is stream-copied.
    for attempt in range(1, 5):
        encode = ["-af", mastering_filter(gain, ceiling), "-c:a", "aac",
                  "-b:a", "256k", "-ar", "48000"]
        audio_input = premix_path
        if audio_start:
            # MP4 skips the encoded priming packet with a zero-based edit.
            # Remove that packet before moving this track away from zero,
            # where it would otherwise be presented as early audio.
            encoded = premix_path.with_name("encoded.m4a")
            audio_input = premix_path.with_name("without-priming.m4a")
            ffmpeg("-v", "error", "-y", "-i", premix_path, *encode, encoded)
            ffmpeg("-v", "error", "-y", "-i", encoded, "-ss", 0, "-c:a", "copy", audio_input)
            encode = ["-c:a", "copy"]
        ffmpeg("-v", "error", "-y", "-copyts",
               "-itsoffset", f"{video_start:.9f}", "-i", picture,
               "-itsoffset", f"{audio_start:.9f}", "-i", audio_input, "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", *encode, "-movflags", "+faststart", output)
        measured = loudness(output)
        if audio_passes(measured) or attempt == 4:
            break
        peak = measured["TP_dBTP"]
        if peak is not None and peak > -1:
            ceiling -= peak + 1.2
        if abs(measured["I_LUFS"] + 14) > 0.5:
            gain += -14 - measured["I_LUFS"]
    return {"attempts": attempt, "static_gain_db": round(gain, 4), "limiter_ceiling_db": round(ceiling, 4)}


def run(video, out, *, layout=None, cover_hold=None, scenes=None):
    if not enabled():
        print(DISABLED, file=sys.stderr)
        return None
    from collections import Counter

    from sfx_cues import cue_events, load_sounds, local_file, loudness, plan_cues, premix, render_stem

    video, out = local_file(video), Path(out).resolve()
    scenes = local_file(scenes) if scenes else None
    if video == out:
        raise ValueError("output path must differ from input")
    if cover_hold is not None and (not math.isfinite(cover_hold) or cover_hold <= 0):
        raise ValueError("--cover-hold must be a positive number of seconds")
    info = probe(video)
    width, height = info["width"], info["height"]
    if min(width, height) < 8 or width % 2 or height % 2 or not info["fps"] or not info["duration"] > 0:
        raise ValueError("finish pass needs even video dimensions and a valid frame rate and duration")
    starts = stream_offsets(info)
    layout = layout_path(info, layout)
    if layout is None:
        print("finish pass: no layout for this aspect, skipping anchor relocation and title effects",
              file=sys.stderr)
    plan = plan_layout(layout, width, height) if layout else None
    if plan and plan["right_rail_overlap"]:
        print("finish pass: TikTok right rail advisory: " + ", ".join(plan["right_rail_overlap"]), file=sys.stderr)
    original = luma(gray_frames(video, width, height, 1)[0])
    cover = select_cover(video, info, plan, original)
    hold = math.ceil(cover_hold * info["fps"]) if cover_hold is not None else 1
    hold = min(hold, info["frames"])
    sounds = load_sounds()
    cues = plan_cues(**cue_events(video, info["duration"], float(info["fps"]), scenes))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".finish-pass-", dir=out.parent) as temporary:
        work = Path(temporary)
        stem, mix, candidate = (work / name for name in ("stem.f32", "premix.wav", "finished.mp4"))
        cue_offset = starts[0] - starts[1]
        render_stem(stem, info["duration"] + max(0, cue_offset), cues, sounds, offset=cue_offset)
        premix(video, stem, mix, bool(info["audio"]))
        before = loudness(mix)
        if before["TP_dBTP"] is None:
            raise ValueError("cannot master a silent mix")
        picture = render_picture(video, work, info, plan, cover, hold)
        mastering = master(picture, mix, candidate, before, starts)
        report = check(candidate, video, layout=layout, cover_frame=cover)
        counts = Counter(cue.sound for cue in cues)
        report.update({
            "artifact": artifact_identity(candidate),
            "flag": os.environ["REELSMITH_FINISH_PASS"],
            "layout": str(layout) if layout else None,
            "cover": {"frame": cover, "time_seconds": float(cover / info["fps"]), "hold_frames": hold},
            "cue_counts": {name: counts[name] for name in sounds},
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
        # Publish the verified media first. An interruption before the report
        # rename leaves a missing or mismatched identity that check rejects.
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
            raise ValueError("published MP4 does not match finish report")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("run")
    render.add_argument("video")
    render.add_argument("--out", required=True, type=Path)
    render.add_argument("--scenes", type=Path, help="optional PySceneDetect CSV")
    render.add_argument("--cover-hold", type=float, help="hold in seconds; defaults to one frame")
    verify = sub.add_parser("check")
    verify.add_argument("video")
    verify.add_argument("--reference", required=True)
    for command in (render, verify):
        command.add_argument("--layout", type=Path, help="fractional source rectangles")
    args = parser.parse_args()
    try:
        if args.command == "run":
            report = run(args.video, args.out, layout=args.layout, cover_hold=args.cover_hold, scenes=args.scenes)
        else:
            report = check(args.video, args.reference, layout=args.layout)
    except (ValueError, KeyError, TypeError, OSError, ImportError) as error:
        print(f"finish pass: {error}", file=sys.stderr)
        return 1
    if report is not None:
        print(json.dumps(report, indent=2))
    return 0 if report is None or report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
