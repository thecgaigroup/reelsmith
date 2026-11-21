# Development Log

## 2026-11-21 (Reelsmith 5.3.1: CI smoke test)

**What changed**
- Added CI smoke test workflow (`.github/workflows/smoke.yml`) that validates fundamentals on every PR and push to main
- Extracts HyperFrames and OpenMotion pins from reference markdown files and verifies they resolve upstream (npm view + git ls-remote)
- Verifies core scripts and key reference files exist
- Runs a real minimal headless render: product-launch template, ~1.5s duration, 640×360 resolution, synthetic content only, no paid voice/generation
- Runs `review.py check` on the rendered output (not dry-run) to verify the review pipeline works
- Guards against paid generation: all API keys unset in job-level env, REELSMITH_IGNORE_KEYS=1, --allow-paid never passed
- Uses pinned action versions (checkout@v4.2.2, setup-node@v4.1.0, setup-python@v5.3.0)
- Bumped VERSION to 5.3.1 and updated CHANGELOG and README

**State**
- Working: real render path tested and passing
- CPU-only, $0 cost, completes in ~1-2 minutes
- Runs on every PR and push to main

**Where we left off**
- Branch: cursor/ci-smoke-test-6d83
- PR #29 addressing round 1 review feedback
- Implementing real render (not dry-run), upstream pin validation, and failure demonstrations

**Open**
- Need to push fixes and create failure demonstration runs

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
