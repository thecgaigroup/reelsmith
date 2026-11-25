# Safe Layout Flag for Vertical 9:16 Captions

**Added in Reelsmith 5.6.0** (or coordinate with PR #49's 5.5.2)

The `--safe-layout` flag positions burned-in captions inside documented safe zones for Reels, TikTok, and YouTube Shorts, ensuring they remain visible and unobstructed.

## Usage

```bash
python3 scripts/captions.py build \
  --words words.json \
  --aspect 9:16 \
  --style boxed \
  --safe-layout \
  -o out/captions
```

The `--safe-layout` flag (9:16 only):
- Positions captions at **540px from bottom** (instead of 691px)
- Restricts horizontal caption band to **120–770px** (instead of 86–994px)
- Text wraps inside this 650px-wide band, staying clear of TikTok's right rail

## Safe Zone Numbers (1080×1920)

| Margin | Legacy (off) | Safe layout (on) |
|---|---|---|
| **Bottom (vertical)** | 691px (36%) | 540px (480 + 60 padding) |
| **Left (horizontal)** | 86px (8%) | 120px (11.1%) |
| **Right (horizontal)** | 86px (8%) | 310px (28.7%) |
| **Caption band width** | 908px (86-994) | 650px (120-770) |

**Rationale:** Strictest combination of Reels (14/35/6/6%), TikTok (12.5/34.5/11.1/11.1% + right rail), and Shorts (8/35/6/10%).

**TikTok right rail:** Buttons occupy roughly x=850–1080 from ~44% height down. The 770px cap keeps text clear.

## Safe Zones Module

`templates/_shared/safe_zones.py` provides the `SafeZones` class:

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

When `enabled=False`, all margins are zero (no effect).

## Frame-0 Quality Checker

`scripts/test_frame0_cover.py` validates that frame 0 meets quality requirements:
- Luma mean ≥ 16 (not too dark)
- Luma stddev ≥ 12 (sufficient contrast)
- No more than 5% darker than source hero art

```bash
python3 scripts/test_frame0_cover.py video.mp4 \
  --source hero.jpg \
  --min-mean 16 \
  --min-stddev 12 \
  --max-darkening 5
```

Uses ffmpeg signalstats filter. Provides both CLI tool and importable API.

## Backward Compatibility

**Default is OFF.** When `--safe-layout` is absent:
- Captions use legacy positioning (691px from bottom)
- Output is byte-for-byte identical to earlier versions
- Verified by hash comparison in tests

Safe layout only affects 9:16 aspect. 16:9, 1:1, and 4:5 are unaffected.

## See Also

- `references/platform-specs.md` — Platform requirements and safe zones
- `references/captions.md` — Caption styles and sync requirements
- `templates/_shared/safe_zones.py` — Safe zone calculator API
