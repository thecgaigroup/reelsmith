# Reelsmith roadmap

Parked work. Do not start these until the current release gates elsewhere are stable, unless the owner asks for a spike.

## Fold in local FFmpeg edit helpers (no sidecar)

**Status:** parked  
**Source of ideas:** [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (local FFmpeg toolset + MCP for coding agents: cut, captions, reframe, loudness, platform exports)

**Decision:** Do **not** depend on that package as a sidecar or MCP dependency. Break down what is useful and add it **directly** into Reelsmith (scripts, `references/helpers.md`, and any thin wrappers that fit the existing `scripts/` style).

**Goals when we pick this up:**
- Inventory the upstream tools/recipes against what Reelsmith already covers (`export.py`, `captions.py`, `review.py`, `beats.py`, and the ffmpeg recipes in `helpers.md`).
- Port the gaps that matter for editing finished footage (trim/cut, reframe/crop for platform, loudness, simple stitch) as first-party helpers beside Remotion/HyperFrames — complementary, not a replacement for templates.
- Keep the free/offline path; no new cloud keys. Prefer stdlib + system ffmpeg, same as today.
- License-check anything copied; rewrite rather than vendor the whole repo.
- Document new commands in `references/helpers.md` and mention them in the SKILL.md route table only if they become a primary job path.

**Out of scope for this item:** shipping a separate MCP server package, or requiring users to install ffmpeg-skill alongside Reelsmith.

## Design/motion studio ideas (Amir Mushich list, Oct 2026)

**Status:** parked  
**Source:** [AmirMušić post](https://x.com/AmirMushich/status/2113692928824484078) — “10 GitHub repos to turn you into a design/motion studio”

**Already covered by Reelsmith:** [HyperFrames](https://github.com/heygen-com/hyperframes), [Remotion](https://github.com/remotion-dev/remotion). No action.

**Decision:** Same as FFmpeg — **fold useful bits in**, do not add these repos as sidecars or required dependencies. Inventory → port gaps → document in `references/` / templates.

### Port candidates (priority)

1. **[video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)** — page/capture + ~150 shot recipes → Remotion promo. Closest upgrade path for existing Remotion templates and product-launch / feature-explainer flows.
2. **[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)** — 59 film looks implemented in code (no video model). Candidate for a first-party style/look library next to motion-design helpers; zero spend.
3. **[impeccable](https://github.com/pbakaus/impeccable)** — anti AI-slop design skill with rule-based checks. Candidate to harden Remotion/HyperFrames visual QA (alongside `review.py`), not a full design-system product.

### Explicitly out of scope for Reelsmith

- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), [Penpot](https://github.com/penpot/penpot), [diagram-design](https://github.com/cathrynlavery/diagram-design) — product UI / design-file tooling, wrong lane.
- [blender-mcp](https://github.com/ahujasid/blender-mcp), [img2threejs](https://github.com/img2threejs/img2threejs) — 3D stacks; not Reelsmith’s template/render path.

**When:** parked until other release gates are stable, unless the owner asks for a spike sooner.
