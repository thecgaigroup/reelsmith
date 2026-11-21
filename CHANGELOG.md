# Changelog

All notable changes to Reelsmith will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<<<<<<< HEAD
## [5.5.0] - 2026-11-21

### Added

**Stream-Highlights Mode** - Extract vertical 9:16 highlight clips from live streams and gaming VODs

- **Chat-burst analysis**: Priority-based moment detection (chat bursts > RMS loudness > speech-lexicon)
  - Twitch IRC and YouTube live chat collection support (optional)
  - Chat.json file input for pre-recorded chat logs
  - Spam-resistant scoring with rolling z-score spike detection
  - Peak sub-bucket detection within windows
- **URL input**: Process streams directly from YouTube, Twitch, etc. via yt-dlp (optional dependency)
  - Requires `--rights-confirmed` flag to proceed
  - Lazy import - works without yt-dlp for local files
- **90-second chunking**: Efficient processing of long streams
- **Advanced face/person detection** (optional models):
  - YuNet face detection (MIT License, 233 KB, OpenCV Zoo)
  - YOLOX-S person tracking (Apache-2.0, 35 MB, OpenCV Zoo)
  - Graceful fallback to OpenCV Haar cascade when models unavailable
  - Model download via `scripts/fetch_models.py` with SHA-256 verification
- **Facecam-aware crop**: 9:16 crop positioning keeps facecam corner OUT of frame
- **6-second lead-in**: Clips start 6s before peak moment for context
- **Stream-pop captions**: 3-word pop-in captions (yellow new, white spoken)
- **Profanity masking**: Automatic masking in burned-in captions (audio unchanged)
  - Enabled by default, disable with `--no-profanity-mask`
  - Custom masking implementation (first letter + asterisks)
- **Optional dependencies**: `requirements-stream.txt` for yt-dlp, faster-whisper, onnxruntime
- **Comprehensive tests**: All with mocks, no network in CI
  - Chat scoring tests with synthetic data
  - Profanity masking tests
  - Rights-flag enforcement test (mocked yt-dlp)
  - Model fallback tests (no downloads in CI)
  - End-to-end synthetic fixture test (done_when requirement)

**New modules**:
- `scripts/chat_scoring.py`: Chat burst analysis with rolling z-score spike detection
- `scripts/stream_chat.py`: Twitch IRC and YouTube live chat collectors (generator-based)
- `scripts/profanity_mask.py`: Profanity masking for captions
- `scripts/fetch_models.py`: Model downloader with SHA-256 verification
- `scripts/test_stream_highlights.py`: Comprehensive test suite with mocks
- `requirements-stream.txt`: Optional stream-mode dependencies
- `THIRD_PARTY_NOTICES`: Dependency and model license notices

**Extended modules**:
- `scripts/highlights.py`: Added `--mode stream` with chat-burst scoring
- `scripts/facetrack.py`: Added `--detector` (haar/yunet/yolox) with fallbacks
- `scripts/clipping.py`: Added `--mode stream-highlights` with URL input and chunking

**Documentation**:
- Comprehensive README section for stream-highlights mode
- Updated `references/clipping.md` with stream-highlights workflow
- Updated capabilities menu

### Changed

- VERSION bumped to 5.5.0
- README updated with stream-highlights installation and usage
- references/clipping.md expanded with stream mode documentation

### Technical Details

- All code written from scratch in Reelsmith style
- No close paraphrasing of external projects
- Models from OpenCV Zoo (MIT/Apache-2.0)
- Optional dependencies lazy-loaded
- Graceful degradation when optional features unavailable
- Rights confirmation required for URL input
- All tests use mocks, CI runs without network access

## [5.4.5] - 2026-11-21

### Added
- **README version test** (`scripts/test_readme_version.py`): Validates that README H1 title doesn't contain a stale version, and any explicit version mentions match VERSION file. Catches version drift automatically in CI.

### Changed
- **README.md**: Dropped version from H1 title (now "# Reelsmith"). Added clipping lane and educational explainer to capabilities table to match `capabilities_menu.py`.
- **capabilities_menu.py**: Updated clipping capability name and description to match README for consistency.
- **ci.yml**: Added `test_readme_version.py` to test suite.

No new dependencies. Prevents README version drift through automated testing.

## [5.4.4] - 2026-11-21

### Added
- **Clipping capability entry**: Added "Extract highlight clips from long-form video" to capabilities menu (`scripts/capabilities_menu.py`) with reference to `references/clipping.md`. This entry was missing after PR #28 added the clipping lane to the route table.
- **Educational explainer capability entry**: Added "Educational explainers with charts and timelines" for Signal Shorts format to capabilities menu, with reference to `references/explainer-format-signal-shorts.md`. This entry was previously missing from the capabilities menu.
- **Strict drift test**: New test in `scripts/test_capabilities_menu.py` that parses all routes from SKILL.md's route table and verifies each user-facing route has a matching CAPABILITIES entry using strict one-to-one mapping. Each route maps to exactly one capability via template name or reference path, with no substring catch-alls. Explicit exclusion list for helper functions and advanced workflows with reasons. This prevents future drift between the route table and capabilities menu.
- **Up-to-date doctor message**: `scripts/doctor.py` now prints exactly one line "Reelsmith X.Y.Z is up to date" when the installed version matches the latest release, making the output cleaner when no update is needed.
- **Test for up-to-date path**: Added `test_up_to_date_message()` in `scripts/test_doctor.py` that mocks the GitHub API response to verify the up-to-date message is printed correctly.

### Changed
- `scripts/doctor.py`: Added case for when current version equals latest version to print clean up-to-date message.
- `scripts/test_capabilities_menu.py`: Rewrote drift test with strict matching logic that maps each route to exactly one capability by template name or reference path. Added explicit exclusion list with one-line reasons for each excluded route.
- `scripts/test_doctor.py`: Added imports for `json` and `unittest.mock` to support mocked network tests. Fixed wrapper script to apply mock before importing doctor.py.

No new dependencies. All changes improve maintainability and user experience with clearer messaging and stricter drift detection.
## [5.4.3] - 2026-11-21

### Added
- **CI smoke test** (`.github/workflows/smoke.yml`) that runs on every PR and push to main:
  - Extracts ALL HyperFrames and OpenMotion pin occurrences from reference docs (prose "pinned at X" + all command "hyperframes@X") and verifies they all match and resolve upstream
  - Tests `npm view hyperframes@<version>` resolves for the declared pin
  - Tests `git ls-remote` for OpenMotion commit exists upstream  
  - Fails if any pin occurrence disagrees (prose vs command mismatch) or if the pin doesn't resolve
  - Verifies core scripts and key reference files exist
  - Runs a real minimal headless render (product-launch template, ~1.5s, 640×360, synthetic content, no paid voice/generation)
  - Runs `review.py check` on the rendered output to verify the review pipeline works
  - Guards against paid generation: all API keys unset in job-level env, `REELSMITH_IGNORE_KEYS=1`, `--allow-paid` never passed
- Smoke test is CPU-only, $0, completes in <2 minutes, and uses pinned action versions (actions/checkout@v4.2.2, actions/setup-node@v4.1.0, actions/setup-python@v5.3.0)

### Changed
- README: added CI and testing section describing both workflows (ci.yml and smoke.yml)
- Pin extraction now checks ALL occurrences in reference files, not just first match

The smoke test validates fundamentals on every change: all pin occurrences match and resolve upstream, the core render path works end-to-end, and paid APIs cannot be invoked.

## [5.4.2] - 2026-11-21

### Added
- **Version update awareness**: `scripts/doctor.py` now checks the installed VERSION against the latest GitHub release (falling back to main's VERSION file if no releases exist). If a newer version is available, it prints exactly one line with the update command that matches the installation method (git pull for git installs, download instructions otherwise). Network errors, timeouts (3s), or HTTP failures are handled gracefully and still pass with a "could not check" message. Uses stdlib only, no new dependencies.
- **Update Reelsmith entry**: Added to capabilities menu in `scripts/capabilities_menu.py` to help users discover version update functionality.
- **Behavioral tests**: `scripts/test_version_check.py` covers newer version, same version, and offline/timeout scenarios with mocked network calls (5 tests). Added to CI workflow.

### Changed
- `scripts/doctor.py`: Now checks for Reelsmith updates at startup. Prints update instructions only when a newer version is detected. Never auto-installs or runs updates.
- `.github/workflows/ci.yml`: Added `test_version_check.py` to test discovery.
- `scripts/capabilities_menu.py`: Added "Update Reelsmith" entry to CAPABILITIES list.

No new dependencies. All checks use stdlib (urllib.request, json). Suggestion only—never auto-installs or touches anything mid-project.

## [5.4.0] - 2026-11-21

### Added
- **Long-form to vertical 9:16 clipping lane** for extracting highlight moments from user-owned local videos. Workflow: detect highlights using transcript + audio energy heuristics, track faces with OpenCV for stable 9:16 crop, generate shifted captions with pysubs2, and export face-tracked clips with burned-in captions. All CPU-only, $0, no LLM required.
- `scripts/highlights.py`: Highlight detection using word-level transcript and audio energy scoring. Ranks segments by speech pacing, punctuation patterns (questions, exclamations), and audio dynamics. No LLM or paid API required; uses transcript + ffmpeg volumedetect heuristics only.
- `scripts/facetrack.py`: Face detection and tracking using OpenCV Haar cascades (CPU-only, ships with opencv-python) with IoU-based tracker ID management (technique inspired by supervision pattern; supervision is not a dependency). Generates smooth 9:16 crop windows centered on tracked faces with position smoothing.
- `scripts/clipping.py`: Main orchestrator that runs the full pipeline: transcribe → detect highlights → track faces → extract clips → shift captions → burn captions → review each clip. Outputs one directory per clip with video, captions (SRT/ASS), burned video, and review results.
- `scripts/test_clipping.py`: Comprehensive tests for all five task requirements: (1) highlight JSON structure and clip aspect/duration, (2) subject center stays in crop window ≥95% of frames, (3) continuous segments keep single tracker_id, (4) SRT shifting preserves cue count and moves last cue end by T, (5) 48kHz audio check passes.
- `references/clipping.md`: Complete clipping lane documentation covering when to use it, workflow steps, highlight scoring approach, face tracking with OpenCV, caption shifting with pysubs2, integration with existing review/captions pipeline, and limitations.
- Dependencies: opencv-python (Apache-2.0, CPU-only Haar cascades), pysubs2 (MIT, subtitle manipulation). All compatible licenses, no GPL/AGPL/LGPL/MPL, no gated models.

### Changed
- `README.md`: Added "When to use the clipping lane" section explaining use cases (talking-head content, local videos only) and when not to use it (music videos, multi-speaker, YouTube downloads).
- `SKILL.md`: Added clipping workflow to route table and workflow section.
- `.github/workflows/ci.yml`: Added `test_clipping.py` to CI test discovery.

**Harvested techniques from AI-Youtube-Shorts-Generator (MIT, Anil Chandra Naidu Matcha):** highlight ranking approach (score/hook/reason schema), segment deduplication by overlap threshold, natural boundary detection at sentence breaks, and face-centered crop concept. Re-implemented from scratch; no wholesale adoption, no yt-dlp downloader, no MuAPI/OpenAI/Gemini dependency.

**Dependency licenses verified:**
- opencv-python: Apache-2.0 (core library + Haar cascade files)
- pysubs2: MIT (tkarabela/pysubs2)

No YouTube downloader, no paid services, no new credentials. Local input files only. Reuses existing parakeet/WhisperX transcription path (user must provide transcript or run separately), captions.py for burn-in, review.py for quality gates, and FFmpeg for all video operations. Clips pass through the same review gate as templates: aspect, duration, loudness, sync, flashes, cuts.

## [5.3.1] - 2026-11-21

### Added
- **Capabilities menu** for user discovery: plain-language list of what Reelsmith can make, shown when users ask "what can you do" or when they're new to the skill. Each entry names one capability with a sample clip from `examples/previews/`. Menu is generated from `scripts/capabilities_menu.py`, which derives the free-key recommendation from `capabilities.py`'s actual feature detection (currently recommends Pexels when no stock provider is configured).
- **SKILL.md**: capabilities menu added to main body, with trigger guidance in the description that fires only on discovery questions ("what can you do", new users). Clarifies that menu is for automatic discovery only — users never need to pick from it for normal requests.
- **README.md**: capabilities menu added as a table with example GIFs, matching the SKILL.md menu content.
- **Tests**: `scripts/test_capabilities_menu.py` verifies (1) every menu entry's sample path exists, (2) README and SKILL menus match (both generated from the same source), (3) free-key line matches what `capabilities.py` reports, (4) trigger guidance only fires on appropriate cases, plus determinism, plain-language, and real-examples-only checks. 8 tests, all in CI.

### Changed
- `.github/workflows/ci.yml`: added `test_capabilities_menu.py` to test discovery.

No new dependencies, no paid services, no new keys. Menu generation is deterministic and stays in sync with actual capabilities. Routing and normal workflow unchanged — menu is opt-in discovery only.

## [5.3.0] - 2026-11-18

### Added
- **Stills-first spend-safe approval gate** for AI generation workflows (from coleam00/ai-content-factory, MIT). `references/ai-generation.md` now documents a fail-closed pattern: generate cheap stills/keyframes first with per-item cost estimates, collect explicit human approval records, and only render approved items to video. No paid API call may proceed without an explicit approval record; missing or empty approval means stop with a visible message, never a silent skip. This pattern applies to any paid-generation path (AI b-roll, keyframes, image-to-video). Adapted from the content factory's explore-approve-render flow.
- **Audio/video sync drift detection** in `scripts/review.py`: new `check_sync_drift()` function detects A/V desync using ffprobe to read audio and video stream start_time and duration. Reports start offset and end duration mismatch in milliseconds (2 probes). Flags WARNING when drift exceeds ±50 ms. Measurement failures are reported as visible 'could not measure' WARN, never silent pass. Approach after coleam00/skills edit-video sync validation (MIT). Tests: `scripts/test_sync_drift.py` (7 tests, in CI).
- **Environment diagnostic script** `scripts/doctor.py`: pre-flight check for dependencies before any render. Checks Python version, ffmpeg/ffprobe (and the encoders/filters the pipeline uses: libx264, aac, loudnorm, ebur128, alimiter, xfade, drawtext), Python packages (numpy, scipy, Pillow, librosa), Node/npx for HyperFrames, fonts, and reports what will work. Exits non-zero if core dependencies are missing. Approach after coleam00/skills edit-video `doctor.py` (MIT), adapted for Reelsmith's stack. No CUDA/NVENC/torch checks (optional, not required). Tests: `scripts/test_doctor.py` (8 tests, in CI).

### Changed
- `references/ai-generation.md`: added stills-first approval gate section with workflow (generate stills, show costs, require explicit approval, render only approved items), fail-closed rules (no paid call without approval record, empty approval stops with error), and offline helpers (approval file validation). Links from storyboard workflow and the spend-control discussion in `SKILL.md`.
- `scripts/review.py check`: now calls `check_sync_drift()` during the review gate and logs sync findings to `review.json`. Drift over ±50 ms is WARNING; worse drifts are reported in milliseconds at each probe point.
- `SKILL.md`: added `doctor.py` to the "Start every job" section: run it once on a new machine before the first render, to verify dependencies.
- `.github/workflows/ci.yml`: added `test_sync_drift.py` and `test_doctor.py` to CI test discovery.

No new paid providers, no new credentials, no Higgsfield wiring. Forced alignment from edit-video skill requires torch and is omitted (out of scope; cutting-specific). Loudness checks (ebur128, true peak) already present in `review.py` since 5.2.2. Every new check is offline/free, warning-only by default, and fails visibly on tool errors (never silently passes). Attribution added to `THIRD_PARTY_NOTICES.md`.

## [5.2.2] - 2026-11-18

### Added
- Automatic motion audit during all render paths (HyperFrames, Remotion, OpenMotion). The audit runs after composition build, before or right after render, in WARNING-ONLY mode by default: findings are printed and logged visibly, but never fail or block the render. `review.py auto_audit()` helper function added.
- Shared shell helper `scripts/audit_warn.sh` for consistent WARNING-ONLY behavior across all render paths. Properly captures exit codes and distinguishes clean/FAIL/error states. Used by `render.sh` and documented in `openmotion.md` render loop.
- Opt-in strict mode via `REELSMITH_AUDIT_STRICT=1` environment variable. When enabled, FAIL findings stop the render. Default is off (WARNING-ONLY).
- Tests: `scripts/test_auto_audit.py` (12 tests) verifies that audit runs during render path, findings do not change exit code in default mode, strict mode does fail on FAIL findings, and crash/skip is surfaced. `scripts/test_audit_warn_sh.py` (6 tests) verifies shell helper behavior. All stdlib, no network.

### Changed
- `scripts/reelsmith.py render`: calls `review.auto_audit()` on each composition after build, before HyperFrames lint.
- `templates/feature-explainer/render.sh`: uses `audit_warn.sh` helper for consistent WARNING-ONLY behavior with proper exit code handling.
- `references/openmotion.md`: render loop uses `audit_warn.sh` helper instead of direct audit call to avoid aborting `set -e` loops.
- `SKILL.md`: workflow step 4 now mentions automatic audit; Scripts section updated to reflect auto-run behavior.
- `references/brand-qa.md`: checklist item 13 and commands section updated to note automatic audit during render.
- `.github/workflows/ci.yml`: Added new test files to CI test discovery.

Every workflow logs audit status. Any failure or skip prints a clear visible line (e.g. 'motion audit SKIPPED/ERROR: <reason>') rather than silently passing. One-line summary always printed: 'motion audit: N warnings' or 'motion audit: clean'. Shell helper exits 0 in default WARNING-ONLY mode (even with findings), non-zero only in strict mode with FAIL.

## [5.2.1] - 2026-11-18

### Changed
- **HyperFrames:** Bumped from `0.8.197` to `0.9.7` to align with OpenMotion's HyperFrames version. Both the main HyperFrames path and the OpenMotion path now use the same HyperFrames 0.9.7 core.
- Updated all package manifests (`hyperframes-example/package.json`, `lottie-example/package.json`), reference documentation (`references/hyperframes.md`, `references/openmotion.md`, `references/music.md`, `references/brand-qa.md`), scripts (`scripts/reelsmith.py`), getting-started guide, example READMEs, and ROADMAP to reflect the new version.
- The 0.9.0 breaking change (removing Plan v1 distributed rendering on AWS Lambda/Cloud Run) does not affect Reelsmith's local CLI usage. All CLI commands (`doctor`, `lint`, `check`, `snapshot`, `render`) remain unchanged.
- `HYPERFRAMES_NO_TELEMETRY=1` remains set to keep telemetry disabled.

No new dependencies, no new keys, no paid services.

## [5.2.0] - 2026-11-18

### Added
- OpenMotion as the third render engine, beside HyperFrames and Remotion (Marc, 2026-11-18). `references/openmotion.md` covers the pin (`nexu-io/openmotion@9e2f877`, Apache-2.0, HyperFrames 0.9.7 core), the source install with telemetry off, and what stays off (model gateway, Studio server, MCP, catalogs). It also covers the project shape that passes Studio lint, the render loop (preflight, Studio lint, snapshot, render, `verify-export.ts`, `review.py`), the 16:9, 9:16 and 1:1 settings, and how `brand.json`, captions, music and beat lock plug in. Includes portability and version-skew notes and the maturity caveats.
- `SKILL.md`: a "Pick the engine" table and a route row. HyperFrames stays the default for client and awards sizzles. Remotion is for speech-locked type and campaign matrices. OpenMotion is for a Studio timeline handoff, or for Studio lint plus frame-exact export verification.
- `openmotion-example/`: a 6.5 s kinetic title card (mask-reveal-up, ambient drift, no audio, no default look). It is Studio-lint clean and also renders on `hyperframes@0.9.7`.
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

Focus line and campaign pitch stay parked (see ROADMAP). All restated in our words; no files or prompts copied. Deliberate pins unchanged (`Codex 0.160.1`, `@openai/codex*`, `Hermes 0.22.4`).

## [5.1.3] - 2026-11-17

### Added
- `references/review-and-qa.md`: cut list, clicks at cuts, edit memory, story-short camera. After StatsPerform/video-story (@30d1c89, MIT), KellisLab/story-camera (@1876393, MIT @bc4cfa8), and thisiskeanyvy/cut-video (@2d8de78, Apache-2.0). All restated in our words; no files, prompts or classifiers copied.
- `SKILL.md`: pointers to cut list and edit memory.
- ROADMAP: three-source harvest, with what was skipped.

Licensed music only. No generative audio. Story camera and edit memory do not change the routing rules and aren't defaults.

## [5.1.2] - 2026-11-17

### Added
- LICENSE file (MIT).
- `.gitignore` that excludes common intermediate files, Python cache, and the vendored Remotion tgz.

## [5.1.1] - 2026-11-17

### Changed
- README: added Examples section with gallery image and preview GIFs linking to full MP4 samples.

## [5.1.0] - 2026-11-17

Initial public release.
