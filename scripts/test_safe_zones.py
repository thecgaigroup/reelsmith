#!/usr/bin/env python3
"""Tests for safe_zones.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "templates" / "_shared"))

from safe_zones import SafeZones, get_safe_margins, get_caption_vpos


def test_safe_zones_disabled():
    """When disabled, all margins should be zero."""
    zones = SafeZones(1080, 1920, enabled=False)
    top, bottom, left, right = zones.get_margins()
    assert top == 0
    assert bottom == 0
    assert left == 0
    assert right == 0
    assert zones.get_caption_band() == (0, 1080)


def test_safe_zones_enabled_standard():
    """When enabled with standard 1080x1920, use exact pixel margins."""
    zones = SafeZones(1080, 1920, enabled=True)
    top, bottom, left, right = zones.get_margins()
    
    # Standard margins
    assert top == 220, f"Expected top margin 220px, got {top}"
    assert bottom == 672, f"Expected bottom margin 672px (35% keep-clear), got {bottom}"
    assert left == 120, f"Expected left margin 120px, got {left}"
    assert right == 310, f"Expected right margin 310px, got {right}"
    
    # Caption band
    x_min, x_max = zones.get_caption_band()
    assert x_min == 120, f"Expected caption x_min 120px, got {x_min}"
    assert x_max == 770, f"Expected caption x_max 770px, got {x_max}"
    assert x_max - x_min == 650, f"Caption band should be 650px wide"


def test_safe_zones_positions():
    """Badge and pill positions should be inside safe zones."""
    zones = SafeZones(1080, 1920, enabled=True)
    
    badge_x, badge_y = zones.get_badge_position()
    assert badge_x == 144, f"Badge x should be 120 + 24 = 144, got {badge_x}"
    assert badge_y == 244, f"Badge y should be 220 + 24 = 244, got {badge_y}"
    
    pill_x, pill_y = zones.get_pill_position()
    assert pill_x == 746, f"Pill x should be 1080 - 310 - 24 = 746, got {pill_x}"
    assert pill_y == 244, f"Pill y should be 220 + 24 = 244, got {pill_y}"


def test_safe_zones_dimensions():
    """Usable dimensions should account for margins."""
    zones = SafeZones(1080, 1920, enabled=True)
    
    safe_height = zones.get_safe_height()
    assert safe_height == 1028, f"Safe height should be 1920 - 220 - 672 = 1028, got {safe_height}"
    
    safe_width = zones.get_safe_width()
    assert safe_width == 650, f"Safe width should be 1080 - 120 - 310 = 650, got {safe_width}"


def test_caption_vpos_enabled():
    """When enabled, captions sit at the bottom safe zone boundary."""
    vpos = get_caption_vpos(1920, enabled=True)
    assert vpos == 672, f"Caption vpos should be 672 (bottom margin), got {vpos}"


def test_caption_vpos_disabled():
    """When disabled, use legacy 36% position."""
    vpos = get_caption_vpos(1920, enabled=False)
    assert vpos == int(1920 * 0.36), f"Legacy caption vpos should be 691, got {vpos}"


def test_get_safe_margins_function():
    """Convenience function should return same as SafeZones class."""
    top, bottom, left, right = get_safe_margins(1080, 1920, enabled=True)
    assert (top, bottom, left, right) == (220, 672, 120, 310)
    
    top, bottom, left, right = get_safe_margins(1080, 1920, enabled=False)
    assert (top, bottom, left, right) == (0, 0, 0, 0)


if __name__ == "__main__":
    test_safe_zones_disabled()
    test_safe_zones_enabled_standard()
    test_safe_zones_positions()
    test_safe_zones_dimensions()
    test_caption_vpos_enabled()
    test_caption_vpos_disabled()
    test_get_safe_margins_function()
    print("All safe_zones tests passed!")
