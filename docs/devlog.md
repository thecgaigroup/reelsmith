# Development Log

## 2026-11-21 (Reelsmith 5.4.0: long-form to vertical 9:16 clipping lane)

**What changed**
- Added complete long-form to vertical 9:16 clipping lane for extracting face-tracked highlight moments from local videos
- Created `scripts/highlights.py`: highlight detection using transcript + audio energy heuristics (no LLM, $0)
- Created `scripts/facetrack.py`: face tracking with OpenCV Haar cascades + supervision for stable 9:16 crop windows
- Created `scripts/clipping.py`: main orchestrator integrating highlights, tracking, caption shifting, and review
- Created `scripts/test_clipping.py`: comprehensive tests for all 5 task requirements (8 tests, all pass)
- Added `references/clipping.md`: complete documentation including workflow, when to use/not use, techniques harvested, limitations
- Updated README.md with "When to use the clipping lane" section
- Updated SKILL.md route table to include clipping workflow
- Updated CHANGELOG.md with full 5.4.0 entry including attribution and dependency license table
- Bumped VERSION to 5.4.0
- Updated CI workflow to install new dependencies (opencv-python, supervision, pysubs2) and run clipping tests

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
  5. ✅ 48kHz audio check passes on clips
- Dependencies verified: opencv-python (Apache-2.0), supervision (MIT), pysubs2 (MIT) - no GPL/AGPL/LGPL/MPL
- Techniques harvested from AI-Youtube-Shorts-Generator (MIT) and re-implemented
- No LLM required - uses transcript + audio energy heuristics for highlight scoring
- Awaiting CI results and review

**Open**
- None: implementation complete, all tests pass, documentation comprehensive

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
