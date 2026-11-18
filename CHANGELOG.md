# Changelog

All notable changes to Reelsmith will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.2.0] - 2026-11-18

### Added
- OpenMotion as the third render engine, beside HyperFrames and Remotion (Marc, 2026-11-18). `references/openmotion.md` covers the pin (`nexu-io/openmotion@9e2f877`, Apache-2.0, HyperFrames 0.9.7 core), the source install with telemetry off, and what stays off (model gateway, Studio server, MCP, catalogs). It also covers the project shape that passes Studio lint, the render loop (preflight, Studio lint, snapshot, render, `verify-export.ts`, `review.py`), the 16:9, 9:16 and 1:1 settings, and how `brand.json`, captions, music and beat lock plug in. Includes portability and version-skew notes and the maturity caveats.
- `SKILL.md`: a "Pick the engine" table and a route row. HyperFrames stays the default for client and awards sizzles. Remotion is for speech-locked type and campaign matrices. OpenMotion is for a Studio timeline handoff, or for Studio lint plus frame-exact export verification.
- `openmotion-example/`: a 6.5 s kinetic title card (mask-reveal-up, ambient drift, no audio, no default look). It is Studio-lint clean and also renders on `hyperframes@0.8.197`.
- `scripts/openmotion_preflight.py`: a stdlib check of the Studio-lint structure rules (mounted sub-compositions, registered paused timelines, matching durations, transform-only tweens, no wall clock). Tests: `scripts/test_openmotion_preflight.py` (in CI). CI also runs the preflight on the example.
- `scripts/capabilities.py`: an `openmotion_runtime` tool. `openmotion` appears under engines when `REELSMITH_OPENMOTION_DIR` (default `/workspace/tools/openmotion`) has the installed engine.

### Changed
- The QA gates now name all three engines: `brand-qa.md` (BRIEF stills, commands, critic prompts; "do not suggest a third renderer" became "do not switch engines"), `review-and-qa.md` (stills), `music.md` (`b(n)`, audio clips), `client-sizzle.md` (engine table), `hyperframes.md` (pointer), and the `brand.py` docstring. `review.py`, `beats.py lock` and `export.py` were already engine-agnostic and are unchanged.
- ROADMAP: the 5.1.4 skip "OpenMotion as a tool" is superseded for the render path only.

No OpenMotion files are vendored. No paid generation and no new keys.

## [5.1.6] - 2026-11-18

### Added
- `scripts/review.py audit`: static motion audit of a HyperFrames or Remotion comp, with no render. FAIL on random values, wall-clock time, timers and frame callbacks, and CSS animations or transitions. WARN on `will-change`, layout-property tweens, and linear-eased entrances or exits. Worst level wins; exit 1 on any FAIL; `audit-ok` marks an intended exception; `--json`. Audit shape after motiondivision/ai-kit (MIT @1e42494); rules are the house engine rules. Tests: `scripts/test_motion_audit.py` (in CI).
- `references/motion-design.md`: springs by feel (arrival time and bounce converted to stiffness and damping for `spring01` and Remotion; cue off arrival, not settle), after ai-kit. Phase shares inside one move, ambient layers with numbers and the loop-period rule, a symptom-to-fix table, and signature curves, after LottieFiles/motion-design-skill (MIT @2e1f3c0), merged with the existing Disney, choreography and acted-effects rules without repeating them.
- `references/review-and-qa.md`: motion audit section. `references/brand-qa.md`: checklist item 13 and motion findings by severity (critical, high, medium).
- `references/templates.md`: exploded reveal, an optional product shot for the Detail shape (client-supplied product data only), after annnguyentt/anatomy-reveal-skill (MIT @dd01e1c) on wheresryan22/anatomy (MIT @1482e84).
- `references/transitions.md`: polish recipes with numbers (chromatic fringe, glitch bursts, rack focus, subject trails, speed-based whip blur, seeded grain, vignette, practical-light bloom on footage only) in CSS, GSAP or `ffmpeg`; no new package. Technique survey of pmndrs/react-postprocessing, fand/vfx-js and Alchemist0823/three.quarks (all MIT).
- `SKILL.md`: `review.py audit` and springs-by-feel pointers. ROADMAP: motion-repo list harvest with the skip list.

No look is a default; `poster-grid` is still never a default; the series variety rule is unchanged. All restated in our words; no files, prompts, kits, catalogs or media copied.

## [5.1.5] - 2026-11-17

### Added
- `scripts/beats.py lock`: share of picture cuts within 70 ms of a beat against chance on that grid, from `cuts.json` (`cut` rows only), with `--offset` and the median offset. Verdict "beat-synced edit" at four or more cuts, at least half on the beat and at least 1.8× chance. Approach after JuneYaooo/rea-video (Apache-2.0 @bb11b13), re-implemented. Tests: `scripts/test_beat_lock.py` (in CI).
- `references/storyboard.md`: shot ledger (`BREAKDOWN.md`) — card, one line per shot, shot notes; seen versus inferred (`~`) keys; made-by classes with tells; remake by production unit; picture, packaging and sound layers; narrative line; beat lock in the card. After rea-video and the VIDEO.md format (videomd/videomd, Apache-2.0 @0837221).
- `references/brand-qa.md`: generic-AI tells (color, icons, copy, numbers, pictures, layout, template look) as defaults the brief or `LOOK.md` can earn back. After heydamir/unslop (CC BY 4.0 @620163e) and pbakaus/impeccable (Apache-2.0 @d41d986).
- `references/review-and-qa.md`: reading time per text block. After lemomo-ai/lemo-opuscar `readcheck.mjs` (MIT @00a7f9e); its CC BY-NC docs not used.
- `references/motion-design.md`: acted effects (wind-up, freeze on contact, held drawings, effects that end). After patch-gg/pixelfx (MIT @5294518).
- `references/music.md`, `SKILL.md`: `beats.py lock` and shot-ledger pointers.
- ROADMAP: 20-repo animation list harvest, with the skip list.

All restated in our words; no files, prompts, catalogs, case reports, or reference media copied.

## [5.1.4] - 2026-11-17

### Added
- `references/motion-design.md`: look file (`LOOK.md`). Keep, swap with measured capacity, timing, materials, check; status `described` / `rendered` / `reviewed`; `seen` / `chosen` / `changed` tags; a swap test. A series uses several looks, at least two changes per episode; no look is the default and `poster-grid` is never a series default. Brand stays in `brand.json`.
- `references/templates.md`: launch story shapes (proof, detail, rhythm; none is the default), the verify hold, and direction cards at plan approval.
- `references/storyboard.md`: optional per-shot Check line; the spectacle written as four moments.
- `references/brand-qa.md`: type complaint triage (resource, reading, fit; face-only versus setting-only test).
- `SKILL.md`: pointers to `LOOK.md` and the story shapes.
- ROADMAP: OpenMotion harvest, with what was skipped.

All after nexu-io/openmotion (Apache-2.0 @664be50), restated in our words. No files, code, templates, catalog entries, or design systems copied. Docs only; no script changes.

## [5.1.3] - 2026-11-17

### Added
- Cut list in `scripts/review.py`: `cuts.json` with each picture jump classified as cut, flash, fast move or transition; INFO row with cuts per minute. Approach after heygen-com/hyperframes `measure cuts` (Apache-2.0 @d317abc), re-implemented in Python.
- Clicks at cuts in `scripts/review.py`: WARN when a cut carries a hard audio step (no ~30 ms fade). After browser-use/video-use (MIT @43cfc56). Tests: `scripts/test_cut_detection.py`.
- `references/review-and-qa.md`: cut list and clicks, self-eval at every cut with a three-pass cap, and `EDIT_LOG.md` session memory (Strategy, Decisions, Reasoning, Locked, Outstanding).
- `references/storyboard.md`: take-apart "Measured" now uses `cuts.json`, consecutive frames at events, and one-topic look reports in numbers.
- `references/motion-design.md`: story-short camera numbers (after mromidev/claude-animated-shorts, MIT @e3b817b) and switch-versus-tween plus match recipes (after hyperframes reverse-any-video).
- `references/helpers.md`: filler and pause cut numbers; `references/captions.md`: captions on a cut film (after browser-use/video-use).
- `SKILL.md`: read `EDIT_LOG.md` first. `references/music.md`: lock picture timing before the cue sheet.
- ROADMAP: three-source harvest; storybook three.js look parked.

## [5.1.2] - 2026-11-15

### Added
- Take-apart dossier in `references/storyboard.md`: structured reference breakdown capturing what makes exceptional films work (seen, measured, take sections covering spine, world, formal idea, hand-overs, weak spots, keeps/breaks). Take shape and pace only, never the reference's subject, words, pictures, or music. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- Five kinds of boundaries in `references/transitions.md`: every cut must be becomes / carried / matched / door / change of ground. "Next" is not a reason. Includes pointer from storyboard.md. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- Measure a reference move in `references/motion-design.md`: frame-by-frame measurement method to fit a move's speed curve as cubic-bezier. The rebuild must match the curve, not just the look. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- One-frame pop scan in `references/review-and-qa.md` and `scripts/review.py`: detect frames whose change is far larger than neighbors' (swap, reset, flash). Implemented with behavioral test in `scripts/test_pop_detection.py`. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- ROADMAP.md entry documenting video-decompiler fold and what was skipped (video-decompiler/raea as engine: FSL license and competes with Remotion/HyperFrames; woodxbt listicle: index already covered or parked; Hairline: web widget).

## [5.1.1] - 2026-11-14

### Added
- Archive rights gate in `references/stock-media.md`: clear guidance on allowed sources (Wikimedia Commons, Library of Congress, NARA) and rights (US public domain 1930 or earlier, federal works, CC0/BY/BY-SA); refused licenses (NC, ND, post-1930 press photos). Source: Moh4696/cinematic-skill (MIT, exploraX).
- Evidence vs illustration rule in `references/brand-qa.md`: code-drawn documents must be labelled as recreations; AI stills are illustration only, never evidence or real person stand-ins. Source: Moh4696/cinematic-skill (MIT, exploraX).
- Voice-first timing in `references/voiceover.md`: cut scratch voice first, then time picture to words; keep time-stretch within 0.90–1.15x; hits land on spoken words. Source: Moh4696/cinematic-skill (MIT, exploraX).
- Documentary preset in `references/scriptwriting.md`: cold open, bridge, forward-only chronology, sections as takes, turn, close. Includes fact_notes guidance with sources. Source: Moh4696/cinematic-skill (MIT, exploraX).
- One phrase, one way in `references/kinetic-type.md`: a phrase is either typed on screen or shown as document, never both; typed labels at least 3% of frame height. Source: Moh4696/cinematic-skill (MIT, exploraX).

## [5.1.0] - 2026-10-27
- Initial craft documentation surface with harness, motion grammar, kinetic type recipes, and sound cues.
