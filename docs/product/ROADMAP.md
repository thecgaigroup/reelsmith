Title: Reelsmith
Type: Operating Doc (Roadmap)
Owner: Marc Wojcik
Status: Draft
Last Reviewed: 2026-11-26
Reviewers: Marc Wojcik
Supersedes: ROADMAP.md (as the plan)

# Reelsmith roadmap

## Summary

This is the current plan. The [former roadmap](../../ROADMAP.md) keeps the craft notes and parked ideas. First make the local brief and render contract reliable, then use it in Ignition and show job outcomes in Orbit. GitHub issues labelled `roadmap` track the milestones.

**API first, UI second.** Reelsmith API v1 comes before any UI that uses it. The Orbit status record also lands before the Orbit view.

## Done

| Item | Evidence |
|---|---|
| HyperFrames template renders and a Remotion narrated explainer | [Skill workflow](../../SKILL.md#workflow-templates) and [templates](../../templates/) |
| Optional OpenMotion render path and preflight | 5.2.0 in the [changelog](../../CHANGELOG.md) |
| Vertical clipping from long-form footage and stream-highlights mode | 5.4.0 and 5.5.0 in the [changelog](../../CHANGELOG.md) |
| Opt-in vertical caption safe layout and frame-0 checks | 5.6.0 in the [changelog](../../CHANGELOG.md) |
| Opt-in offline finish pass with sound cues and title depth of field and bloom | 5.7.0 in the [changelog](../../CHANGELOG.md) |

## Phase 1. Brief to reviewed export

| # | Milestone | Requirements | Exit criteria | Issue |
|---|---|---|---|---|
| 1.0 | Reelsmith API v1 | FR-B1, FR-API1, FR-API2, FR-API3, FR-API4 | The repo has a semver CLI contract and JSON schemas for briefs, jobs and results. Hosted CI fails on schema or CLI drift. Any render service included in v1 has a checked-in OpenAPI spec and runs the same contract tests against its implementation. UIs are clients of the contract. | #50 |
| 1.1 | HyperFrames reference render | FR-B1, FR-B2, FR-API2 | A synthetic brief passes dry run and produces playable horizontal and vertical cuts and schema-valid job results in hosted CI. An invalid brief returns a structured error before rendering. | #51 |
| 1.2 | Document and verify the Remotion path | FR-B2, FR-API2 | A narrated sample rendered with the documented Remotion command plays with synchronized captions. The supported-engine table states which Remotion inputs and outputs v1 covers and links to the separate invocation for the rest. | #52 |
| 1.3 | Review evidence and approved export | FR-Q1, FR-Q2 | A vertical speech fixture produces review evidence for captions, framing, brand and audio. Standard export refuses a pending review and produces delivery files and credit notes after approval. | #53 |

## Phase 2. Integrated with CGAI

| # | Milestone | Requirements | Exit criteria | Issue |
|---|---|---|---|---|
| 2.1 | Ignition render step | FR-I1, FR-API3 | An Ignition sample workflow dry-runs a brief, renders it, and retrieves output and QA references through the documented interface. An invalid brief fails the workflow step with a readable reason. | #54 |
| 2.2 | Orbit job status feed | FR-I2, FR-API2 | A valid test job and a failed job emit schema-valid terminal records with elapsed time and review outcome where available. The failed record contains a scrubbed reason. A contract test rejects records with local paths. | #55 |
| 2.3 | Orbit render status view | FR-I2, FR-API3, FR-API4 | With shared sign-in, Orbit shows the state, elapsed time and review outcome of the successful sample and the reason the failed sample stopped. The values match the status records from 2.2. | #56 |

## Order and dependencies

- The contract in 1.0 sets the inputs and outputs for the reference render and review work. Record the supported engine paths as part of v1.
- Ignition uses the same interface as the CLI workflow. Orbit reads the status record from 2.2. If either integration needs a render service, land its OpenAPI contract and tests before the consuming UI.

## How a milestone closes

Record the exit evidence in its GitHub issue. The PR goes through independent review and green CI.
