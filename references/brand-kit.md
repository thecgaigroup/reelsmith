# Brand kit (`brand.json`)

One file drives every engine: HyperFrames templates (CSS variables + bundled fonts), the Remotion kit
(`themeFromBrand()` + `loadBrandFonts()`), caption burn-in (ASS colors and fonts), thumbnails and
lower thirds. Schema: `brand/brand.schema.json`. Example: `brand/sample-brand.json` ("Brightline", a fictional brand).

```json
{ "name": "Acme", "tagline": "…", "url": "acme.example", "handle": "@acme",
  "logo": {"primary": "logo.svg", "on_dark": "logo-white.svg", "mark": "mark.svg", "min_height_pct": 6, "watermark": false},
  "colors": {"bg": "#0B1220", "fg": "#F8FAFC", "primary": "#5B6CFF", "secondary": "#22D3EE", "accent": "#FFB020", "muted": "#94A3B8", "surface": "#162036"},
  "fonts": {"heading": {"family": "Space Grotesk", "weight": 700, "source": "google"},
            "body": {"family": "Inter", "weight": 500, "source": "google"}},
  "voice": {"tone": ["confident"], "avoid": ["jargon"], "person": "we", "cta": "Start free today", "wps": 2.5,
            "tts_voice": "af_heart", "pronunciations": {"SaaS": "sass"}},
  "lower_third": {"style": "bar", "bg": "surface", "fg": "fg", "accent": "primary", "radius": 14, "position": "left"},
  "motion": {"energy": "low|medium|high", "ease": "power3.out", "corner_radius": 24},
  "music": {"mood": "upbeat electronic, 110-128 BPM"} }
```
Required: `name`, `colors.bg`, `colors.fg`, `colors.primary`, `fonts.heading`. Everything else has defaults.
Font `source`: `google` (fetched once, then cached), `file` (with `"file": "fonts/X.ttf"`) or `system`.
Paths are relative to the brand.json file.

## Commands
    brand.py validate brand.json          # files exist + WCAG contrast (fg/bg 4.5:1, large text 3:1)
    brand.py bundle brand.json --out DIR  # DIR/brand/{logo, fonts, brand.resolved.json, brand.css, hf-variables.json}
    brand.py css brand.json | brand.py hf-vars brand.json
    reelsmith.py render --brand brand.json …    # templates bundle it automatically
Remotion: `brand.py bundle brand.json --out public`, then set `brandFile: "brand/brand.resolved.json"` in the plan.

## Building a brand from what the user has
1. **They have brand guidelines:** copy the hex colors, font names and logo files exactly. Ask for an SVG or
   transparent PNG logo, plus a light version for dark backgrounds.
2. **Only a logo:** `brand.py from-logo logo.svg --name "Acme" -o brand.json` picks a dominant color (primary),
   a complementary accent and dark/light bg/fg, then validates contrast. Review it with the user.
3. **Only a website:** `brand.py from-site https://acme.example -o brand.json` makes one polite fetch of that page
   (no crawling). It reads theme-color, CSS custom properties, the most frequent hex colors, Google Fonts links
   and the og:image/logo. Confirm with the user: sites often use stock accent colors.
4. **Nothing:** start from `sample-brand.json`, change the name, and choose one primary color plus a heading font
   (Space Grotesk, Inter, Manrope and Sora are safe Google fonts).
Always run `validate`. If primary on bg is below 3:1, use primary for shapes only and fg for text.

Record two lines motion will read, and do not invent them: what the first second should feel like (up to three words in `voice.tone`) and one thing the picture must never do (add it to `voice.avoid`). Missing hex codes get asked for, or sampled with `from-site` and confirmed. Do not write a second `brand.md` or `MOTION.md`. `brand.json` is the intake.

## Rules
- Logo at least `min_height_pct` of frame height, on its own clear space, and never stretched. Use the white or
  `on_dark` version on dark backgrounds.
- Brand tone and `avoid` feed script writing; `voice.cta` is the default CTA; `voice.wps` sets pacing.
- Never use another company's marks, fonts or trade dress without rights. Fonts must allow video embedding
  (Google Fonts: OFL or Apache, fine).
