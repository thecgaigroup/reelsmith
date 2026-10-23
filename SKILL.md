---
name: reelsmith
description: Use when the user asks for a video - sizzle reel, promo, launch or teaser, event recap, testimonial, data/stat story, how-to or tutorial, animated slides or kiosk loop, narrated explainer, social clip (Reels, Shorts, TikTok, LinkedIn, X), captions, overlay or GIF. Writes the script, plans and gets approval, builds from parameterized templates with a brand kit, real or synth music on a beat grid, free stock and local voice, captions and platform presets, runs a review gate, then renders 16:9, 9:16 and 1:1 on your own computer. Paid AI is optional and quoted first.
---

# Reelsmith

Videos built in code from one spec: script -> plan -> approval -> template render -> review -> export.
Everything works free and offline; optional keys add features. Paths below (`scripts/`, `templates/`,
`references/`) are relative to the Reelsmith folder: beside this file, or `/workspace/reelsmith/` on a Grok Bot box.

## Start every job
1. `python3 scripts/capabilities.py` - shows what is ON/OFF (never prints keys). Mention, once, which free key
   would help (e.g. Pexels for stock video). Never require one.
2. Gather: goal, audience, platform(s), length, brand (`brand.json`; build one: references/brand-kit.md), media,
   music preference, voice yes/no. Ask only what is unclear.
3. Pick a template (below) or a custom build.

## Route the job
| Job | Use | Read |
|---|---|---|
| Launch reel, feature drop, promo | template `product-launch` (music-led) | templates.md, music.md |
| Event highlights from photos | `event-recap` | templates.md, stock-media.md |
| Customer quotes / reviews | `testimonial` | templates.md |
| Teaser, "coming soon", date reveal (loopable) | `countdown-teaser` | templates.md |
| Numbers, report highlight, milestone | `stat-callout` | templates.md |
| Talk/booth/kiosk loop, animated deck | `slides-presentation` (`--loop`) | templates.md |
| Tutorial, walkthrough, onboarding (+ YouTube chapters) | `howto-tutorial` | templates.md, youtube-publishing.md |
| Narrated product explainer with captions | `feature-explainer` (Remotion; `render.sh`) | remotion.md |
| Custom kinetic piece, overlay, alpha, GIF | HyperFrames by hand | hyperframes.md, motion-design.md |
| Diagrams / math, Lottie, cut user footage, transcribe | Manim, Lottie, auto-editor, parakeet | helpers.md |
| Script or VO lines | 2-3 options + `script_lint.py` | scriptwriting.md, voiceover.md |
| Captions (SRT/VTT/ASS, burn-in) | `captions.py` | captions.md |
| Platform specs, safe zones, delivery files | `export.py`, `presets.json` | platform-specs.md, loudness-accessibility.md |
| AI b-roll, images, avatars, AI music (paid) | Fal / Higgsfield, quote first | ai-generation.md |

Licenses: HyperFrames is Apache-2.0. Remotion is free for individuals and teams of up to 3; companies of 4+ need
a license (ask once if commercial). Music, stock, fonts: licensed, credited (`stock.py credit`, `credits.json`).

## Workflow
1. **Script:** write 2-3 options (hook in 3 s, one idea per scene, CTA last) at about 2.5 words/s; lint them.
2. **Plan:** `reelsmith.py sample TEMPLATE > content.json`, fill it, then
   `reelsmith.py render --template T --content content.json --brand brand.json --out OUT --dry-run`.
   Show the shot list (scene, text, VO, seconds), music + license, voice (free or quoted), aspects.
3. **Approval (always)** before long renders and before any paid generation.
4. **Draft:** `reelsmith.py render … --aspect 16x9,9x16,1x1 --music track.mp3|synth --vo auto --draft`.
5. **Review gate:** `review.py check VIDEO --out OUT/_review --preset P --job OUT/job.json`; look at
   scenes.jpg, safe.jpg, phone.jpg; fix; send the preview; on the user's yes, `review.py approve`.
6. **Final + export:** render without `--draft`, then `export.py run VIDEO --preset reels,tiktok,youtube
   --review OUT/_review --out OUT/delivery` (refuses without approval). YouTube: `youtube_prep.py` (never uploads).
7. **Deliver:** attach files with one line each (aspect, length, LUFS), credits, AI disclosure; offer re-cuts.

## Scripts (`scripts/`)
`capabilities.py` features on/off | `brand.py` validate, bundle, from-logo, from-site | `reelsmith.py` list,
sample, render, loop, seam | `script_lint.py` | `beats.py` grid, snap, fit, synth | `stock.py` search, fetch,
credit (API keys only, `--dry-run`) | `captions.py` build/burn | `review.py` check, approve, status |
`export.py` run, overlay, list, loudnorm | `youtube_prep.py` | `presets.json`.
HyperFrames setup and pin: references/hyperframes.md. Kokoro needs `HYPERFRAMES_PYTHON=<venv>/bin/python`.

## Rules
- Keys only via the platform's secret prompt as env vars; never echo, log or write them. `REELSMITH_IGNORE_KEYS=1`
  forces the free path.
- Paid voice/AI only when named + `--allow-paid` + key present + the user approved the quote. A decline is final.
- Stock only through official APIs with a key; never scrape or hotlink; keep the credits.
- Real quotes, logos and faces only with permission; avatars and voice clones need consent; disclose AI.
- Captions on anything with speech; text inside safe zones; at most 3 flashes/s; -14 LUFS, at most -1 dBTP.
- Remotion finals: `export.py loudnorm` (it doesn't normalize).
- Never auto-post or upload; prepare files for the user.

## Failures
OOM: `--workers 2` (HyperFrames) / `--concurrency=2` (Remotion). Chrome: `$HF doctor` / `npx remotion browser
ensure`. Blank HyperFrames frame: timeline not paused/registered or a bad asset path. No librosa: beats falls back to
a fixed BPM (pass `--bpm`). No Kokoro: espeak-ng. 401: re-ask for the key via the secret prompt.

## Ask the user when
Plan approval (always); script choice; voice pick; unclear platform, length, brand or music; any paid
generation (with the quote); consent for a face or voice; final review approval; Remotion headcount if commercial.
