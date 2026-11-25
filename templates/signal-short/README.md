# Signal Short Template

A 9:16 vertical Short template demonstrating safe layout positioning: title reveal with center line, cyan/purple keyword highlights, badge (top-left), pill (top-right), and key points over hero art background.

## Slots

- `title` — Main title with keyword emphasis (up to 48 chars)
- `key1` — First key point (up to 60 chars)
- `key2` — Second key point (up to 60 chars)
- `key3` — Optional third key point (up to 60 chars)
- `hero` — Hero background image (blog art, photo)
- `pill_text` — Text for top-right pill (default: "THE SIGNAL")
- `cta` — Call to action text
- `url` — Website URL

## Safe Layout Support

This template supports the `--safe-layout` flag (Reelsmith 5.6.0+):

**When enabled:**
- Badge positioned at (144, 244)px inside safe zone
- Pill positioned at (746, 244)px inside safe zone
- Captions use 120–770px horizontal band (clears TikTok right rail)
- Frame 0 is a strong cover: title fully set, badge and art visible

**When disabled (default):**
- Badge at (40, 40)px
- Pill at (1040, 40)px
- Captions use 86–994px horizontal band
- Frame 0 may open mid-reveal

See `references/safe-layout.md` for complete documentation.

## Example

```bash
# Render with safe layout enabled
python3 templates/signal-short/render.sh out/signal --safe-layout

# Render legacy mode (default)
python3 templates/signal-short/render.sh out/signal-legacy
```

## Visual Style

- **Center line:** White 1.2vmin bar, 50% width
- **Keywords:** Alternating cyan (#22D3EE) and purple (#A78BFA)
- **Badge:** Circular, 80×80px
- **Pill:** Rounded rectangle with gradient (primary → secondary)
- **Hero background:** Zoomed and panned (kenburns effect)
- **Captions:** Boxed style, synced to speech

Duration: 10–14 seconds
Aspect ratio: 9:16 only
Energy: Medium

## Safe Zone Demonstration

Frame-0 stills showing safe layout ON vs OFF are in `/opt/cursor/artifacts/`:
- `signal-short-frame0-safe-on.png` — Badge, pill, and captions inside safe zones
- `signal-short-frame0-safe-off.png` — Legacy positioning (may clip on TikTok/Reels)
