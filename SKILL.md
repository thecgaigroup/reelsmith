---
name: reelsmith
description: >-
  Use when the user asks for a video. Client or awards sizzle from real footage:
  read references/client-sizzle.md first (dense footage + kinetic type, six-part
  skeleton, HyperFrames skills ON — never HYPERFRAMES_SKIP_SKILLS), then
  storyboard.md, kinetic-type.md, transitions.md, motion-design.md, brand-qa.md,
  and hyperframes.md. Use remotion.md only when type locks to speech; captions.md
  when speech is on screen. Also promo, launch, recap, testimonial, how-to,
  slides, explainer, social clips. Paid AI only after a quote.
---
# Reelsmith

Videos built in code from one spec: script → plan → approval → render → review → export.
Everything works free and offline; optional keys add features. Paths below (`scripts/`, `templates/`,
`references/`) are relative to the Reelsmith folder: beside this file, or `/workspace/reelsmith/` on a Grok Bot box.

**Craft bar:** client and awards work must feel like a production-house cut — real selects, speech- or beat-locked
kinetic type, correct logos — not grey placeholders or a talk-head TEMP diverted from the brief.

## Start every job
1. `python3 scripts/capabilities.py` — shows what is ON/OFF (never prints keys). Mention, once, which free key
   would help (e.g. Pexels for stock). Never require one.
2. Gather: goal, audience, platform(s), length, brand (`brand.json`; build one: references/brand-kit.md), media,
   music preference, voice yes/no. Ask only what is unclear.
3. **Route honestly** (table below). If the brief is a multi-beat sizzle with real footage, use **client-sizzle** —
   do not force a social template or invent AI talk-heads.

## Route the job
| Job | Use | Read |
|---|---|---|
| **Awards / partner / client sizzle from real selects** | **client-sizzle**, HyperFrames skills ON | **client-sizzle.md** first, then storyboard.md, kinetic-type.md, transitions.md, motion-design.md, hyperframes.md, brand-qa.md. remotion.md only if speech-locked. captions.md if speech is on screen |
| Launch reel, feature drop, promo | template `product-launch` (music-led) | templates.md, music.md |
| Event highlights from photos | `event-recap` | templates.md, stock-media.md |
| Customer quotes / reviews | `testimonial` | templates.md |
| Teaser, "coming soon", date reveal (loopable) | `countdown-teaser` | templates.md |
| Numbers, report highlight, milestone | `stat-callout` | templates.md |
| Talk/booth/kiosk loop, animated deck | `slides-presentation` (`--loop`) | templates.md |
| Tutorial, walkthrough, onboarding (+ YouTube chapters) | `howto-tutorial` | templates.md, youtube-publishing.md |
| Narrated product explainer with captions | `feature-explainer` (Remotion; `render.sh`) | remotion.md |
| Custom kinetic piece, overlay, alpha, GIF | HyperFrames by hand (Remotion if speech-locked) | hyperframes.md, motion-design.md, kinetic-type.md, transitions.md, brand-qa.md |
| Diagrams / math, Lottie, cut user footage, transcribe | Manim, Lottie, auto-editor, parakeet | helpers.md |
| Script or VO lines | 2–3 options + `script_lint.py` | scriptwriting.md, voiceover.md |
| Captions (SRT/VTT/ASS, burn-in) | `captions.py` | captions.md |
| Platform specs, safe zones, delivery files | `export.py`, `presets.json` | platform-specs.md, loudness-accessibility.md |
| AI b-roll, images, avatars, AI music (paid) | Fal / Higgsfield, quote first | ai-generation.md |

Licenses: HyperFrames is Apache-2.0. Remotion is free for individuals and teams of up to 3; companies of 4+ need
a license (ask once if commercial). Music, stock, fonts: licensed, credited (`stock.py credit`, `credits.json`).

## Client sizzle (mandatory when it fits)
Read **references/client-sizzle.md** first and fill its six-part skeleton before any build.
Load in this order, and do not skip ahead to a render:
1. `client-sizzle.md` — bar, anti-patterns, skeleton.
2. `storyboard.md` — copy `examples/storyboard/` and swap in the real beats.
3. `kinetic-type.md` — implement a house recipe (default `mask-reveal-up`). Do not pass house ids to HyperFrames as registry blocks.
4. `transitions.md` — one primary seam, at most two accents. Name only real blocks.
5. `motion-design.md` — ambient idle, bans, one named spectacle.
6. `hyperframes.md` — default engine. Skills on. Never `HYPERFRAMES_SKIP_SKILLS=1`.
7. `remotion.md` only when type locks to speech. `captions.md` when speech is on screen.
8. `brand-qa.md` before a draft leaves. Score hook / phone / motion / variety / brand / sound.
Stay on this lane until the user explicitly pivots. No Flashtalk or interview TEMP mid-job.

## Workflow (templates)
1. **Script:** write 2–3 options (hook in 3 s, one idea per scene, CTA last) at about 2.5 words/s; lint them.
2. **Plan:** `reelsmith.py sample TEMPLATE > content.json`, fill it, then
   `reelsmith.py render --template T --content content.json --brand brand.json --out OUT --dry-run`.
   Show the shot list (scene, text, VO, seconds), music + license, voice (free or quoted), aspects.
3. **Approval (always)** before long renders and before any paid generation.
4. **Draft:** `reelsmith.py render … --aspect 16x9,9x16,1x1 --music track.mp3|synth --vo auto --draft`.
5. **Review gate:** `review.py check VIDEO --out OUT/_review --preset P --job OUT/job.json`; look at
   scenes.jpg, safe.jpg, phone.jpg; run brand-qa.md for client work; fix; send the preview; on the user's yes,
   `review.py approve`.
6. **Final + export:** render without `--draft`, then `export.py run VIDEO --preset reels,tiktok,youtube
   --review OUT/_review --out OUT/delivery` (refuses without approval). YouTube: `youtube_prep.py` (never uploads).
7. **Deliver:** attach files with one line each (aspect, length, LUFS), credits, AI disclosure when needed; offer re-cuts.

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
- Real quotes, logos and faces only with permission; avatars and voice clones need consent; disclose AI gen media.
  Licensed real project footage of talent is not an AI-likeness substitute problem — still follow Rights for any
  synthetic lookalike or voice-clone.
- Captions on anything with speech; text inside safe zones; at most 3 flashes/s; −14 LUFS, at most −1 dBTP.
- Remotion finals: `export.py loudnorm` (it doesn't normalize).
- Never auto-post or upload; prepare files for the user.
- Prefer footage-first craft over generative shortcuts when selects exist.

## Failures
OOM: `--workers 2` (HyperFrames) / `--concurrency=2` (Remotion). Chrome: `$HF doctor` / `npx remotion browser
ensure`. Blank HyperFrames frame: timeline not paused/registered or a bad asset path. No librosa: beats falls back to
a fixed BPM (pass `--bpm`). No Kokoro: espeak-ng. 401: re-ask for the key via the secret prompt.

## Ask the user when
Plan approval (always); script choice; voice pick; unclear platform, length, brand or music; any paid
generation (with the quote); consent for a face or voice; final review approval; Remotion headcount if commercial;
explicit pivot off client-sizzle onto AI talk-heads or a different deliverable.
