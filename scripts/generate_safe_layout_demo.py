#!/usr/bin/env python3
"""Generate demonstration images showing safe layout on vs off for Signal Short style."""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not available, generating placeholder text files instead", file=sys.stderr)
    Path("/opt/cursor/artifacts/signal-short-frame0-safe-on.txt").write_text(
        "Signal Short Frame 0 (safe layout ON)\n"
        "Badge at: (144, 244) px\n"
        "Pill at: (746, 244) px\n"
        "Caption band: 120-770 px horizontal\n"
        "Caption position: 540 px from bottom\n"
        "Title: fully visible at frame 0 (strong cover)\n"
    )
    Path("/opt/cursor/artifacts/signal-short-frame0-safe-off.txt").write_text(
        "Signal Short Frame 0 (safe layout OFF - legacy)\n"
        "Badge at: (40, 40) px\n"
        "Pill at: (1040, 40) px\n"
        "Caption band: 86-994 px horizontal\n"
        "Caption position: 691 px from bottom\n"
        "Title: may open mid-reveal\n"
    )
    sys.exit(0)

# Generate actual demonstration images
def create_demo_frame(safe_layout=False):
    """Create a demonstration frame showing UI element positions."""
    W, H = 1080, 1920
    
    # Create image with dark background
    img = Image.new('RGB', (W, H), color=(15, 23, 42))  # Dark slate
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font_large = font_medium = font_small = None
    
    # Draw hero background (lighter slate)
    draw.rectangle([(0, 0), (W, H)], fill=(30, 41, 59))
    
    # Draw safe zone indicators if enabled
    if safe_layout:
        # Safe zone boundaries
        top, bottom, left, right = 220, 480, 120, 310
        
        # Draw safe zone lines
        draw.rectangle([(left, top), (W - right, H - bottom)], outline=(34, 211, 238), width=4)  # Cyan
        
        # Badge position (144, 244)
        badge_x, badge_y = 144, 244
        badge_size = 80
        draw.ellipse([(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)], 
                    fill=(255, 200, 0), outline=(255, 255, 255), width=3)
        draw.text((badge_x + 40, badge_y + 30), "B", fill=(0, 0, 0), font=font_medium, anchor="mm")
        
        # Pill position (746, 244)
        pill_x, pill_y = 746 - 150, 244  # Adjust for width
        pill_w, pill_h = 300, 50
        draw.rounded_rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)], 
                              radius=25, fill=(34, 211, 238))
        draw.text((pill_x + pill_w//2, pill_y + pill_h//2), "THE CGAI SIGNAL", 
                 fill=(0, 0, 0), font=font_small, anchor="mm")
        
        # Caption band (120-770)
        cap_y = H - 540
        cap_x_min, cap_x_max = 120, 770
        draw.rectangle([(cap_x_min, cap_y - 100), (cap_x_max, cap_y + 100)], 
                      fill=(0, 0, 0, 128), outline=(167, 139, 250), width=3)  # Purple
        draw.text(((cap_x_min + cap_x_max)//2, cap_y), "Captions wrap here\ninside safe zone",
                 fill=(255, 255, 255), font=font_small, anchor="mm", align="center")
        
        # Title (center, fully visible)
        title_y = H // 2
        draw.text((W//2, title_y - 100), "Safe Layout Keeps", fill=(34, 211, 238), 
                 font=font_large, anchor="mm")
        draw.text((W//2, title_y), "Content Visible", fill=(167, 139, 250), 
                 font=font_large, anchor="mm")
        
        # Center line
        line_w = int(W * 0.5)
        line_h = 10
        draw.rectangle([(W//2 - line_w//2, title_y + 80), (W//2 + line_w//2, title_y + 80 + line_h)],
                      fill=(255, 255, 255))
        
        # Label
        draw.text((W//2, H - 100), "SAFE LAYOUT: ON", fill=(34, 211, 238), 
                 font=font_medium, anchor="mm")
    else:
        # Legacy positions
        # Badge position (40, 40)
        badge_x, badge_y = 40, 40
        badge_size = 80
        draw.ellipse([(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)], 
                    fill=(255, 200, 0), outline=(255, 255, 255), width=3)
        draw.text((badge_x + 40, badge_y + 30), "B", fill=(0, 0, 0), font=font_medium, anchor="mm")
        
        # Pill position (1040, 40) - note this is off-screen to the right
        pill_x, pill_y = 1040 - 150, 40
        pill_w, pill_h = 300, 50
        draw.rounded_rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)], 
                              radius=25, fill=(34, 211, 238))
        draw.text((pill_x + pill_w//2, pill_y + pill_h//2), "THE CGAI SIGNAL", 
                 fill=(0, 0, 0), font=font_small, anchor="mm")
        
        # Caption band (86-994)
        cap_y = H - 691
        cap_x_min, cap_x_max = 86, 994
        draw.rectangle([(cap_x_min, cap_y - 100), (cap_x_max, cap_y + 100)], 
                      fill=(0, 0, 0, 128), outline=(167, 139, 250), width=3)
        draw.text(((cap_x_min + cap_x_max)//2, cap_y), "Wide caption band\n(may hit right rail)",
                 fill=(255, 255, 255), font=font_small, anchor="mm", align="center")
        
        # Title (center, partially visible - mid-reveal)
        title_y = H // 2
        draw.text((W//2, title_y - 100), "Safe Layout", fill=(100, 100, 100), 
                 font=font_large, anchor="mm")  # Dimmed
        draw.text((W//2, title_y), "Con", fill=(167, 139, 250), 
                 font=font_large, anchor="mm")  # Partial
        
        # Center line (partial)
        line_w = int(W * 0.2)  # Shorter to show mid-reveal
        line_h = 10
        draw.rectangle([(W//2 - line_w//2, title_y + 80), (W//2 + line_w//2, title_y + 80 + line_h)],
                      fill=(255, 255, 255))
        
        # Label
        draw.text((W//2, H - 100), "SAFE LAYOUT: OFF (Legacy)", fill=(150, 150, 150), 
                 font=font_medium, anchor="mm")
        
        # TikTok right rail overlay (approximate)
        rail_x = 850
        draw.rectangle([(rail_x, int(H * 0.44)), (W, int(H * 0.9))], 
                      fill=(255, 0, 0, 64), outline=(255, 0, 0), width=2)
        draw.text((rail_x + 50, H//2 + 200), "TikTok\nbuttons", 
                 fill=(255, 100, 100), font=font_small, anchor="mm", align="center")
    
    return img


if __name__ == "__main__":
    print("Generating safe layout demonstration frames...")
    
    # Generate frame with safe layout ON
    img_on = create_demo_frame(safe_layout=True)
    out_on = Path("/opt/cursor/artifacts/signal-short-frame0-safe-on.png")
    img_on.save(out_on, "PNG")
    print(f"✓ Generated {out_on} (1080x1920, safe layout ON)")
    
    # Generate frame with safe layout OFF
    img_off = create_demo_frame(safe_layout=False)
    out_off = Path("/opt/cursor/artifacts/signal-short-frame0-safe-off.png")
    img_off.save(out_off, "PNG")
    print(f"✓ Generated {out_off} (1080x1920, safe layout OFF)")
    
    print("\nDemonstration frames show:")
    print("  - Badge and pill positioning")
    print("  - Caption band horizontal limits")
    print("  - Safe zone boundaries (ON) vs TikTok right rail (OFF)")
    print("  - Frame 0 strong cover (ON) vs mid-reveal (OFF)")
