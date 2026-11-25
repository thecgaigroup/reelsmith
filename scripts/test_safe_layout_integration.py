#!/usr/bin/env python3
"""Integration tests for safe layout: render videos and verify positioning and quality."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cmd(cmd, check=True):
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"stdout: {result.stdout}", file=sys.stderr)
        print(f"stderr: {result.stderr}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.returncode, result.stdout, result.stderr


def test_caption_flag_produces_different_output():
    """Verify --safe-layout flag changes ASS output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create minimal words.json
        words = [
            {"text": "This", "start": 0.0, "end": 0.3},
            {"text": "is", "start": 0.3, "end": 0.5},
            {"text": "a", "start": 0.5, "end": 0.6},
            {"text": "test", "start": 0.6, "end": 1.0}
        ]
        words_file = tmpdir / "words.json"
        words_file.write_text(json.dumps(words))
        
        # Generate without safe layout
        base_legacy = tmpdir / "legacy"
        run_cmd(["python3", "scripts/captions.py", "build",
                "--words", str(words_file),
                "--aspect", "9:16",
                "--style", "boxed",
                "-o", str(base_legacy)])
        
        # Generate with safe layout
        base_safe = tmpdir / "safe"
        run_cmd(["python3", "scripts/captions.py", "build",
                "--words", str(words_file),
                "--aspect", "9:16",
                "--style", "boxed",
                "--safe-layout",
                "-o", str(base_safe)])
        
        # Read ASS files
        ass_legacy = (base_legacy.parent / f"{base_legacy.name}.ass").read_text()
        ass_safe = (base_safe.parent / f"{base_safe.name}.ass").read_text()
        
        # They should be different
        assert ass_legacy != ass_safe, "Safe layout should produce different ASS output"
        
        # Check specific differences
        # Legacy uses approximately 86px horizontal margins and 691px vertical
        assert ",86,86,691," in ass_legacy or ",86,86,692," in ass_legacy, \
            "Legacy should use ~86px horizontal, 691px vertical margins"
        
        # Safe layout uses 120px left, 310px right, 672px vertical (keeps bottom 35% clear)
        assert ",120,310,672," in ass_safe, \
            "Safe layout should use 120px left, 310px right, 672px vertical margins"
        
        print("✓ Caption flag produces different output test passed")


def test_safe_layout_backward_compatibility():
    """Verify default (no flag) produces same output as legacy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        words = [{"text": "Test", "start": 0.0, "end": 1.0}]
        words_file = tmpdir / "words.json"
        words_file.write_text(json.dumps(words))
        
        # Generate default (no flag)
        base_default = tmpdir / "default"
        run_cmd(["python3", "scripts/captions.py", "build",
                "--words", str(words_file),
                "--aspect", "9:16",
                "-o", str(base_default)])
        
        # Read and check it uses legacy positioning
        ass_default = (base_default.parent / f"{base_default.name}.ass").read_text()
        assert ",86,86,691," in ass_default or ",86,86,692," in ass_default, \
            "Default (no flag) should use legacy margins"
        
        print("✓ Safe layout backward compatibility test passed")


def test_safe_layout_only_affects_9x16():
    """Verify flag has no effect on 16:9 or 1:1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        words = [{"text": "Test", "start": 0.0, "end": 1.0}]
        words_file = tmpdir / "words.json"
        words_file.write_text(json.dumps(words))
        
        for aspect in ["16:9", "1:1"]:
            # Without flag
            base_off = tmpdir / f"{aspect}-off"
            run_cmd(["python3", "scripts/captions.py", "build",
                    "--words", str(words_file),
                    "--aspect", aspect,
                    "-o", str(base_off)])
            
            # With flag
            base_on = tmpdir / f"{aspect}-on"
            run_cmd(["python3", "scripts/captions.py", "build",
                    "--words", str(words_file),
                    "--aspect", aspect,
                    "--safe-layout",
                    "-o", str(base_on)])
            
            # Should be identical
            ass_off = (base_off.parent / f"{base_off.name}.ass").read_text()
            ass_on = (base_on.parent / f"{base_on.name}.ass").read_text()
            
            assert ass_off == ass_on, \
                f"Safe layout should have no effect on {aspect}"
        
        print("✓ Safe layout only affects 9:16 test passed")


def test_frame0_quality_requirements():
    """Verify frame 0 quality checker can run (needs actual video)."""
    # This is a dry-run test that verifies the checker script exists and can be imported
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from test_frame0_cover import check_frame0_cover, check_frame0_luma_requirements
        print("✓ Frame 0 quality checker module loads correctly")
    except ImportError as e:
        print(f"✗ Failed to import frame 0 checker: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)  # Run from repo root
    
    print("Running safe layout integration tests...\n")
    
    test_caption_flag_produces_different_output()
    test_safe_layout_backward_compatibility()
    test_safe_layout_only_affects_9x16()
    test_frame0_quality_requirements()
    
    print("\n✅ All safe layout integration tests passed!")
