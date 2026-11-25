import shutil
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


def test_unset_flag_leaves_fresh_checkout_untouched(monkeypatch, tmp_path):
    monkeypatch.delenv("REELSMITH_FINISH_PASS", raising=False)
    monkeypatch.delenv("PYTHONDONTWRITEBYTECODE", raising=False)
    monkeypatch.delenv("PYTHONPYCACHEPREFIX", raising=False)
    scripts = tmp_path / "scripts"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    before = set(tmp_path.rglob("*"))
    result = subprocess.run([sys.executable, str(scripts / "finish_pass.py"), "run",
                             "missing.mp4", "--out", "out.mp4"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert set(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("url", ["http://example.invalid/x", "https://example.invalid/x",
                                 "tcp://example.invalid:1234", "file:///tmp/fake.mp4", "-"])
def test_finish_pass_rejects_nonlocal_inputs_before_subprocess(monkeypatch, tmp_path, url):
    import finish_pass as fp

    monkeypatch.setenv("REELSMITH_FINISH_PASS", "1")
    local = tmp_path / "local.mp4"
    local.touch()

    def unexpected(*args, **kwargs):
        pytest.fail("media tool invoked before local file validation")

    monkeypatch.setattr(subprocess, "run", unexpected)
    monkeypatch.setattr(subprocess, "Popen", unexpected)
    with pytest.raises(ValueError, match="local regular file"):
        fp.run(url, local)
    with pytest.raises(ValueError, match="local regular file"):
        fp.check(url, local)
    with pytest.raises(ValueError, match="local regular file"):
        fp.check(local, url)


def test_disabled_run_never_calls_a_media_tool(monkeypatch, tmp_path, capsys):
    import finish_pass as fp

    monkeypatch.delenv("REELSMITH_FINISH_PASS", raising=False)

    def unexpected(*args, **kwargs):
        pytest.fail("disabled finish pass invoked a subprocess")

    monkeypatch.setattr(subprocess, "run", unexpected)
    monkeypatch.setattr(subprocess, "Popen", unexpected)
    target = tmp_path / "unused" / "out.mp4"
    monkeypatch.setattr(sys, "argv", ["finish_pass.py", "run", "missing.mp4", "--out", str(target)])
    assert fp.main() == 0
    assert capsys.readouterr().err.strip() == fp.DISABLED
    assert not target.parent.exists()


def test_finish_modules_do_not_import_existing_repo_scripts():
    import ast

    local_modules = {path.stem for path in SCRIPTS.glob("*.py")}
    for name in ("finish_pass", "finish_pass_flag", "sfx_cues"):
        tree = ast.parse((SCRIPTS / f"{name}.py").read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0
                imports.add(node.module.split(".")[0])
        assert imports & local_modules <= {"finish_pass_flag", "sfx_cues"}
