Title: Reelsmith
Type: Operating Doc (PRFAQ)
Owner: Marc Wojcik
Status: Draft
Last Reviewed: 2026-11-26
Reviewers: Marc Wojcik
Supersedes: None

# Reelsmith PRFAQ

## Press release

*Working-backwards draft written as if the product described here has launched. The roadmap records what has shipped.*

### The CGAI Group launches Reelsmith, an open-source skill that takes video from brief to reviewed export

The CGAI Group today launched Reelsmith for makers and coding agents who build launches, explainers and short videos. Start with a brief, see the plan, then make a reviewable cut with the right brand, captions and aspect ratio.

**The problem.** When each video starts from scratch, every cut means checking the brand, captions and framing again. An agent can make a draft quickly, but the person reviewing it still needs to see what changed and whether it is ready to deliver.

**The solution.** Reelsmith uses HyperFrames for template-driven video and Remotion for narrated, speech-timed work. A brand kit carries the logo, colors and type. The review step produces contact sheets and a phone-size preview. After approval, export produces files for the intended format. A versioned CLI and JSON contract give agents the same path through the job each time.

**How it fits CGAI.** Reelsmith is how CGAI products such as Signal Studio make video. Ignition builds agent workflows that can validate a brief, run a render and retrieve the result. Orbit is the company dashboard where render state, failures and review outcomes are visible. CGAI products share sign-in and connector conventions where they connect.

**From Marc Wojcik, owner.** “we build everything api first ui second”.

**Getting it.** Follow the [Reelsmith setup guide](../../README.md#install) and try a [sample template](../../README.md#examples).

## Customer FAQ

**What can I make?**  
Product launches, recaps, tutorials and narrated explainers. The clipping tools can also turn long-form footage into vertical highlights.

**Can I use my own brand and footage?**  
Yes. Pass a brand kit and supply media you have permission to use. Caption tools support sidecar files or burn-in, and the vertical safe-layout option keeps captions clear of the documented overlays.

**Can I run it locally?**  
Yes. Follow the setup guide for the renderer and tools you need. The reference template path can render with supplied media and voice turned off.

**Will Reelsmith post the result for me?**  
Reelsmith prepares files for delivery. Posting is handled by the caller.

## Internal FAQ

**What does API first mean for a video skill?**  
The API is the versioned brief and render interface. The current HyperFrames CLI takes template content JSON and brand information, supports a dry run, and writes `job.json`. The planned contract gives callers documented JSON schemas for briefs, jobs and results. A render service, if added, describes the same contract in a checked-in OpenAPI spec. Any UI uses the same interface.

**How does Reelsmith fit the other products?**  
Marc wants CGAI products “integrated and work together”, with “one login for all” and “the same or similar connectors like grokbot does to outside tools or mcp”, so working across them feels “frictionless”. Orbit is “our center of the universe”. Reelsmith's CGAI integration reports job state, duration, failure reason and review outcome there. Ignition “will be the piece that builds agents and agent workflows”. It can use the same interface to plan, render and retrieve output references and QA results. Shared sign-in applies to CGAI-hosted surfaces. The public local CLI runs on its own.
