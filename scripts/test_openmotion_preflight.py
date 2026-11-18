"""Tests for openmotion_preflight.py: OpenMotion Studio structure rules, checked statically. No Node, Chrome or render."""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openmotion_preflight import check, main  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "openmotion-example"


def _copy(tmp_path):
    dst = tmp_path / "proj"
    shutil.copytree(EXAMPLE, dst, ignore=shutil.ignore_patterns("brand", ".hyperframes", "out", "renders"))
    return dst


def _edit(path, old, new):
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new, 1))


def test_shipped_example_is_clean():
    assert check(EXAMPLE) == []
    assert main([str(EXAMPLE)]) == 0


def test_nested_root_clip_needs_a_subcomposition():
    # Same rule OpenMotion's Studio lint reports as nested_structure_needs_subcomposition.
    findings = check(REPO / "hyperframes-example")
    assert findings and all("sub-composition" in f for f in findings)


def test_layout_tween_fails(tmp_path):
    p = _copy(tmp_path)
    _edit(p / "compositions/title.html", "{ opacity: 0, x: -40 }", "{ opacity: 0, letterSpacing: '0.6em' }")
    assert any("letterSpacing" in f for f in check(p))


def test_wall_clock_fails(tmp_path):
    p = _copy(tmp_path)
    _edit(p / "compositions/title.html", "ease: 'none' }, 0);", "ease: 'none' }, Math.random());")
    assert any("randomness" in f for f in check(p))


def test_unregistered_timeline_fails(tmp_path):
    p = _copy(tmp_path)
    _edit(p / "compositions/title.html", "window.__timelines['title-card'] = tl;", "")
    assert any("does not register" in f for f in check(p))


def test_duration_mismatch_fails(tmp_path):
    p = _copy(tmp_path)
    _edit(p / "compositions/title.html", 'data-duration="6.5"', 'data-duration="5"')
    assert any("data-duration differs" in f for f in check(p))


def test_missing_mount_and_unreadable_project(tmp_path):
    p = _copy(tmp_path)
    (p / "compositions/title.html").unlink()
    assert any("missing file" in f for f in check(p))
    assert main([str(tmp_path / "nope")]) == 2
