"""Unit tests for validate_music_license.py.

Run: python3 -m pytest scripts/test_validate_music_license.py

Adapted from codepawl/creator-generalist (MIT), commit d3ab529a, read 2026-11-14.
"""

import json
import pathlib
import subprocess
import sys

# Assume pytest is available (it's in requirements.txt or can be installed)
try:
    import pytest
except ImportError:
    print("pytest not found. Install it with: pip install pytest")
    sys.exit(1)


SCRIPT = pathlib.Path(__file__).resolve().parent / "validate_music_license.py"


def run_validator(manifest_path):
    """Run the validator script and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifest_path)],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.returncode, result.stdout, result.stderr


def test_cc0_passes(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track1.mp3",
            "title": "Track 1",
            "author": "Artist",
            "license": "CC0",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 0, stdout + stderr
    assert "1 of 1 tracks pass" in stdout


def test_cc_by_with_credit_passes(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track2.mp3",
            "title": "Track 2",
            "author": "Artist Name",
            "license": "CC BY 4.0",
            "credit": "Artist Name (example.com), CC BY 4.0",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 0, stdout + stderr
    assert "1 of 1 tracks pass" in stdout


def test_cc_by_without_credit_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track3.mp3",
            "title": "Track 3",
            "author": "Artist",
            "license": "CC BY 3.0",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "requires a credit line" in stdout


def test_unknown_license_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track4.mp3",
            "title": "Track 4",
            "author": "Artist",
            "license": "Unknown License",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "not in allowlist" in stdout


def test_nc_license_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track5.mp3",
            "title": "Track 5",
            "author": "Artist",
            "license": "CC BY-NC 4.0",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "NC" in stdout


def test_nd_license_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track6.mp3",
            "title": "Track 6",
            "author": "Artist",
            "license": "CC BY-ND 4.0",
            "credit": "Artist (example.com)",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "ND" in stdout


def test_sa_license_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track7.mp3",
            "title": "Track 7",
            "author": "Artist",
            "license": "CC BY-SA 4.0",
            "credit": "Artist (example.com)",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "SA" in stdout


def test_missing_license_blocks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "track8.mp3",
            "title": "Track 8",
            "author": "Artist",
            "source": "https://example.com"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "BLOCKED" in stdout
    assert "license field is missing" in stdout


def test_mixed_tracks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([
        {
            "file": "good1.mp3",
            "title": "Good Track 1",
            "author": "Artist A",
            "license": "CC0"
        },
        {
            "file": "bad.mp3",
            "title": "Bad Track",
            "author": "Artist B",
            "license": "All Rights Reserved"
        },
        {
            "file": "good2.mp3",
            "title": "Good Track 2",
            "author": "Artist C",
            "license": "CC BY 4.0",
            "credit": "Artist C, CC BY 4.0"
        }
    ]), encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 1, stdout + stderr
    assert "2 of 3 tracks pass" in stdout
    assert "1 tracks BLOCKED" in stdout


def test_empty_manifest(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("[]", encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 0, stdout + stderr
    assert "empty" in stdout.lower()


def test_invalid_json(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{ not valid json }", encoding="utf-8")
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 2


def test_missing_file(tmp_path):
    manifest = tmp_path / "does-not-exist.json"
    
    exit_code, stdout, stderr = run_validator(manifest)
    assert exit_code == 2
    assert "not found" in stdout.lower()
