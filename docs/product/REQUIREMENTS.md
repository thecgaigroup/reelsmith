Title: Reelsmith
Type: Operating Doc (Requirements)
Owner: Marc Wojcik
Status: Draft
Last Reviewed: 2026-11-26
Reviewers: Marc Wojcik
Supersedes: None

# Reelsmith requirements

## Summary

Reelsmith is the open-source skill for taking a video from brief to reviewed export. Its workflow starts with a plan and uses code, templates, a brand kit and captions to make and check the cut. This PFR defines the interface CGAI products and other agents can build on. The current workflow is in [SKILL.md](../../SKILL.md).

## Tenets

1. **Plan before rendering.** Match the template or engine to the brief. Use a storyboard for a multi-beat cut and review the draft before delivery.
2. **Keep a local path.** The reference render should work on a prepared machine with supplied media and no sign-in.
3. **API first, UI second.** Design the brief, job and result contract first so a person or agent can run the same job.
4. **One CGAI.** Work should be “frictionless” across products that are “integrated and work together”, with “one login for all” on hosted CGAI surfaces and “the same or similar connectors like grokbot does to outside tools or mcp” where workflows reach external tools.

## Goals and non-goals

### Goals

- **G1.** Turn a brief into a repeatable branded render with review evidence.
- **G2.** Let agents plan, render and inspect results through a stable interface.
- **G3.** Let Ignition workflows run video jobs and Orbit show how those jobs went.

### Non-goals (now)

- Building a general-purpose timeline editor or a mandatory render service.
- Uploading or posting videos from Reelsmith.

## Users

| User | Needs |
|---|---|
| Video maker | A fast way to plan, preview, review and export a branded cut |
| Developer or coding agent | Documented inputs, errors and outputs that work in a script |
| CGAI workflow operator | A render step for products such as Signal Studio and visible run outcomes in Orbit |

## Functional requirements

### FR-B. Brief and render (G1, G2)

- **FR-B1 Brief and plan.** Validate template inputs, brand, media, aspect and caption settings before rendering. A dry run returns the resolved plan or tells the caller what to fix.
- **FR-B2 Render from code.** Document the HyperFrames template path and the Remotion path. Produce a video and job record from the same accepted brief for each supported aspect. Document which combinations v1 supports.

### FR-Q. Review and export (G1)

- **FR-Q1 Review evidence.** Return the review outcome and evidence references. For speech, check caption timing and safe placement, including the opt-in vertical layout. Check framing, brand and audio before delivery.
- **FR-Q2 Approved export.** Use the existing review approval path before standard delivery export. Return delivery files and any required credit or disclosure notes.

### FR-I. CGAI integration (G3)

- **FR-I1 Ignition render step.** Let workflows validate a brief, request a render and retrieve job state, result and QA references through the documented interface. Reuse CGAI connectors for external tools when needed.
- **FR-I2 Orbit reporting.** Report job ID, state, elapsed time, failure reason and review outcome through a versioned status record. Orbit displays that record on the shared CGAI sign-in.

## API first (FR-API)

Marc, 2026-11-26: “we build everything api first ui second”.

- **FR-API1 Documented, versioned API.** Check the CLI contract and JSON schemas for briefs, render jobs and results into the repo. Use semantic versioning and record breaking changes in the changelog. If a render service exists, check in a versioned OpenAPI spec for it using the same payloads.
- **FR-API2 Contract tests in CI.** Validate fixtures against the schemas and test CLI behavior and outputs on GitHub-hosted CI. For a render service, test its implementation against OpenAPI. Drift fails the build.
- **FR-API3 The UI is one client.** Any UI uses the same documented interface and job data as agents. No UI-only endpoints.
- **FR-API4 API milestone before UI milestone.** Land each feature's API milestone before the UI milestone that uses it.

The current `reelsmith.py render` CLI accepts template content JSON, a brand kit, an aspect and an output directory. `--dry-run` produces a resolved `job.json`; a completed render also writes `job.json`. The Remotion explainer has a separate render script today. The v1 contract defines the supported brief fields, dry-run and render inputs, job status and errors, and references to output and review artifacts.

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | Run a small reference render and the contract checks on GitHub-hosted CI. The reference path runs without provider credentials. |
| NFR-2 | Keep checked-in examples synthetic or cleared for redistribution. Keep media and local paths out of status reports. |
| NFR-3 | Return a machine-readable failure when a render fails or when a required artifact is missing. |

## Guardrails

- **GR-1** Only spend, credentials and irreversible deletes wait for Marc. Production deploys and publishing follow decide-and-show. Record the decision and show the result to Marc. Reelsmith itself stops at delivery files.
- **GR-2** Use media, marks, voices and likenesses with permission. Carry credits and synthetic-media disclosures when required.
- **GR-3** Preserve the human review gate for delivery. Changes land after independent review and green CI.

## Success metrics

| Measure | How to verify |
|---|---|
| Brief-to-export completion | A repository fixture produces a plan, playable video, review record and approved export. |
| Contract conformance | Hosted CI accepts valid fixtures and rejects invalid briefs and mismatched job results. |
| Render visibility | A successful job and a failed job show matching terminal states in the CLI result and Orbit. |
| Time to first preview | Measure elapsed time from valid brief to playable preview on the reference path. Baseline and target are open. |

## Risks and mitigations

- Renderer upgrades can change font metrics, layout or timing. Run the existing smoke render and review sample artifacts before updating pins.
- The render record can carry local paths or production details. Report only job state, timings, review outcome and a scrubbed failure reason to Orbit.
- Template and engine options differ. Document the supported v1 combinations and reject unsupported input before rendering.

## Open questions

- Which render paths beyond the HyperFrames reference template belong in API v1?
- When would a render service be needed, and what artifact access would it offer?
- What preview-time baseline and target should the reference render use?
- Which shared connector will carry render status to Orbit?
