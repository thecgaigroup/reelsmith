#!/usr/bin/env python3
"""Test that caption bottom edges stay above y=1248 (within safe zone) on 1080x1920."""
import json
import re
import tempfile
from pathlib import Path
import subprocess


def test_caption_bottom_edge_in_safe_zone():
    """With --safe-layout on 1080x1920, all caption lines' bottom edges must be at y >= 1248."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test words
        words = [
            {"text": "This", "start": 0.0, "end": 0.3},
            {"text": "is", "start": 0.3, "end": 0.5},
            {"text": "a", "start": 0.5, "end": 0.6},
            {"text": "test", "start": 0.6, "end": 1.0}
        ]
        words_file = tmpdir / "words.json"
        words_file.write_text(json.dumps(words))
        
        # Generate with safe layout enabled
        base_safe = tmpdir / "safe"
        subprocess.run([
            "python3", "scripts/captions.py", "build",
            "--words", str(words_file),
            "--aspect", "9:16",
            "--style", "boxed",
            "--safe-layout",
            "-o", str(base_safe)
        ], check=True, capture_output=True)
        
        # Read ASS file and check MarginV (vertical margin from bottom)
        ass_safe = (base_safe.parent / f"{base_safe.name}.ass").read_text()
        
        # Extract MarginV from Style line
        # Format: Style: Default,Font,Size,...,MarginL,MarginR,MarginV,Encoding
        style_match = re.search(r'Style: Default,[^,]+,\d+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,\d+,\d+,\d+,\d+,\d+,\d+,\d+,\d+,(\d+),(\d+),(\d+),\d+', ass_safe)
        
        if not style_match:
            raise AssertionError("Could not parse Style line from ASS file")
        
        margin_v = int(style_match.group(3))  # MarginV is the 3rd captured group
        
        # margin_v should be 672 (bottom safe zone)
        # Caption bottom edge is at y = 1920 - margin_v
        caption_bottom_y = 1920 - margin_v
        safe_zone_bottom_y = 1920 - 672  # = 1248
        
        assert margin_v == 672, f"MarginV should be 672px, got {margin_v}px"
        assert caption_bottom_y <= safe_zone_bottom_y, \
            f"Caption bottom edge at y={caption_bottom_y} exceeds safe zone limit (y={safe_zone_bottom_y})"
        
        print(f"✓ Caption bottom edge test passed: MarginV={margin_v}px, bottom at y={caption_bottom_y} (safe zone y >= {safe_zone_bottom_y})")


if __name__ == "__main__":
    import os
    import sys
    os.chdir(Path(__file__).parent.parent)
    
    test_caption_bottom_edge_in_safe_zone()
    print("\n✅ Caption bottom edge test passed!")
