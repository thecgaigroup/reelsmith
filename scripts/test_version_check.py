#!/usr/bin/env python3
"""Tests for doctor.py version checking.

Tests version comparison logic by importing and mocking the check_version_update function.
"""
import io, json, sys, unittest.mock as mock, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def test_newer_version_available():
    """Detects when a newer version is available."""
    import doctor
    
    # Mock VERSION file to be 5.3.0 and GitHub to return 5.4.0
    with mock.patch("pathlib.Path.read_text", return_value="5.3.0\n"):
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = mock.MagicMock()
                mock_response.read.return_value = b'{"tag_name": "v5.4.0"}'
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response
                
                captured = io.StringIO()
                with mock.patch("sys.stdout", captured):
                    doctor.check_version_update()
                
                out = captured.getvalue()
                assert "newer version" in out.lower() or "5.4.0" in out, \
                    f"Expected update message, got: {out}"

def test_same_version():
    """Doesn't show update message when versions match."""
    import doctor
    
    with mock.patch("pathlib.Path.read_text", return_value="5.3.2\n"):
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = mock.MagicMock()
                mock_response.read.return_value = b'{"tag_name": "v5.3.2"}'
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response
                
                captured = io.StringIO()
                with mock.patch("sys.stdout", captured):
                    doctor.check_version_update()
                
                out = captured.getvalue()
                assert "newer version" not in out.lower(), \
                    f"Should not show update for same version, got: {out}"

def test_network_timeout():
    """Handles network timeout gracefully."""
    import doctor
    
    with mock.patch("pathlib.Path.read_text", return_value="5.3.2\n"):
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("urllib.request.urlopen", side_effect=Exception("timeout")):
                captured = io.StringIO()
                with mock.patch("sys.stdout", captured):
                    # Should not crash
                    doctor.check_version_update()
                
                out = captured.getvalue()
                assert "could not check" in out.lower(), \
                    f"Expected network error message, got: {out}"

def test_no_releases_fallback():
    """Falls back to main branch VERSION when no releases exist."""
    import doctor
    
    with mock.patch("pathlib.Path.read_text", return_value="5.2.0\n"):
        with mock.patch("pathlib.Path.exists", return_value=True):
            call_count = [0]
            
            def mock_urlopen_side_effect(req, timeout=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call (releases) fails
                    raise Exception("No releases")
                else:
                    # Second call (main VERSION) succeeds
                    mock_response = mock.MagicMock()
                    mock_response.read.return_value = b"5.3.2\n"
                    mock_response.__enter__.return_value = mock_response
                    return mock_response
            
            with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen_side_effect):
                captured = io.StringIO()
                with mock.patch("sys.stdout", captured):
                    doctor.check_version_update()
                
                out = captured.getvalue()
                assert "newer version" in out.lower() or "5.3" in out, \
                    f"Expected fallback to work, got: {out}"

def test_git_vs_zip_install():
    """Provides correct update command based on installation."""
    import doctor
    
    with mock.patch("pathlib.Path.read_text", return_value="5.3.0\n"):
        # Test with .git directory present (git install)
        def mock_exists(self):
            return ".git" in str(self) or "VERSION" in str(self)
        
        with mock.patch("pathlib.Path.exists", mock_exists):
            with mock.patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = mock.MagicMock()
                mock_response.read.return_value = b'{"tag_name": "v5.4.0"}'
                mock_response.__enter__.return_value = mock_response
                mock_urlopen.return_value = mock_response
                
                captured = io.StringIO()
                with mock.patch("sys.stdout", captured):
                    doctor.check_version_update()
                
                out = captured.getvalue()
                assert "git pull" in out or "download" in out, \
                    f"Expected update command, got: {out}"

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{len(tests)} tests passed")
