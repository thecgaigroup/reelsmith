# Reelsmith v5.1

**This file is the canonical agent guidance for this repository (MEGA_LOOP_CONTRACT:v1).** Codex and Cursor read it natively; Claude Code reads CLAUDE.md, which imports this file via `@AGENTS.md`.

## Session start

When beginning a new agent session in this repository:

1. Read this file (AGENTS.md) completely
2. Read the top 2-3 entries of `docs/devlog.md` to understand recent changes
3. Check repository state: `git status --short` and `git log --oneline -8`
4. Note the current branch
5. If this repo has a `loop/` directory, also run `make doctor` and `make queue`
6. Require or create a Paperclip ticket key for this work
7. Label the Herdr pane with `ticket=<KEY>`
8. Post a 5-line briefing to the ticket describing the task
9. Define `done_when` conditions before beginning implementation work

## Session close

When completing an agent session in this repository:

1. Prepend a dated entry to `docs/devlog.md` with these sections:
   - **What changed**: Brief summary of modifications
   - **State**: Current status (working/broken/blocked)
   - **Where we left off**: Next steps for future sessions
   - **Open**: Outstanding questions or issues
2. Commit all changes to a feature branch (never push directly to `main`)
3. Open a pull request with clear description
4. Run a `codex-reviewer` Herdr pane in read-only mode
5. Wait for the review verdict and record the head commit SHA between `REVIEW-BEGIN` and `REVIEW-END` markers
6. Only merge when: LAND directive appears at HEAD AND all CI checks are green
7. Post evidence of completion to the Paperclip ticket
8. If this repo has a `loop/` directory, also run `make lineage`

## Repository

See README.md for what this repository is and how it is organized, and SKILL.md for the skill entry point.
