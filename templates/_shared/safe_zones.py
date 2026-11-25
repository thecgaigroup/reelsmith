"""Safe zone calculations for vertical 9:16 video layouts (Reels, TikTok, Shorts).

Usage:
    from safe_zones import SafeZones, get_safe_margins
    
    zones = SafeZones(1080, 1920, enabled=True)
    top, bottom, left, right = zones.get_margins()  # pixels
    caption_x_min, caption_x_max = zones.get_caption_band()  # horizontal safe band
"""

class SafeZones:
    """Safe zone calculator for 9:16 vertical video (1080x1920).
    
    Platform requirements (from references/platform-specs.md):
    - Reels: 14% top, 35% bottom, 6% sides
    - TikTok: 12.5% top, 34.5% bottom, 11.1% sides + right rail
    - Shorts: 8% top, 35% bottom, 6% left, 10% right
    
    Our safe zone (strictest combination):
    - Top: 220px (12.0% of 1920, slightly above TikTok 12.5%)
    - Bottom: 480px (25.0% of 1920, well inside all platforms' 34-35%)
    - Left: 120px (11.1% of 1080, matches TikTok)
    - Right: 310px (28.7% of 1080, clears TikTok right rail)
    
    Caption band (horizontal): x 120-770px on 1080 wide (650px usable width)
    This clears TikTok's right rail while staying inside the left margin.
    """
    
    # Safe zone margins in pixels for 1080x1920
    TOP_PX = 220
    BOTTOM_PX = 480
    LEFT_PX = 120
    RIGHT_PX = 310
    
    # Caption band horizontal limits (clears right rail)
    CAPTION_X_MIN = 120
    CAPTION_X_MAX = 770
    
    def __init__(self, width=1080, height=1920, enabled=False):
        """Initialize safe zones for the given dimensions.
        
        Args:
            width: Video width in pixels (default 1080)
            height: Video height in pixels (default 1920)
            enabled: Whether safe layout is enabled (default False for backward compatibility)
        """
        self.width = width
        self.height = height
        self.enabled = enabled
        
        if enabled and (width, height) != (1080, 1920):
            # Scale margins proportionally if not standard 1080x1920
            self.top = int(height * (self.TOP_PX / 1920))
            self.bottom = int(height * (self.BOTTOM_PX / 1920))
            self.left = int(width * (self.LEFT_PX / 1080))
            self.right = int(width * (self.RIGHT_PX / 1080))
            self.caption_x_min = int(width * (self.CAPTION_X_MIN / 1080))
            self.caption_x_max = int(width * (self.CAPTION_X_MAX / 1080))
        else:
            self.top = self.TOP_PX if enabled else 0
            self.bottom = self.BOTTOM_PX if enabled else 0
            self.left = self.LEFT_PX if enabled else 0
            self.right = self.RIGHT_PX if enabled else 0
            self.caption_x_min = self.CAPTION_X_MIN if enabled else 0
            self.caption_x_max = self.CAPTION_X_MAX if enabled else width
    
    def get_margins(self):
        """Return (top, bottom, left, right) margins in pixels."""
        return self.top, self.bottom, self.left, self.right
    
    def get_caption_band(self):
        """Return (x_min, x_max) horizontal limits for caption text in pixels."""
        return self.caption_x_min, self.caption_x_max
    
    def get_safe_height(self):
        """Return usable height between top and bottom margins."""
        return self.height - self.top - self.bottom
    
    def get_safe_width(self):
        """Return usable width between left and right margins."""
        return self.width - self.left - self.right
    
    def get_badge_position(self):
        """Return (x, y) position for top-left badge in pixels from origin."""
        return self.left + 24, self.top + 24  # 24px padding inside safe zone
    
    def get_pill_position(self):
        """Return (x, y) position for top-right pill in pixels from origin."""
        return self.width - self.right - 24, self.top + 24  # 24px padding inside safe zone


def get_safe_margins(width=1080, height=1920, enabled=False):
    """Convenience function to get safe zone margins.
    
    Args:
        width: Video width in pixels
        height: Video height in pixels
        enabled: Whether safe layout is enabled
        
    Returns:
        Tuple of (top, bottom, left, right) margins in pixels
    """
    zones = SafeZones(width, height, enabled)
    return zones.get_margins()


def get_caption_vpos(height=1920, enabled=False):
    """Get vertical position for captions (margin from bottom).
    
    When safe layout is enabled, captions sit inside the safe zone.
    When disabled, uses legacy position (36% from bottom, 691px on 1920).
    
    Args:
        height: Video height in pixels
        enabled: Whether safe layout is enabled
        
    Returns:
        Margin from bottom in pixels
    """
    if enabled:
        zones = SafeZones(1080, height, enabled=True)
        # Captions sit 60px above the bottom safe zone
        return zones.bottom + 60
    else:
        # Legacy position: 36% from bottom
        return int(height * 0.36)
