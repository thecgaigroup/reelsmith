# Safe Layout for Vertical 9:16 Shorts

**Added in Reelsmith 5.6.0**

Safe layout mode positions UI elements (badges, pills, titles) and captions inside the documented safe zones for Reels, TikTok, and YouTube Shorts, ensuring they remain visible and unobstructed on all platforms.

## When to use

Enable safe layout (`--safe-layout` flag) for:
- **Vertical 9:16 content** destined for Reels, TikTok, or YouTube Shorts
- **Templates with persistent UI elements** (badges, pills, branding) that must stay visible
- **Multi-line captions** that need to wrap without hitting TikTok's right-side button rail

Leave it **off** (the default) for:
- 16:9 or 1:1 content (safe layout has no effect)
- Legacy projects that need pixel-perfect reproduction of earlier renders
- Content where you're managing safe zones manually

## What changes when enabled

### For 9:16 video (1080×1920 px):

| Element | Legacy (off) | Safe layout (on) |
|---|---|---|
| **Top safe margin** | 0 px | 220 px (12% of height) |
| **Bottom safe margin** | 691 px (36%) | 480 px (25%), keeps captions 540px from bottom |
| **Left safe margin** | 86 px (8%) | 120 px (11.1%, matches TikTok) |
| **Right safe margin** | 86 px (8%) | 310 px (28.7%, clears TikTok right rail) |
| **Caption band (horizontal)** | 86–994 px (908 px wide) | 120–770 px (650 px wide, clears right buttons) |
| **Badge position** | (40, 40) px | (144, 244) px (inside safe zone) |
| **Pill position** | (1040, 40) px | (746, 244) px (inside safe zone) |
| **Frame 0** | May open mid-reveal | Full cover: title set, badge and art visible |

### Platform safe zones (reference)

From `references/platform-specs.md`:

| Platform | Top | Bottom | Left | Right | Notes |
|---|---|---|---|---|---|
| **Reels** | 14% | 35% | 6% | 6% | Meta official guidance |
| **TikTok** | 12.5% | 34.5% | 11.1% | 11.1% | Plus right rail from ~44% height down |
| **Shorts** | 8% | 35% | 6% | 10% | Google guidance |
| **Our safe zone** | 220px | 480px | 120px | 310px | Strictest combination of all three |

**TikTok's right rail:** Buttons (like, comment, share) occupy roughly x=850–1080px from about 44% of the height down. Our 770px caption width cap keeps text clear of this rail while allowing generous line length.

## Usage

### With captions.py

```bash
python3 scripts/captions.py build \
  --words words.json \
  --aspect 9:16 \
  --style boxed \
  --safe-layout \
  -o out/captions
```

The `--safe-layout` flag:
- Positions captions at 540px from the bottom (instead of 691px)
- Restricts horizontal caption band to 120–770px (instead of 86–994px)
- Text wraps inside this narrower band rather than overflowing

### With HyperFrames templates

Templates that support safe layout (such as `signal-short`) read `ctx["safe_layout"]` from the build context. When `True`, the template uses `SafeZones` to position badges, pills, and other persistent UI elements.

Example in `build.py`:

```python
from safe_zones import SafeZones

safe_layout = ctx.get("safe_layout", False)

if safe_layout and ctx["vertical"]:
    zones = SafeZones(1080, 1920, enabled=True)
    badge_x, badge_y = zones.get_badge_position()  # (144, 244)
    pill_x, pill_y = zones.get_pill_position()      # (746, 244)
else:
    # Legacy positions
    badge_x, badge_y = 40, 40
    pill_x, pill_y = 1040, 40
```

Pass `--safe-layout` or set `{"safe_layout": true}` in the render config.

### Frame 0 cover requirement

When safe layout is enabled, **frame 0 must be a strong cover**, not mid-reveal:
- The main title or headline is **fully set** (all words visible)
- Badge and hero art are present
- Any reveal animation starts **after frame 0** (hold the cover for 6–10 frames, then animate)

**Quality gates:**
- Luma mean ≥ 16 (not too dark)
- Luma stddev ≥ 12 (sufficient contrast, not flat)
- No more than 5% darker than the source hero art

Check with `scripts/test_frame0_cover.py`:

```bash
python3 scripts/test_frame0_cover.py video.mp4 \
  --source hero.jpg \
  --min-mean 16 \
  --min-stddev 12 \
  --max-darkening 5
```

## Safe zone calculations

The `templates/_shared/safe_zones.py` module provides:

```python
from safe_zones import SafeZones, get_safe_margins, get_caption_vpos

# Full API
zones = SafeZones(1080, 1920, enabled=True)
top, bottom, left, right = zones.get_margins()           # (220, 480, 120, 310) px
x_min, x_max = zones.get_caption_band()                  # (120, 770) px
safe_height = zones.get_safe_height()                    # 1220 px
safe_width = zones.get_safe_width()                      # 650 px
badge_x, badge_y = zones.get_badge_position()            # (144, 244) px
pill_x, pill_y = zones.get_pill_position()               # (746, 244) px

# Convenience functions
top, bottom, left, right = get_safe_margins(1080, 1920, enabled=True)
caption_margin_v = get_caption_vpos(1920, enabled=True)  # 540 px
```

When `enabled=False`, all margins are zero (no effect on layout).

## Testing

**Unit tests:**
- `scripts/test_safe_zones.py` — Safe zone calculations and positioning
- `scripts/test_safe_layout_captions.py` — Caption positioning with safe layout flag

**Integration tests:**
Run with both flag states and verify:
1. Flag off: output is **byte-identical** to main (hash or pixel diff of frame 0 and a mid frame)
2. Flag on: badge, pill, and caption bounding boxes are inside safe zones
3. Flag on: caption horizontal span is within [120, 770] px
4. Flag on: frame 0 passes luma/stddev/darkening checks

**Example test:**

```bash
# Render with flag off (legacy)
python3 templates/signal-short/render.sh out/legacy

# Render with flag on
python3 templates/signal-short/render.sh out/safe --safe-layout

# Check frame 0 quality (safe version)
python3 scripts/test_frame0_cover.py out/safe/signal-short-9x16.mp4 \
  --source templates/_media/placeholder-tech.jpg

# Compare hashes (legacy should be unchanged from main)
# Visually inspect both frame-0 stills
```

## Backward compatibility

**Default is OFF.** When the `--safe-layout` flag is absent or `safe_layout: false`:
- Captions use legacy positioning (36% from bottom for 9:16)
- Templates use legacy UI positions (no safe margins)
- Rendering output is **byte-for-byte identical** to Reelsmith 5.5.1 and earlier

This ensures:
- Existing projects render identically
- CI and test baselines remain valid
- Safe layout is opt-in for new work

## Notes

- Safe layout **only affects 9:16 aspect ratio**. 16:9, 1:1, and 4:5 are unaffected.
- The safe zone numbers (220/480/120/310 px) are the **strictest combination** of Reels, TikTok, and Shorts guidance.
- TikTok's right rail occupancy varies by device and UI state; 770px is a conservative cap that works across common configurations.
- For other aspect ratios or custom margins, modify `safe_zones.py` or manage safe zones in your template directly.

## See also

- `references/platform-specs.md` — Platform requirements, safe zones, and export presets
- `references/captions.md` — Caption styles and sync requirements
- `templates/_shared/safe_zones.py` — Safe zone calculator API
- `scripts/test_frame0_cover.py` — Frame 0 quality checker
