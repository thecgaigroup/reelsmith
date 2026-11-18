"""Tests for beats.py beat_lock: share of cuts on a beat against chance. No audio or ffmpeg needed."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from beats import beat_lock  # noqa: E402

BEATS = [round(i * 0.5, 3) for i in range(121)]  # 120 BPM for 60 s


def test_cuts_on_the_beat_are_locked():
    cuts = [2.0, 4.01, 6.5, 8.0, 10.02, 12.5, 15.0, 17.49]
    r = beat_lock(BEATS, cuts)
    assert r["on_beat"] == 8 and r["locked"] and r["verdict"] == "beat-synced edit"
    assert 0.2 < r["chance"] < 0.35  # 2 x 70 ms per 500 ms beat


def test_offbeat_cuts_are_not_locked():
    cuts = [2.25, 4.25, 6.75, 8.25, 10.25, 12.75]
    r = beat_lock(BEATS, cuts)
    assert r["on_beat"] == 0 and not r["locked"]


def test_random_cuts_sit_near_chance():
    rnd = random.Random(7)
    cuts = sorted(rnd.uniform(1, 59) for _ in range(400))
    r = beat_lock(BEATS, cuts)
    assert abs(r["ratio"] - r["chance"]) < 0.08 and not r["locked"]


def test_dense_grid_raises_chance():
    dense = [round(i * 0.1, 3) for i in range(601)]  # every 100 ms: everything is "near a beat"
    r = beat_lock(dense, [2.03, 4.05, 6.07, 8.01, 10.04])
    assert r["chance"] == 1.0 and not r["locked"]


def test_only_hard_cuts_from_cuts_json_count():
    rows = [{"t": 2.0, "kind": "cut"}, {"t": 2.2, "kind": "flash"}, {"t": 4.0, "kind": "cut"},
            {"t": 5.3, "kind": "fast"}, {"t": 6.0, "kind": "cut"}, {"t": 8.0, "kind": "cut"}]
    r = beat_lock(BEATS, rows)
    assert r["cuts"] == 4 and r["on_beat"] == 4 and r["locked"]


def test_offset_moves_picture_onto_music_clock():
    cuts = [3.0 + b for b in (2.0, 4.0, 6.0, 8.0, 10.0)]  # music starts 3.2 s into the picture
    assert not beat_lock(BEATS, [c + 0.2 for c in cuts], offset=0.0)["locked"]
    assert beat_lock(BEATS, [c + 0.2 for c in cuts], offset=3.2)["locked"]


def test_median_offset_reports_early_cuts():
    cuts = [b - 0.033 for b in (2.0, 4.0, 6.0, 8.0, 10.0)]  # one frame early at 30 fps
    r = beat_lock(BEATS, cuts)
    assert r["locked"] and -40 < r["median_offset_ms"] < -25


def test_too_few_cuts_gives_no_verdict():
    r = beat_lock(BEATS, [2.0, 4.0])
    assert not r["locked"] and r["verdict"] == "not enough cuts"


def test_empty_inputs():
    assert beat_lock([], [1.0])["verdict"] == "no beats"
    assert beat_lock(BEATS, [])["verdict"] == "no cuts"
