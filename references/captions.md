---
description: Load when speech is on screen or a sidecar SRT/VTT is required. One HyperFrames caption block per section. Burn-in and sidecar profiles live here.
---

# Captions

Captions come from word timings, never from guesswork, when timings exist:
- Kokoro and espeak: the pipeline spreads words by syllable weight inside each measured VO clip (marked approximate in job.json).
- ElevenLabs `with-timestamps`: exact character alignment.
- Other audio: `hyperframes transcribe a.mp3 -e parakeet --json` (local), or WhisperX for several speakers.

    captions.py build --words words.json -o out/captions --profile netflix --aspect 9:16 --style pop --brand brand.json
    captions.py estimate --text "Spoken line." --start 1.2 --end 4.0      # last resort
    captions.py burn video.mp4 out/captions.ass -o burned.mp4 --fontsdir brand/fonts
Remotion: `npx tsx scripts/export-captions.ts src/plans/<slug>.ts > words.json`, then `captions.py build`.

## Profiles
| Profile | Characters/line | Lines | Max cps | Min / max duration | Use |
|---|---|---|---|---|---|
| netflix | 42 | 2 | 20 | 5/6 s / 7 s | Sidecar SRT/VTT for YouTube, LinkedIn, accessibility |
| bbc | 37 | 2 | 17 (≈160–180 wpm) | 1 s / 7 s | Broadcast-style, slower readers |
| social | 24 | 2 | 22 | 0.6 s / 3 s | Burned-in short pages for vertical social |
Rules applied: break at punctuation and clause boundaries; never split a name or number; balance the two
lines (bottom-heavy pyramid); a gap of at least 2 frames between cues; hold the last word through short gaps.
Sidecars always use the netflix profile (complete sentences); burn-in uses `social` in vertical.

## Burn-in styles (`--style`)
- `clean`: white text, soft shadow, no box. Best over controlled backgrounds.
- `boxed`: a semi-opaque surface box. Best over busy footage, and the most accessible choice.
- `karaoke`: the active word highlighted in the brand accent (ASS `\k` timing).
- `pop`: 1–3 word pages with a scale pop and accent emphasis. TikTok and Reels energy.
Placement: inside the preset safe zone, above the bottom UI (Reels and TikTok: above 65% of the height in
the default layout), and never covering faces or on-screen text. Size: at least 4.5% of frame height in
vertical, 3.5% in 16:9. Contrast at least 4.5:1 (WCAG 1.4.3).

## HyperFrames caption blocks

For type authored inside a composition, name one block for the section. Source: [captions catalog](https://hyperframes.heygen.com/prompting/captions-catalog). Do not invent a name. Do not mix two styles in one section. Switch only at a section break. These are not the burn-in path above, and they are not a matte-behind-a-speaker unless the composition already cuts the subject out.

| Tone | Blocks |
|---|---|
| Hype | `caption-kinetic-slam` (one full-screen word per beat), `caption-highlight` (line stays, one word hot) |
| Editorial | `caption-editorial-emphasis` (size contrast on one or two emphasis words), `caption-clip-wipe` |
| Clean / corporate | `caption-clip-wipe`, `caption-weight-shift` |
| Karaoke | `caption-pill-karaoke`, `caption-highlight` |

`caption-glitch-rgb`, `caption-particle-burst`, and `caption-neon-glow` are not client-sizzle defaults. Transcript words come from `$HF transcribe` or `captions.py`. Emphasis words: one or two, from `kinetic-type.md`.

Upload SRT/VTT as sidecars wherever the platform allows (YouTube, LinkedIn, X, Facebook). Burn in for
Reels, TikTok and Shorts, where many people watch muted.

Sources: Netflix Timed Text Style Guide (partnerhelp.netflixstudios.com/hc/en-us/articles/217350977);
BBC Subtitle Guidelines (bbc.co.uk/accessibility/forproducts/guides/subtitles); WCAG 2.2 1.2.2 and 1.4.3.
