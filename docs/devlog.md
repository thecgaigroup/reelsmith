# Development Log

## 2026-11-26 (Reelsmith product docs)

**What changed**
- Added a product docs index, PRFAQ, requirements and roadmap. The root roadmap points to the new docs and stays as history.

**State**
- Product docs are in draft. The roadmap records what has shipped and marks proposed milestones for issue tracking.

**Where we left off**
- The first milestone versions the brief and render interface. The roadmap puts that work and the status feed before the Orbit view.

**Open**
- Confirm which render paths belong in API v1, whether a render service is needed, and which shared connector will carry render status to Orbit.

## 2026-11-25 (Reelsmith 5.7.0)

- Rebased the finish-pass branch onto main after #47 took 5.6.0. This release is 5.7.0. The finish-pass CHANGELOG entry sits above the 5.6.0 safe-layout notes, and CI runs both test lists.

## 2026-11-25 (Reelsmith 5.6.0 round 4)

**What changed**
- Added a CFR and A/V alignment preflight, bounded the single AAC mix to the picture, and verified cue accounting in `check`.

**State**
- Local, uncommitted changes for PR #48 on `feat/finish-pass-slim-r4`.

**Where we left off**
- Signal rendered 23 cues, matched the round 3 MP4 SHA-256, and passed `check`. Local evidence is in `.finish-slim/FIX4_REPORT.md`.

**Open**
- Local FFmpeg lacks libass for the stream-highlights end-to-end test. Independent review and hosted CI are pending.

## 2026-11-25 (Reelsmith 5.6.0 round 3)

**What changed**
- Planned cues from frame timestamps, retained full early cues in the default mix, and reported rendered and skipped cues.
- Extended encoded mastering retries and added explicit diagnostics for short pictures and silent mixes.

**State**
- Local fixes for PR #48 on `feat/finish-pass-slim-r3`.

**Where we left off**
- Regression, CI-list and Signal render evidence is in `.finish-slim/FIX3_REPORT.md`.

**Open**
- Independent review and hosted CI are pending.

## 2026-11-25 (Reelsmith 5.6.0 review fixes)

**What changed**
- Suppressed bytecode writes on disabled runs and extended short programme tracks so late sound cues survive mastering.
- Preserved the static top and bottom strips in the bundled 9:16 layout with feathered edges around the central blur and title bloom.
- Added a clean error for scene CSVs with a missing or blank first row and regression coverage for all four findings.

**State**
- Local fix round for PR #48 on `feat/finish-pass-slim`.

**Where we left off**
- Local verification results and the Signal checks are recorded in `.finish-slim/FIX_REPORT.md`.

**Open**
- Independent review and hosted CI remain pending.

## 2026-11-25 (Reelsmith 5.6.0)

**What changed**
- Added an opt-in offline pass for ducked CC0 sound cues, encoded AAC loudness verification, and title depth of field and bloom.
- Added synthetic tests to CI and documented the finish command.

**State**
- Local author patch on `feat/finish-pass-slim`, uncommitted until the orchestrator commits it.

**Where we left off**
- The local build report records the synthetic tests and Signal Short verification.

**Open**
- Orchestrator review and hosted CI are pending.

## 2026-11-21 (Reelsmith 5.4.1: CI smoke test)

**What changed**
- Added CI smoke test workflow (`.github/workflows/smoke.yml`) that validates fundamentals on every PR and push to main
- Extracts ALL HyperFrames and OpenMotion pin occurrences (prose "pinned at X" + all commands "hyperframes@X") and verifies they all match and resolve upstream
- Fails if any pin occurrence disagrees (prose vs command mismatch) or if the pin doesn't resolve on npm/git
- Verifies core scripts and key reference files exist
- Runs a real minimal headless render: product-launch template, ~1.5s duration, 640×360 resolution, synthetic content only, no paid voice/generation
- Runs `review.py check` on the rendered output (not dry-run) to verify the review pipeline works
- Guards against paid generation: all API keys unset in job-level env, REELSMITH_IGNORE_KEYS=1, --allow-paid never passed
- Uses pinned action versions (checkout@v4.2.2, setup-node@v4.1.0, setup-python@v5.3.0)
- Merged origin/main (9c4e47e) including PR #28 (5.4.0 clipping lane)
- Bumped VERSION to 5.4.1 and updated CHANGELOG and README

**State**
- Working: real render path with ALL pin occurrences checked
- CPU-only, $0 cost, completes in ~1-2 minutes
- Runs on every PR and push to main

**Where we left off**
- Branch: cursor/ci-smoke-test-6d83
- Merged origin/main (9c4e47e) with 5.4.0
- Ready for final CI validation and failure demonstrations

**Open**
- Need to verify PR is mergeable and CI runs green
- Create failure demo PRs showing pin mismatch and nonexistent pin detection

## 2026-11-21 (Reelsmith 5.4.0: long-form to vertical 9:16 clipping lane)

**What changed**
- Added complete long-form to vertical 9:16 clipping lane for extracting face-tracked highlight moments from local videos
- Created `scripts/highlights.py`: highlight detection using transcript + audio energy heuristics (no LLM, $0)
- Created `scripts/facetrack.py`: face tracking with OpenCV Haar cascades with IoU-based tracker IDs for stable 9:16 crop windows
- Created `scripts/clipping.py`: main orchestrator integrating highlights, tracking, caption shifting, and review
- Created `scripts/test_clipping.py`: comprehensive tests for all 5 task requirements (8 tests, all pass)
- Added `references/clipping.md`: complete documentation including workflow, when to use/not use, techniques harvested, limitations
- Updated README.md with "When to use the clipping lane" section
- Updated SKILL.md route table to include clipping workflow
- Updated CHANGELOG.md with full 5.4.0 entry including attribution and dependency license table
- Bumped VERSION to 5.4.0
- Updated CI workflow to install new dependencies (opencv-python, pysubs2) and run clipping tests

**State**
- Working: all 102 tests pass (8 new clipping tests + 94 existing tests)
- All CI checks expected to pass (lints, type checks, builds, tests)
- PR #28 opened against main: https://github.com/thecgaigroup/reelsmith/pull/28
- HEAD commit: 34244e0b9d4693ad6e8337da4b56cb83e8013531
- Branch: cursor/clipping-lane-5-4-0-251d

**Where we left off**
- PR is ready for review with complete test results and dependency license verification
- All 5 task requirements met:
  1. ✅ Highlight JSON has score/hook/reason/start/end; clips are 9:16 and duration matches within 1 frame
  2. ✅ Tracked subject center stays in crop window ≥95% of frames
  3. ✅ Continuous segments keep single tracker_id
  4. ✅ SRT shifting preserves cue count and moves last cue end by T
  5. ✅ 48kHz audio passes without quality warning

**Open**
- None: all tasks complete, tests passing, ready for review

## 2026-11-18 (Reelsmith 5.2.2: auto motion audit during render)

**What changed**
- Added automatic motion audit integration for all render paths (HyperFrames, Remotion, OpenMotion)
- Created `review.auto_audit()` helper function that runs audit in WARNING-ONLY mode by default
- Integrated audit into `scripts/reelsmith.py` render (after composition build, before HyperFrames lint)
- Updated `templates/feature-explainer/render.sh` to run audit on Remotion source before rendering
- Updated `references/openmotion.md` render loop to include audit step before Studio lint
- Added opt-in strict mode via `REELSMITH_AUDIT_STRICT=1` environment variable (default: off)
- Updated docs: `SKILL.md` workflow and scripts section, `references/brand-qa.md` checklist and commands
- Created comprehensive tests in `scripts/test_auto_audit.py` (12 tests, all passing)
- Bumped VERSION to 5.2.2 and added CHANGELOG entry

**State**
- Working: all tests pass (18 total: 12 auto_audit + 6 shell helper + existing motion_audit)
- Review feedback addressed: shared shell helper, proper exit code handling, WARNING-ONLY spelling
- Rebased onto main (f10d6f4) with PR #25 (HyperFrames 0.9.7)
- CHANGELOG ordered correctly: 5.2.2 then 5.2.1
- VERSION: 5.2.2
- All render paths use shared audit_warn.sh helper for consistent behavior

**Where we left off**
- Branch force-pushed after rebase: cursor/auto-motion-audit-5-2-2-e009
- Head commit: f1d9283
- PR #26 updated and ready for re-review
- CI includes new test files

**Open**
- None: all review feedback addressed and tests passing

## 2026-11-16

**What changed**
- Added root AGENTS.md with MEGA_LOOP_CONTRACT:v1 standard agent session guidance (Session start and Session close sections)
- Added root CLAUDE.md that imports AGENTS.md
- Created docs/devlog.md for tracking development history

**State**
- Working: all three documentation files created and committed to cursor/adopt-agent-session-standard-0e49 branch
- No code changes, tests, workflows, or other files modified
- No nested AGENTS.md or CLAUDE.md files exist in this repository

**Where we left off**
- Documentation-only PR ready for review
- Agent session contract (MEGA_LOOP_CONTRACT:v1) adopted from acos-core repository standard
- PR includes deterministic checks showing only the three intended files changed

**Open**
- None: this is a pure documentation adoption with no implementation concerns
