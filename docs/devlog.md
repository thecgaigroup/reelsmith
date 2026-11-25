# Development Log

## 2026-11-25 (Finish pass review round 5)

**What changed**
- Ranked caption candidates by backing and position before choosing a baseline. The checker measures source strokes separately and verifies their contrast at the destination.
- Replaced region-wide reveal checks with connected-component measurements and sampled every frame from 0.4 to 0.8 seconds.

**State**
- The round 5 patch is uncommitted in the assigned worktree for PR #46.

**Where we left off**
- The local build report records the encoded regressions, Signal crop inspection, and repeated flag-off comparison.

**Open**
- Independent review is pending. The local stream-highlights integration requires FFmpeg with libass.

## 2026-11-25 (Finish pass review round 4)

**What changed**
- Relocated centered short captions by local contrast and position across the full height of the caption band. The checker compares source and destination strokes independently of relocation alpha.
- Filled the full padded source regions on every frame from surrounding background and added a sampled encoded-picture gate for reveal leftovers.
- Fit the Signal captions left of TikTok's right rail at 72% of the original width and 70% of the height.

**State**
- The round 4 patch is uncommitted in the assigned worktree for PR #46.

**Where we left off**
- The local build report records the round 4 regression results, Signal crop inspection, and repeated flag-off baseline comparison.

**Open**
- The patch awaits independent review. The local stream-highlights integration requires FFmpeg with libass.

## 2026-11-25 (Finish pass review round 3)

**What changed**
- Gated preset delivery on the encoded opening frame, retained centered one- and two-glyph captions, and tied source fill to the pixels actually relocated.
- Bound the finish report to the MP4 by SHA-256 and byte size. The MP4 is renamed first and the report follows.

**State**
- The round 3 patch is in the assigned worktree for PR #46.

**Where we left off**
- The local build report maps each finding to its regression and records the verification results.

**Open**
- The round 3 patch awaits independent review. Local stream-highlights integration requires FFmpeg with libass.

## 2026-11-25 (Finish pass review round 1)

**What changed**
- Preserved the opening cover through preset FPS conversion and retained the original A/V lead or lag through mastering and export.
- Restricted local media input protocols, clustered caption masks around aligned glyphs, and added independent opening-frame text checks.
- Staged the report ahead of MP4 replacement and added flag-off golden coverage for the audio-mastering and mux commands.

**State**
- The local Signal render and checker pass with 23 cues, −14.0 LUFS and −1.3 dBTP. Flag-off audio-bearing Reels export and thumbnail match the local `origin/main` results byte for byte.

**Where we left off**
- The local build report maps the six review findings to fixes and regression evidence. The round 1 patch is committed on `feat/finish-pass-flag`.

**Open**
- The updated patch awaits independent review. The local stream-highlights integration test requires an FFmpeg build with libass.

## 2026-11-25 (Opt-in finish pass)

**What changed**
- Added a local finish pass for baked masters with verified CC0 sound cues, one audio mastering stage, layout-based anchor relocation, title depth of field and bloom, and a replacement opening cover.
- Keyed the relocated pill and captions per frame so their backing follows the visible text and empty bands leave the destination picture clear.
- Routed approved exports through the pass only when `REELSMITH_FINISH_PASS` is enabled and added regression tests to the CI list.

**State**
- The reference Signal master passes the cover, safe-zone, encoded audio, and timeline gates. Flag-off Reels export and thumbnail match the local `origin/main` results byte for byte.
- The local CI run has the known stream-highlights integration failure because this FFmpeg build lacks libass.

**Where we left off**
- The author changes are in the assigned feature worktree. The local build report records measurements and suggested commit groupings.

**Open**
- The Signal caption band intersects TikTok's right-rail advisory region. The release and independent review workflows are outside this author pass.

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
