---
name: reelsmith
description: >-
  Use when the user asks for a video. Client or awards sizzle from real footage:
  read references/client-sizzle.md first (dense footage + kinetic type, six-part
  skeleton, HyperFrames skills ON — never HYPERFRAMES_SKIP_SKILLS), then
  storyboard.md (frame-numbered BRIEF), kinetic-type.md, transitions.md,
  motion-design.md (taste numbers, motion grammar), music.md (cue sheet, launch sync taps, bed-relative levels),
  hyperframes.md (harness: reference, then data, then motion), and brand-qa.md (stills, fresh reviewer, item-by-item, scores to 8+).
  Use remotion.md only when type locks to speech or a locked master needs a
  campaign matrix. openmotion.md (third engine) only for a HyperFrames-format piece that needs a Studio
  timeline handoff or OpenMotion's Studio lint and export verifier. Optional product-hero notes in that file add no Three.js
  package and do not change the engine. captions.md when speech is on screen. Also promo, launch,
  recap, testimonial, how-to, slides, explainer, social clips. Paid AI only
  after a quote. When the user asks "what can you do" or "what can Reelsmith make",
  show the capabilities menu (run `python3 scripts/capabilities_menu.py` and display
  the output), then ask what they need. The menu is automatic discovery only — never
  require users to pick from it for normal requests.
---
# Reelsmith

Videos built in code from one spec: script → plan → approval → render → review → export.
Everything works free and offline; optional keys add features. Paths below (`scripts/`, `templates/`,
`references/`) are relative to the Reelsmith folder: beside this file, or `/workspace/reelsmith/` on a Grok Bot box.

**Craft bar:** client and awards work must feel like a production-house cut — real selects, speech- or beat-locked
kinetic type, correct logos — not grey placeholders or a talk-head TEMP diverted from the brief.

## What Reelsmith can make

- **Product launches and feature promos**: Music-driven announcement videos with kinetic type and brand animations (see `examples/previews/product-launch-9x16.gif`)
- **Event recaps and highlights**: Turn event photos into engaging video recaps with music and transitions (see `examples/previews/event-recap-16x9.gif`)
- **Testimonials and customer stories**: Showcase customer quotes and reviews with polished typography (see `examples/previews/testimonial-16x9.gif`)
- **Coming soon teasers**: Countdown and date-reveal videos with loopable animations (see `examples/previews/countdown-teaser-9x16.gif`)
- **Stats and milestone callouts**: Highlight key numbers, metrics, and achievements (see `examples/previews/stat-callout-9x16.gif`)
- **Tutorials and how-tos**: Step-by-step instructional videos with chapter markers for YouTube (see `examples/previews/howto-tutorial-16x9.gif`)
- **Slide presentations and kiosk loops**: Animated decks for talks, booths, or continuous display (see `examples/previews/slides-presentation-16x9.gif`)
- **Feature explainers with narration**: Product walkthroughs with voiceover and auto-generated captions (see `examples/previews/feature-explainer-1x1.gif`)
- **Educational explainers with charts and timelines**: Signal Shorts format explainers with visual data, maps, and timelines (no single example; see references/explainer-format-signal-shorts.md)
- **Vertical clips from long-form video**: Extract face-tracked highlight moments from talking-head content for Reels, Shorts, TikTok (no single example; see references/clipping.md)
- **Client sizzle reels and awards cuts**: Production-quality cuts from real footage with beat-synced kinetic type (no single example; see references/client-sizzle.md)

Everything works free and offline. Optional API keys add features: a **Pexels** key unlocks high-quality stock photos and videos. Run `python3 scripts/capabilities.py` to see what's available.

Tell me what you need — aspect ratio, length, platform, and brand — and I'll write the script, plan the cut, and render the video.

## Start every job
0. In an existing film folder, read `EDIT_LOG.md` first and say the last session in one sentence (`review-and-qa.md`, Edit log). Append to it before you end the session.
1. **New machine:** `python3 scripts/doctor.py` once before the first render — checks ffmpeg, Python packages, Node,
   fonts, and Reelsmith updates. Exits 1 if core dependencies are missing. Prints update instructions if a newer version
   is available. See what works before starting.
2. `python3 scripts/capabilities.py` — shows what is ON/OFF (never prints keys). Mention, once, which free key
   would help (e.g. Pexels for stock). Never require one.
3. Gather: goal, audience, platform(s), length, brand (`brand.json`; build one: references/brand-kit.md), media,
   music preference, voice yes/no. Ask only what is unclear.

## Quick reference
- **List capabilities and keys**: `python3 scripts/capabilities.py`
- **Check dependencies and updates**: `python3 scripts/doctor.py`
- **Update Reelsmith**: Run `doctor.py` for instructions, or `git pull origin main` (git install) / re-download zip (zip install)
4. **Route honestly** (table below). If the brief is a multi-beat sizzle with real footage, use **client-sizzle** —
   do not force a social template or invent AI talk-heads.

## Route the job
| Job | Use | Read |
|---|---|---|
| **Awards / partner / client sizzle from real selects** | **client-sizzle**, HyperFrames skills ON | **client-sizzle.md** first, then storyboard.md, kinetic-type.md, transitions.md, motion-design.md, music.md, hyperframes.md, brand-qa.md. remotion.md only if speech-locked or for a campaign matrix. Product-hero notes in that file stay on this HyperFrames lane. captions.md if speech is on screen |
| Educational explainer with charts/maps/timelines (Signal Shorts format) | explainer format, ~55 s, 9:16 | explainer-format-signal-shorts.md (sits alongside product-launch as an option, not a replacement) |
| Launch reel, feature drop, promo | template `product-launch` (music-led) | templates.md (house launch recipes, story shapes), music.md, motion-design.md |
| Event highlights from photos | `event-recap` | templates.md, stock-media.md |
| Customer quotes / reviews | `testimonial` | templates.md |
| Teaser, "coming soon", date reveal (loopable) | `countdown-teaser` | templates.md |
| Numbers, report highlight, milestone | `stat-callout` | templates.md |
| Talk/booth/kiosk loop, animated deck | `slides-presentation` (`--loop`) | templates.md |
| Tutorial, walkthrough, onboarding (+ YouTube chapters) | `howto-tutorial` | templates.md, youtube-publishing.md |
| Narrated product explainer with captions | `feature-explainer` (Remotion; `render.sh`) | remotion.md. Optional product-hero notes in that file only when the storyboard names a physical device. No Three.js package |
| Custom kinetic piece, overlay, alpha, GIF | HyperFrames by hand (Remotion if speech-locked) | hyperframes.md, motion-design.md, kinetic-type.md, transitions.md, music.md, brand-qa.md |
| Title card, endslate or bumper someone will retime in a GUI; must pass Studio lint + export verify | OpenMotion (HyperFrames format, `openmotion-example/`) | openmotion.md, then the same motion, music and QA files as HyperFrames |
| **Extract highlight clips from long-form video (talking-head, local files only)** | **clipping lane**, `clipping.py` | **clipping.md** — long-form to 9:16, face-tracked crop, highlight detection (CPU-only, $0, no LLM), shifted captions |
| **Stream highlights from live streams and VODs** | **stream-highlights mode**, `clipping.py --mode stream-highlights` | **clipping.md** — chat-burst scoring, URL input (yt-dlp), facecam-aware crop, profanity masking, optional models (YuNet, YOLOX) |
| Diagrams / math, Lottie, cut user footage, transcribe | Manim, Lottie, auto-editor, parakeet | helpers.md |
| Script or VO lines | 2–3 options + `script_lint.py` | scriptwriting.md, voiceover.md |
| Captions (SRT/VTT/ASS, burn-in) | `captions.py` | captions.md |
| Platform specs, safe zones, delivery files | `export.py`, `presets.json`. For an optional baked-master finish, set `REELSMITH_FINISH_PASS=1` with `finish_pass.py` or `export.py run`. | platform-specs.md, loudness-accessibility.md, finish-pass.md |
| AI b-roll, images, avatars, AI music (paid) | Fal / Higgsfield, quote first | ai-generation.md |

## Pick the engine
| Engine | When |
|---|---|
| **HyperFrames** (default) | Client and awards sizzles (`client-sizzle.md`), custom kinetic, overlays, logo grids, alpha, GIF |
| **Remotion** | Type locked to speech, narrated `feature-explainer`, campaign matrix after the master locks |
| **OpenMotion** | Same HTML format as HyperFrames, rendered by OpenMotion's pinned engine. Pick it for a Studio timeline handoff, or when a piece must pass OpenMotion's Studio lint and frame-exact export verification. $0, no keys, model gateway off |

Choose one at plan approval and write it on the storyboard. Do not switch mid-job. No engine carries a default look.
The gates are the same on all three: `review.py`, `brand-qa.md`, `beats.py lock`, `export.py`.

Licenses: HyperFrames and OpenMotion are Apache-2.0. Remotion is free for individuals and teams of up to 3; companies of 4+ need
a license (ask once if commercial). Music, stock, fonts: licensed, credited (`stock.py credit`, `credits.json`).

## Client sizzle (mandatory when it fits)
Read **references/client-sizzle.md** first and fill its six-part skeleton before any build.
Load in this order, and do not skip ahead to a render:
1. `client-sizzle.md` — bar, anti-patterns, skeleton.
2. `storyboard.md` — copy `examples/storyboard/` and swap in the real beats. A "how was this made?" reference gets a shot ledger (`BREAKDOWN.md`).
3. `kinetic-type.md` — implement a house recipe (default `mask-reveal-up`). Do not pass house ids to HyperFrames as registry blocks.
4. `transitions.md` — one primary seam, at most two accents. Name only real blocks.
5. `motion-design.md` — taste numbers, springs by feel, motion grammar, ambient idle, bans, one named spectacle. A series keeps one `LOOK.md` per look and varies the look across episodes.
6. `music.md` — cue sheet on the same beat grid as the picture. Launch hits use `offset_ms` and `bed_db`. −14 LUFS (`loudness-accessibility.md`).
7. `hyperframes.md` — default engine. Skills on. Harness first: reference, then data, then motion. Never `HYPERFRAMES_SKIP_SKILLS=1`.
8. `remotion.md` only when type locks to speech, or for a campaign matrix after the master locks. Read the optional product-hero notes there when the storyboard names a physical device. They add no Three.js package and they leave this lane on HyperFrames. `captions.md` when speech is on screen.
9. `brand-qa.md` before a draft leaves. `review.py audit` on the comp before the first draft render (no FAIL). BRIEF frames, fresh reviewer, item-by-item on a later pass, scores to 8+. The SageCut ladder in that file stays off. Do not require `SAGE_API_KEY`.
Stay on this lane until the user explicitly pivots. No Flashtalk or interview TEMP mid-job.

## Workflow (templates)
1. **Script:** write 2–3 options (hook in 3 s, one idea per scene, CTA last) at about 2.5 words/s; lint them.
2. **Plan:** `reelsmith.py sample TEMPLATE > content.json`, fill it, then
   `reelsmith.py render --template T --content content.json --brand brand.json --out OUT --dry-run`.
   Show the shot list (scene, text, VO, seconds), music + license, voice (free or quoted), aspects.
3. **Approval (always)** before long renders and before any paid generation.
4. **Draft:** `reelsmith.py render … --aspect 16x9,9x16,1x1 --music track.mp3|synth --vo auto --draft`.
   Motion audit runs automatically during render (WARNING-ONLY by default; findings logged but do not block).
5. **Review gate:** `review.py check VIDEO --out OUT/_review --preset P --job OUT/job.json`; look at
   scenes.jpg, safe.jpg, phone.jpg; run brand-qa.md for client work; fix; send the preview; on the user's yes,
   `review.py approve`.
6. **Final + export:** render without `--draft`, then `export.py run VIDEO --preset reels,tiktok,youtube
   --review OUT/_review --out OUT/delivery` (refuses without approval). YouTube: `youtube_prep.py` (never uploads).
7. **Deliver:** attach files with one line each (aspect, length, LUFS), credits, AI disclosure when needed; offer re-cuts.

## Scripts (`scripts/`)
`capabilities.py` features on/off | `brand.py` validate, bundle, from-logo, from-site | `reelsmith.py` list,
sample, render, loop, seam | `script_lint.py` | `beats.py` grid, snap, fit, synth, lock | `stock.py` search, fetch,
credit (API keys only, `--dry-run`) | `captions.py` build/burn | `review.py` check (incl. cut list, clicks at cuts), audit (static motion audit; runs automatically during render in WARNING-ONLY mode), approve, status |
`export.py` run, overlay, list, loudnorm | `youtube_prep.py` | `presets.json`.
`openmotion_preflight.py` (OpenMotion project structure, no Node).
HyperFrames setup and pin: references/hyperframes.md. OpenMotion pin and render loop: references/openmotion.md. Kokoro needs `HYPERFRAMES_PYTHON=<venv>/bin/python`.

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
OOM: `--workers 2` (HyperFrames, OpenMotion) / `--concurrency=2` (Remotion). OpenMotion Studio lint
`nested_structure_needs_subcomposition`: mount the scene as a sub-composition (`openmotion.md`). Chrome: `$HF doctor` / `npx remotion browser
ensure`. Blank HyperFrames frame: timeline not paused/registered or a bad asset path. No librosa: beats falls back to
a fixed BPM (pass `--bpm`). No Kokoro: espeak-ng. 401: re-ask for the key via the secret prompt.

## Ask the user when
Plan approval (always); script choice; voice pick; unclear platform, length, brand or music; any paid
generation (with the quote); consent for a face or voice; final review approval; Remotion headcount if commercial;
explicit pivot off client-sizzle onto AI talk-heads or a different deliverable.
