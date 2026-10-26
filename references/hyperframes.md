---
description: Load for every client sizzle (default engine) and for custom HyperFrames work. Skills stay on. Never set HYPERFRAMES_SKIP_SKILLS on that work. Setup, paused timeline, and the render loop live here.
---

# HyperFrames (manual authoring)

Templates generate HyperFrames projects for you. Use this for custom pieces, overlays and GIFs.
HyperFrames is Apache-2.0 and pinned at 0.8.197. The move from 0.8.188 is a patch line: `doctor`, `lint`, `check`, `snapshot --at`, and `render -o` are the same commands. Snapshot waits for image layers a seek reveals. Multiple `<audio>` clips mix by summing. GSAP stays a local file (`gsap@3`, currently 3.15.0).

## Setup (once)
1. Node 22.12+. If older, unpack a portable Node 22 LTS (nodejs.org linux-x64) to `/workspace/tools/node22/` and
   prepend its `bin` to PATH for HyperFrames only.
2. `export HYPERFRAMES_NO_TELEMETRY=1`; `HF="npx --yes hyperframes@0.8.197"`.
   **Do not set `HYPERFRAMES_SKIP_SKILLS=1` for client sizzle / custom craft** — load project skills (`AGENTS.md` / `CLAUDE.md`: `/hyperframes`, `/media-use`, treatments) first. Skip skills only for throwaway smoke tests.
3. `$HF doctor` (Chrome + FFmpeg). Save GSAP once to `/workspace/tools/gsap.min.js` (jsdelivr `gsap@3/dist/gsap.min.js`).
4. Kokoro TTS: venv `pip install kokoro-onnx soundfile`, `HYPERFRAMES_PYTHON=<venv>/bin/python`.
   Do NOT use `$HF audio --quality best` (cloud processing that may bill).

## Per video
1. `$HF init <slug> --example blank --resolution landscape|portrait|square --non-interactive`; copy GSAP into
   `assets/` and point `<script src>` there.
2. `index.html`: root `<div data-composition-id="main" data-start="0" data-duration data-width data-height>`;
   visible elements and `<audio>`/`<video>` are `class="clip"` with `data-start`, `data-duration`,
   `data-track-index`. One `gsap.timeline({paused:true})` registered as `window.__timelines["main"]`.
3. Animate only transforms and opacity. No CSS transitions, timers, `Math.random()` or `Date.now()`. Build the
   timeline synchronously. Use `fromTo` with explicit end states (cold seeks). Don't mix `translate(-50%)` with
   GSAP x/y. Variables: `<html data-composition-variables='[…]'>` and `window.__hyperframes.getVariables()`.
4. Loop: `$HF lint` -> `$HF check` -> `$HF snapshot --at t1,t2,t3`, then Read the contact sheet.
   On a kinetic or client piece, score that sheet before step 5 (`motion-design.md`). Do not jump to a delivery render on a fade-in title card.
5. `$HF render -o out/x.mp4 --quality delivery` (`draft` for drafts; `--workers 2` if OOM).
   Alpha/GIF: `--format mov|webm|gif` (webm alpha is VP9: decode with `-c:v libvpx-vp9`).

## Kinetic type
Prefer HyperFrames when the piece is a designed page: client sizzle, custom kinetic, overlays, logo grids. The paused timeline **is** `seek(t)` — register it and drive every pose from timeline time. Seek the same `t` twice, and seek backwards, before you trust a frame. Write hits as `b(n)` (`music.md`). Taste numbers: `motion-design.md`. Display type uses `power3.out` or `expo.out` (no overshoot). UI chrome may use `back.out(1.15)`. One display face, one UI face, one accent. Do not set `will-change` or a CSS filter on type the camera scales (the glyphs go soft). Real screenshots and logos only. Client default reveal is a mask/clip word or line stagger (`kinetic-type.md`). `poster-grid` is an optional type grid in that file, not the logo-grid default and not the line default. Name seams from `transitions.md` — one primary, one or two accents — and only name blocks the HyperFrames skill actually has. Skills stay on; do not set `HYPERFRAMES_SKIP_SKILLS`. Speech-locked series work belongs on Remotion (`remotion.md`). Principles: `motion-design.md`.

Premium motion, ambient idle, and the density contract: `motion-design.md`. Caption block names: `captions.md`. Seams, including `beat-freeze-cut` and match cuts: `transitions.md`.

See `hyperframes-example/` (a sizzle) and `lottie-example/` (Lottie seeked by the runtime).

## Troubleshooting
Blank/frozen: timeline not paused or registered, or a bad asset path. `nested_structure` or
`timeline_track_too_dense` warnings are fine in single-file pieces. Chrome won't launch: `$HF doctor`.
`EBADENGINE`: wrong Node.
