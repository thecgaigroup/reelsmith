import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from finish_pass import enabled

SCRIPTS = Path(__file__).resolve().parent


@pytest.mark.parametrize("value,expected", [
    (None, False), ("", False), ("0", False), ("false", False), ("1", True),
    ("TRUE", True), ("On", True), ("YeS", True), ("2", False), ("on ", False),
])
def test_truth_table(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("REELSMITH_FINISH_PASS", raising=False)
    else:
        monkeypatch.setenv("REELSMITH_FINISH_PASS", value)
    assert enabled() is expected


def test_disabled_run_does_not_write(monkeypatch, tmp_path):
    monkeypatch.setenv("REELSMITH_FINISH_PASS", "0")
    target = tmp_path / "untouched" / "out.mp4"
    result = subprocess.run([sys.executable, str(SCRIPTS / "finish_pass.py"), "run", "missing.mp4",
                             "--out", str(target)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "finish pass disabled (REELSMITH_FINISH_PASS not set)" in result.stderr
    assert not target.parent.exists()


def test_export_off_matches_main_argv_and_is_byte_identical(monkeypatch, tmp_path):
    src, out = tmp_path / "src.mp4", tmp_path / "delivery"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=90x160:r=10:d=1",
                    "-c:v", "libx264", str(src)], check=True)
    # Isolate the actual CLI. Reject even an attempted import and record its real ffmpeg arguments.
    harness = r"""
import importlib.abc
import json
import runpy
import subprocess
import sys

class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "finish_pass":
            raise AssertionError("export imported finish_pass with the flag off")

real_run = subprocess.run
def record(argv, *args, **kwargs):
    if argv[0] == "ffmpeg":
        print(json.dumps(argv), file=sys.stderr)
    return real_run(argv, *args, **kwargs)

sys.meta_path.insert(0, Guard())
subprocess.run = record
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
"""
    monkeypatch.setenv("PYTHONPATH", str(SCRIPTS))
    expected = json.loads((SCRIPTS / "fixtures/finish_pass/export_reels_argv.json").read_text())
    outputs = []
    for value in (None, "0"):
        env = os.environ.copy()
        env.pop("REELSMITH_FINISH_PASS", None)
        if value is not None:
            env["REELSMITH_FINISH_PASS"] = value
        result = subprocess.run([sys.executable, "-c", harness, str(SCRIPTS / "export.py"), "run",
                                 str(src), "--preset", "reels", "--out", str(out), "--unreviewed"],
                                capture_output=True, text=True, check=True, env=env)
        commands = [json.loads(line) for line in result.stderr.splitlines()]
        normalized = [[arg.replace(str(src), "@SRC").replace(str(out), "@OUT") for arg in cmd]
                      for cmd in commands]
        assert normalized == expected
        outputs.append(sorted((p.name, p.read_bytes()) for p in out.iterdir()))
    assert outputs[0] == outputs[1]
