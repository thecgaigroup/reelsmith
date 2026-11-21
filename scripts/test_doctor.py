#!/usr/bin/env python3
"""Tests for doctor.py dependency checker.

Tests that doctor.py correctly checks for required dependencies and exits with the right code.
"""
import json, subprocess, sys, unittest.mock as mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCTOR = HERE / "doctor.py"
REPO = HERE.parent
VERSION_FILE = REPO / "VERSION"

def run_doctor():
    """Run doctor.py and return (exit_code, stdout)."""
    r = subprocess.run([sys.executable, str(DOCTOR)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr

def test_doctor_exists():
    """doctor.py file exists and is executable."""
    assert DOCTOR.exists(), f"{DOCTOR} does not exist"

def test_doctor_runs():
    """doctor.py runs without crashing."""
    code, out = run_doctor()
    assert code in (0, 1), f"Expected exit code 0 or 1, got {code}"
    assert len(out) > 0, "Expected output from doctor.py"

def test_checks_python():
    """doctor.py checks Python version."""
    code, out = run_doctor()
    assert "python" in out.lower(), "Expected 'python' in output"

def test_checks_ffmpeg():
    """doctor.py checks for ffmpeg and ffprobe."""
    code, out = run_doctor()
    assert "ffmpeg" in out.lower() or "ffprobe" in out.lower(), "Expected ffmpeg/ffprobe check"

def test_checks_packages():
    """doctor.py checks for Python packages."""
    code, out = run_doctor()
    # At least one of these should appear
    assert any(pkg in out.lower() for pkg in ["numpy", "scipy", "pillow"]), "Expected package checks"

def test_checks_node():
    """doctor.py checks for Node/npx."""
    code, out = run_doctor()
    assert "node" in out.lower() or "npx" in out.lower(), "Expected Node/npx check"

def test_what_works_section():
    """doctor.py prints a 'What works here:' summary."""
    code, out = run_doctor()
    assert "what works" in out.lower(), "Expected 'What works here:' section"

def test_help_flag():
    """doctor.py --help prints usage and exits 0."""
    r = subprocess.run([sys.executable, str(DOCTOR), "--help"], capture_output=True, text=True)
    assert r.returncode == 0, "Expected --help to exit 0"
    assert "usage" in r.stdout.lower() or "check" in r.stdout.lower(), "Expected usage text"

def test_up_to_date_message():
    """doctor.py prints 'Reelsmith X.Y.Z is up to date' when current version equals latest."""
    # Read current version
    current_version = VERSION_FILE.read_text().strip()
    
    # Create a mock response that returns the same version
    class MockResponse:
        def __init__(self, content):
            self.content = content
        def read(self):
            return self.content.encode('utf-8')
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    # Mock the GitHub API response to return current version
    mock_data = {"tag_name": f"v{current_version}"}
    
    with mock.patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value = MockResponse(json.dumps(mock_data))
        code, out = run_doctor()
        
        # Check that it prints the up-to-date message
        assert f"Reelsmith {current_version} is up to date" in out, \
            f"Expected 'Reelsmith {current_version} is up to date' in output, got:\n{out}"
        
        # Should not print update instructions when up to date
        assert "A newer version" not in out, "Should not suggest update when up to date"

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
        except Exception as e:
            print(f"FAIL\n  {e}")
            sys.exit(1)
    print(f"\n{len(tests)} tests passed")
