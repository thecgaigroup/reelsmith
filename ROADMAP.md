# Reelsmith roadmap

Parked work. Do not start these until the current release gates elsewhere are stable, unless the owner asks for a spike.

## Client sizzle is storyboard-first (2026-10-24)

**Status:** in the skill

Awards, partner, and client sizzles now require a storyboard before the edit — `storyboard.json` plus HTML (proportional timeline, brief-beat alignment, shot cards, HAVE/ID/NEED/TEMP) — and a brand QA gate before anything leaves the box. See [references/storyboard.md](references/storyboard.md), [references/client-sizzle.md](references/client-sizzle.md), and [references/brand-qa.md](references/brand-qa.md). The generic pattern (no client media) is in [examples/storyboard/](examples/storyboard/). Showreel kinetic type for that lane is in [references/motion-design.md](references/motion-design.md) (2026-10-25).

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

## Opus 5.5 motion-studio craft (fold-in)

**Status:** kinetic type, transitions, and the comparison bar are in the skill (2026-10-25). The rest of this list stays parked.  
**Sources:** public posts and articles. No course pack to clone.

- [Florence (@flxrnc), Opus 5.5 Motion Lab](https://x.com/flxrnc/status/2105311836190978392)
- [Movez (@0xMovez), How to build a motion design studio with Opus 5.5](https://x.com/0xMovez/status/2104216919033192746)
- Skip Hamza (@humzaakhalid) — a pointer to repos only. The free post is a newsletter funnel; no verifiable unique GitHubs beyond the shared list.

**Already covered by Reelsmith:** [HyperFrames](https://github.com/heygen-com/hyperframes), [Remotion](https://github.com/remotion-dev/remotion) (and its AI skills), the review/export path, contact sheets (`review.py`), loudness at -14 LUFS, beat grid (`beats.py`), and the plan → approve → draft → review gate.

**Decision:** Fold useful craft rules and recipes **directly** into Reelsmith. Do **not** clone course packs or add sidecars. Do **not** add a third `seek(t)` renderer beside HyperFrames and Remotion.

### In the skill (do not re-park)

Written as original recipes in [references/motion-design.md](references/motion-design.md) (Showreel kinetic type), and pointed at from client-sizzle, HyperFrames, Remotion, brand QA, and the review gate. `review.py` appends the six scores to `review.md` and does not change pass/fail.

1. **Render contract** — a pure function of time, mapped onto the paused GSAP timeline or `useCurrentFrame()`. No clocks or randomness in render mode.
2. **Motion ban list** — centered title on a gradient, fade-in-everything, corner labels and frame borders, glow on UI chrome, generic particle bursts, blurry scaled text. One display face, one UI face, one accent unless the brief says otherwise. A new event every 2–4 s.
3. **Springs** — closed-form, tiny overshoot on UI, none on display type. Stagger, holds, and the WCAG flash cap stay in the numbered motion rules.
4. **Critique before the full render** — contact sheet and `phone.jpg` already produced by `review.py`. Score hook / phone / motion / variety / brand / sound.
5. **Product films** — real screenshots, logo, and colors. Never invent UI. Paid generation stays quote-first (`references/ai-generation.md`).
6. **Transitions and slideshow grammar** — one primary seam, match-cut when continuity holds, duration bands, failure modes. [references/transitions.md](references/transitions.md).
7. **Kinetic catalog, caption blocks, storyboard direction** — [references/kinetic-type.md](references/kinetic-type.md), [references/captions.md](references/captions.md), [references/storyboard.md](references/storyboard.md), open board in [examples/storyboard/](examples/storyboard/).
8. **Comparison bar** — Claude’s cut on the same awards brief is the density-and-type bar. Lessons live in [references/client-sizzle.md](references/client-sizzle.md). No paid gen, no new render.

### Still parked

1. **Optional:** synthesize SFX on the beat grid (the public `sfx.mjs` idea) as a first-party helper next to `beats.py`. Do not vendor a course file.
2. **Directed prompt file** — GOAL / TIME / LOOK / MOTION / SHOTS / BANNED / QA. The rules now live in `motion-design.md`. A separate prompt pack is unnecessary unless a job asks.
3. **impeccable-style visual lints** — still the parked design/motion item above. The kinetic scores are a checklist, not a new checker.

### Gallery, post pattern, and skips (2026-10-25)

- **[MotionVideo](https://motionvideo.xyz/)** — bookmark the free gallery (and its public prompts) for showreel density. The site is open source; the skill pack is sold separately. Do not buy it. Do not copy or redistribute pack files.
- **[browser-use/video-use](https://github.com/browser-use/video-use)** — transcript-first EDL, confirm before the cut, filmstrip self-eval. That pattern is a short section in [references/helpers.md](references/helpers.md) for spoken/raw takes. Do not install the repo.
- **[FilmCraft](https://github.com/storytold/filmcraft)** — NLE. Ignore for the generation stack.
- **[CapCut × ChatGPT / Codex](https://www.capcut.com/tools/capcut-x-codex)** — ignore. Not a Reelsmith render path.
- **snapcn Pro letter-morph** — [snapcn text](https://snapcn.dev/docs/text). Do not buy Pro, do not add those components, do not redistribute. House recipes cover the type jobs. Letter-morph is not a default.
- **3D / extrude defaults** — off. Flat vector type is the client default. Liquid chrome stays the parked section below. Glitch (`glitch`, `caption-glitch-rgb`) is not a default.
- **video-use as a sidecar** — pattern only, already in helpers. Do not install the repo.

### Scout indexes (mine later, do not vendor)

- **[guanmo-ai/awesome-ai-motion](https://github.com/guanmo-ai/awesome-ai-motion)**
- **[athemeroy/awesome-claude-5-5-videos](https://github.com/athemeroy/awesome-claude-5-5-videos)** — the “awesome-opus-5-5-videos” URL Movez cites [redirects here](https://github.com/athemeroy/awesome-opus-5-5-videos).
- **[LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)** — one-liners are in `motion-design.md`. Do not vendor the repo.

### Reference only (do not fold as dependencies)

- **[JohnHeibel/PDoomVideo](https://github.com/JohnHeibel/PDoomVideo)** — multi-chapter music-video pattern and `ANIMATION_GUIDE` (skim only).
- Skip: [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase), [buildwithhanif/claude-animation-skill](https://github.com/buildwithhanif/claude-animation-skill), [WinterArc21/Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film) — niche cartoon or long-form, not the Reelsmith template path.

**When:** the parked remainder waits until other release gates are stable, unless the owner asks for a spike sooner.

## Liquid chrome / reflective metal look (optional Three.js path)

**Status:** parked  
**Why:** The owner liked the Florence liquid-chrome demos. Keep best-of-breed recipes available as an optional look beside Remotion and HyperFrames.

**Decision:** Fold useful shaders and helpers **directly** into Reelsmith as an optional look path. Do **not** vendor whole Three.js stacks as sidecars or required dependencies.

### Park / fold-in candidates (OSS and free study)

1. **Paper Design liquid metal** — [shaders.paper.design/liquid-metal](https://shaders.paper.design/liquid-metal) · [paper-design/shaders](https://github.com/paper-design/shaders) (Apache-2.0) · [paper-design/liquid-logo](https://github.com/paper-design/liquid-logo) (PolyForm Shield 1.0.0, not Apache-2.0; study the look, do not copy it in under the shaders license).
2. **Blobmixer (14islands)** — [blobmixer.14islands.com](https://blobmixer.14islands.com) · [connorhvnsen/blob-mixer](https://github.com/connorhvnsen/blob-mixer)
3. **Blob Mixer R3F port** — [lucaperullo.it/components/blob-mixer](https://lucaperullo.it/components/blob-mixer). Recreate the look in [this post](https://x.com/Chimakes3d/status/2106708158840238232).
4. **Metallic Blob** — [metallic-blob.vercel.app](https://metallic-blob.vercel.app) · [nicholaschen09/metallic-blob](https://github.com/nicholaschen09/metallic-blob)
5. **3d-retro chrome metaballs (CC0)** — [3d-retro.com/experiments/metaballs](https://3d-retro.com/experiments/metaballs)
6. **Effect.Labs liquid metal WebGL tutorial** — [liquid-metal shader writeup](https://effect-labs.com/en/pages/blog/liquid-metal-shader-webgl.html)
7. **Xanares Opus chrome Mandelbox** (lab-loop craft) — [post](https://x.com/Xanares/status/2105770390924738984)
8. **Optional:** [radiofun/shaderdoc](https://github.com/radiofun/shaderdoc) (`liquid-metal.html`)

**Study live, do not park as OSS:** Once UI Liquid Metal is Pro source — [once-ui.com/effects](https://once-ui.com/effects).

**Out of scope:** cloning entire Three.js apps as required dependencies, and unpaid or gated component kits as hard dependencies.

**When:** parked until other release gates are stable, unless the owner asks for a spike sooner.
