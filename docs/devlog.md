# Development Log

## 2026-11-25 (Reelsmith 5.6.0: Safe layout for vertical 9:16 Shorts)

**What changed**
- Added opt-in `--safe-layout` flag for vertical 9:16 content (Reels, TikTok, Shorts) that positions UI elements and captions inside documented safe zones
- Created `templates/_shared/safe_zones.py` module with `SafeZones` class and convenience functions for calculating platform-safe margins, caption bands, and badge/pill positions
- Updated `scripts/captions.py` to support `--safe-layout` flag: when enabled for 9:16, uses safe zone margins (540px bottom, 120-770px horizontal caption band) instead of legacy positioning (691px bottom, 86-994px horizontal)
- Added `scripts/test_frame0_cover.py` for validating frame 0 meets luma mean ≥ 16, stddev ≥ 12, and is no more than 5% darker than source hero art (uses ffmpeg signalstats filter)
- Created `templates/signal-short/` demonstration template showing safe layout in action: title reveal with center line, cyan/purple keywords, badge (top-left), pill (top-right), key points over hero art
- Added comprehensive test suite: `test_safe_zones.py` (calculations), `test_safe_layout_captions.py` (caption positioning), `test_safe_layout_integration.py` (flag behavior and backward compatibility)
- Created `references/safe-layout.md` complete guide covering usage, platform requirements, testing, and backward compatibility
- Generated demonstration artifacts: `signal-short-frame0-safe-on.png` and `signal-short-frame0-safe-off.png` showing UI element positioning differences
- Bumped VERSION to 5.6.0 and updated CHANGELOG with complete feature description

**State**
- Working: all 7 new tests pass (safe zones, captions, integration), all existing tests unchanged
- Default is OFF for backward compatibility: output is byte-for-byte identical to 5.5.1 when flag is absent
- Safe zone numbers: top 220px, bottom 480px, left 120px, right 310px (strictest combination of Reels/TikTok/Shorts)
- Caption band: 120-770px horizontal (650px usable, clears TikTok right rail)
- Frame 0 strong cover requirement enforced when flag is on

**Where we left off**
- Branch: cursor/safe-layout-vertical-shorts-f7c0
- Ready for PR: all changes committed, tests pass, documentation complete
- Artifacts saved to /opt/cursor/artifacts/ (frame-0 stills showing safe vs legacy layout)
- Next: open PR, run CI, do NOT merge

**Open**
- Need CI validation on PR
- Frame-0 quality checker works with ffmpeg signalstats; actual video rendering not tested in this branch (would need HyperFrames full setup)
- Signal Short template is demonstration only; real production templates would adapt the safe_layout flag in their build.py

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
