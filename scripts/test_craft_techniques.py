#!/usr/bin/env python3
"""Tests for craft techniques: identity, dropout detection, sanitization, etc."""
import tempfile, subprocess, json, sys
from pathlib import Path

HERE = Path(__file__).parent

def make_test_video(out, dur=1, audio=False):
    """Create a minimal test video."""
    v = out / "v.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s=320x240:r=30:duration={dur}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(v)],
                   capture_output=True, check=True)
    if audio:
        a = out / "a.m4a"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
                        "-c:a", "aac", "-b:a", "128k", str(a)],
                       capture_output=True, check=True)
        test = out / "test.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(v), "-i", str(a),
                        "-c", "copy", "-shortest", str(test)],
                       capture_output=True, check=True)
        return test
    return v

# Test 1: Shared identity format
def test_shared_identity_format():
    """export.py and review.py use same identity format (size:mtime_ns:sha256)."""
    sys.path.insert(0, str(HERE))
    import export
    import review
    
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        test_file = out / "test.txt"
        test_file.write_text("hello world")
        
        export_id = export.file_identity(test_file)
        review_id = review.file_identity(test_file)
        
        assert export_id == review_id
        parts = export_id.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 64  # sha256
        print(f"  shared format verified")

# Test 2: Filter sanitizer
def test_filter_sanitizer():
    """Sanitize dangerous characters in filter graph inputs."""
    from review import sanitize_filter_input
    
    assert "\\'" in sanitize_filter_input("it's")
    assert "\\:" in sanitize_filter_input("C:/path")
    assert "\\\\" in sanitize_filter_input("back\\slash")
    assert sanitize_filter_input("safe text") == "safe text"
    print("  dangerous chars escaped")

if __name__ == "__main__":
    # Run all tests
    for name, obj in list(globals().items()):
        if name.startswith("test_") and callable(obj):
            print(f"Running {name}...")
            try:
                obj()
                print(f"✓ {name}")
            except Exception as e:
                print(f"✗ {name}: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
    print("\nAll tests passed!")
