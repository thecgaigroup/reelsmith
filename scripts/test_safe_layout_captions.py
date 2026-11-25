#!/usr/bin/env python3
"""Tests for safe-layout caption positioning."""
import json
import tempfile
from pathlib import Path

# Test that captions.py respects safe-layout flag
def test_caption_safe_layout_flag():
    """Safe layout flag should affect ASS caption positioning for 9:16."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from captions import to_ass
    
    # Simple test cues
    cues = [{"start": 0.5, "end": 2.0, "text": "Test caption", "lines": ["Test caption"], "words": [{"text": "Test", "start": 0.5, "end": 1.0}, {"text": "caption", "start": 1.0, "end": 2.0}]}]
    
    # Without safe layout (legacy)
    ass_legacy = to_ass(cues, "9:16", "boxed", brand=None, safe_layout=False)
    # Legacy uses 36% of 1920 = 691px margin_v
    assert "MarginV, Encoding" in ass_legacy
    # Check for legacy horizontal margins (8% of 1080 = 86)
    assert ",86,86,691," in ass_legacy or ",86,86,692," in ass_legacy, "Legacy should use ~86px horizontal, 691px vertical margins"
    
    # With safe layout enabled
    ass_safe = to_ass(cues, "9:16", "boxed", brand=None, safe_layout=True)
    # Safe layout uses 480 + 60 = 540px margin_v, and 120px left, 310px right (1080-770=310)
    assert ",120,310,540," in ass_safe, "Safe layout should use 120px left, 310px right, 540px bottom margins"
    
    # Verify they're different
    assert ass_legacy != ass_safe, "Safe layout should produce different output than legacy"
    
    print("✓ Safe layout caption positioning test passed")


def test_caption_band_width():
    """Caption band should be 650px wide (120 to 770) with safe layout."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "templates" / "_shared"))
    from safe_zones import SafeZones
    
    zones = SafeZones(1080, 1920, enabled=True)
    x_min, x_max = zones.get_caption_band()
    width = x_max - x_min
    
    assert width == 650, f"Caption band should be 650px wide, got {width}px"
    assert x_min == 120, f"Caption band should start at 120px, got {x_min}px"
    assert x_max == 770, f"Caption band should end at 770px, got {x_max}px"
    
    print("✓ Caption band width test passed")


def test_safe_layout_only_affects_9x16():
    """Safe layout should only affect 9:16 aspect ratio."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from captions import to_ass
    
    cues = [{"start": 0.5, "end": 2.0, "text": "Test", "lines": ["Test"], "words": [{"text": "Test", "start": 0.5, "end": 2.0}]}]
    
    # 16:9 should be unaffected
    ass_16x9_off = to_ass(cues, "16:9", "clean", brand=None, safe_layout=False)
    ass_16x9_on = to_ass(cues, "16:9", "clean", brand=None, safe_layout=True)
    assert ass_16x9_off == ass_16x9_on, "Safe layout should not affect 16:9"
    
    # 1:1 should be unaffected
    ass_1x1_off = to_ass(cues, "1:1", "clean", brand=None, safe_layout=False)
    ass_1x1_on = to_ass(cues, "1:1", "clean", brand=None, safe_layout=True)
    assert ass_1x1_off == ass_1x1_on, "Safe layout should not affect 1:1"
    
    # 9:16 should be affected
    ass_9x16_off = to_ass(cues, "9:16", "clean", brand=None, safe_layout=False)
    ass_9x16_on = to_ass(cues, "9:16", "clean", brand=None, safe_layout=True)
    assert ass_9x16_off != ass_9x16_on, "Safe layout should affect 9:16"
    
    print("✓ Safe layout aspect ratio specificity test passed")


if __name__ == "__main__":
    test_caption_safe_layout_flag()
    test_caption_band_width()
    test_safe_layout_only_affects_9x16()
    print("\nAll safe layout caption tests passed!")
