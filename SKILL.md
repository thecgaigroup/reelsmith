---
name: reelsmith
description: >-
  Use when the user asks for a video — client/awards sizzle from real footage,
  promo, launch or teaser, event recap, testimonial, data/stat story, how-to,
  animated slides or kiosk loop, narrated explainer, social clip (Reels, Shorts,
  TikTok, LinkedIn, X), captions, overlay or GIF. Footage-first editorial
  sizzles, templates, HyperFrames/Remotion craft with skills on, brand QA, then
  review and export. Paid AI optional and quoted first.
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
| **Awards / partner / client sizzle from real selects** | **client-sizzle** (HyperFrames or Remotion) | **client-sizzle.md**, **storyboard.md**, brand-qa.md, motion-design.md, kinetic-type.md, transitions.md, hyperframes.md or remotion.md |
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
Read **references/client-sizzle.md** end to end. Summary:
1. Map every brief beat; skip none.
2. Author storyboard (JSON + HTML) — see storyboard.md; open pattern in examples/storyboard/ — then ingest real selects (phone/iPad/Day-Of first).
3. Build HyperFrames or Remotion with **skills on** — never `HYPERFRAMES_SKIP_SKILLS=1` on this lane.
4. Showreel kinetic type — `motion-design.md` and `kinetic-type.md`. The bar to match is dense real footage plus that type (comparison bar in client-sizzle.md). Six-part skeleton before the build. Score hook / phone / motion / variety / brand / sound on the contact sheet and `phone.jpg` before a full render.
5. Hard **brand-qa.md** gate + frame snapshots before anything leaves the box.
6. Stay on the sizzle until the user explicitly pivots. Do not open Flashtalk / AI talk-head / lookalike paths
   mid-job without a clear ask + Rights/spend clearance.

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
