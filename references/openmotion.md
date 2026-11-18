---
description: Load when a job picks OpenMotion, the third engine. That means a HyperFrames-format project that needs OpenMotion's stricter Studio lint, its export verifier, or an editable Studio timeline handoff. Not the client-sizzle default (HyperFrames) and not the speech-locked lane (Remotion). Renders headless at $0 with no keys. The model gateway stays off.
---

# OpenMotion (third engine)

OpenMotion ([nexu-io/openmotion](https://github.com/nexu-io/openmotion), Apache-2.0, no NOTICE file) is an agentic video studio built on HyperFrames. Its render core is HyperFrames 0.9.7 (Chromium, then FFmpeg). On top it adds three things we use: a Studio-host lint, an MP4 export verifier, and a Studio timeline a person can edit. The project files are plain HyperFrames HTML. Everything in `hyperframes.md` (paused timeline, `fromTo`, no timers, harness stations) still applies. This file covers only what changes.

## Pick the engine

| Engine | Pick it when | Read |
|---|---|---|
| **HyperFrames** (default) | Client and awards sizzles, custom kinetic pieces, overlays, logo grids, alpha, GIF | `client-sizzle.md`, `hyperframes.md` |
| **Remotion** | Type locked to speech (word timings), narrated `feature-explainer`, a campaign matrix after the master locks | `remotion.md` |
| **OpenMotion** | A HyperFrames-format piece that the client or Marc will retime in a GUI (Studio timeline handoff), or that must pass OpenMotion's Studio lint and frame-exact export verification before it leaves. Title cards, endslates, and short brand bumpers are typical | this file |

- Pick one engine per job, at plan approval. Write it on the storyboard. Do not switch engines mid-job to fix stiff motion; timing and easing live in `motion-design.md`.
- OpenMotion can be picked at plan approval for technical reasons (Studio lint, export verification). HyperFrames stays the sizzle default unless that technical need applies, or Marc asks for the Studio GUI handoff on that job.
- No engine brings a default look. `LOOK.md` and `brand.json` drive the look on all three (`motion-design.md`). `poster-grid` is never a default.

## Pin and install (once, $0, no keys)

Pinned to `nexu-io/openmotion@9e2f87798cacbe1dad5785e03c5dd57193da4c70` (read and test-rendered 2026-11-18; the only release tag, `v0.1.0` @19f7424, is 26 commits earlier). It is not published on npm, so install from source:

```bash
export OPENMOTION_TELEMETRY=0 DO_NOT_TRACK=1 HYPERFRAMES_NO_TELEMETRY=1   # OpenMotion usage analytics are ON by default
OM=${REELSMITH_OPENMOTION_DIR:-/workspace/tools/openmotion}
git -c filter.lfs.smudge= -c filter.lfs.process= -c filter.lfs.required=false clone https://github.com/nexu-io/openmotion "$OM"
git -C "$OM" checkout 9e2f87798cacbe1dad5785e03c5dd57193da4c70
(cd "$OM" && npm ci --ignore-scripts --no-audit --no-fund)    # Node 22.18+; about 610 MB node_modules
HF="$OM/node_modules/.bin/hyperframes"                         # OpenMotion's pinned engine CLI (0.9.7)
$HF doctor                                                     # Chrome + FFmpeg; whisper/Kokoro/Docker optional
```

`capabilities.py` lists `openmotion` under engines once `$OM/node_modules/hyperframes` exists. The clone is about 680 MB with history. Use `--depth 1 --branch main` only when you do not need the pin.

**Stays off:** the model gateway (GPT Image, Seedance, Suno, Eleven via BYOK or the OpenDesign Go plan), `npm run dev`/the Studio server, the MCP server, the template and motion catalogs, the brand design systems, and `npx skills add`. None of these is needed to render. Starting Studio for a handoff is a separate yes from Marc. It binds to localhost only, never to a public port. Paid generation stays on hold (`ai-generation.md`). If a job seems to need a key, flag it; do not add one.

## Project shape

Copy `openmotion-example/` (6.5 s, 16:9, kinetic title card) and edit. Studio lint is stricter than plain HyperFrames lint:

1. `index.html` root: `data-composition-id="main"`, `data-width`, `data-height`, `data-duration`, `data-fps`, and an empty paused `main` timeline.
2. Each root clip that has children is a **mounted sub-composition**: `<div class="clip" data-composition-id="X" data-composition-src="compositions/x.html" data-start data-duration data-track-index data-width data-height>`. The file is wrapped in `<template>`. Its root carries the same id and duration and registers `window.__timelines['X']`. A flat `<section class="clip">` with children (as in `hyperframes-example/`) fails Studio lint.
3. Tween transforms and opacity only. `letterSpacing`, width, top and font-size tweens are errors, not warnings. For a tracking reveal, split the glyphs and move each glyph's `x`.
4. Stable, unique `data-hf-id` on authored elements so Studio edits keep their identity.

## Render loop

```bash
P=path/to/project
python3 scripts/openmotion_preflight.py $P               # stdlib structure check, no Node (CI runs its tests)
node $OM/scripts/lint-project.mjs $OM $P                 # OpenMotion Studio lint: errorCount must be 0
(cd $P && $HF check . && $HF snapshot --at 0.4,1.6,4.5)  # BRIEF stills first (brand-qa.md)
(cd $P && $HF render . -o out/x-16x9.mp4 --format mp4 --quality delivery --json)   # draft: --quality draft
node --experimental-strip-types $OM/scripts/verify-export.ts $P/out/x-16x9.mp4 \
  '{"width":1920,"height":1080,"fps":30,"duration":6.5,"audio":"silent"}'   # audio: required|silent|optional
python3 scripts/review.py check $P/out/x-16x9.mp4 --out $P/out/_review --preset youtube --expect-seconds 6.5
```

`verify-export.ts` checks the container, codec, dimensions, frame rate, duration, a full decode, the exact frame count, and seeks at the first, middle, and last frame. It is a technical gate. `review.py` and `brand-qa.md` remain the craft gates, and the user's OK still comes before delivery.

## Our formats

| Aspect | Root, mounts, and sub-composition roots | Presets |
|---|---|---|
| 16:9 | `1920×1080`, `data-resolution="landscape"` | `youtube`, `x`, `linkedin` |
| 9:16 | `1080×1920`, `data-resolution="portrait"` | `shorts`, `reels`, `tiktok`, `ig-stories` |
| 1:1 | `1080×1080`, `data-resolution="square"` | `ig-feed`, `linkedin-square`, `x-square` |

Make one project per aspect, and relayout the comp; do not scale it. Text stays in safe zones (`platform-specs.md`). The verify-export expectation uses the same width, height, fps and duration. Delivery files and loudness go through `export.py run` after `review.py approve`, exactly as on the other engines. Alpha and loops use `--format mov|webm|gif` (`hyperframes.md`).

## Brand, captions, music

- **Brand:** `python3 scripts/brand.py bundle brand.json --out $P` writes `$P/brand/` (`brand.css`, fonts, logos, `hf-variables.json`). Link `brand/brand.css` from `index.html`, and use `var(--primary)` and the other tokens in sub-compositions with fallbacks. Logos come from `brand/`. `brand.py validate` contrast must pass. OpenMotion's Brand Kit catalog is not used.
- **Captions:** on any speech, the same as other engines. `captions.py build` gives SRT, VTT and ASS. Burn with `captions.py burn` on the rendered MP4, or author caption clips from `words.json` (`captions.md`). OpenMotion's caption export is not used.
- **Music and SFX:** `<audio class="clip" data-start data-duration data-track-index data-volume>` on the root of `index.html`, placed on `b(n) + offset_ms` from `beats.py grid` (`music.md`). Licensed or synthetic beds only (`validate_music_license.py`). No generated music. Check loudness with `review.py`; run `export.py loudnorm` if it misses −14 LUFS or −1 dBTP.
- **Beat lock:** `review.py check` writes `cuts.json`, and `beats.py lock` scores it. The same command works on any engine.

## Portability and version skew

Reelsmith's HyperFrames lane and OpenMotion both pin HyperFrames `0.9.7`. A project that passes OpenMotion's Studio lint also renders on the main HyperFrames path. The reverse is not true: flat HyperFrames sizzles fail Studio lint until their scenes become sub-compositions. When bumping the OpenMotion SHA, re-run the render loop on `openmotion-example/` and re-check the engine version in its `package.json`.

## Caveats (2026-11-18 maturity check)

The project has been OpenMotion since a 2026-11-08 cutover from HTML Anything. It has one tag (`v0.1.0`, 2026-11-17), its package version is `0.0.1` (private), and nothing is published on npm. Its churn is very high: about 50–100 commits a day, many by a bot. Pin by SHA and re-verify before any bump. If upstream breaks, the same project still renders on our HyperFrames pin.

*Source: nexu-io/openmotion (Apache-2.0) @9e2f877. Used as installed tooling: `scripts/lint-project.mjs`, `scripts/verify-export.ts`, and its pinned HyperFrames CLI. Project rules restated from `skills/openmotion-production/references/native.md` in our words. No OpenMotion files are vendored into this repo.*
