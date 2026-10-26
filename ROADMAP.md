# Reelsmith roadmap

Parked work. Do not start these until the current release gates elsewhere are stable, unless the owner asks for a spike.

## Client sizzle is storyboard-first (2026-10-24)

**Status:** in the skill

Awards, partner, and client sizzles now require a storyboard before the edit — `storyboard.json` plus HTML (proportional timeline, brief-beat alignment, shot cards, HAVE/ID/NEED/TEMP) — and a brand QA gate before anything leaves the box. See [references/storyboard.md](references/storyboard.md), [references/client-sizzle.md](references/client-sizzle.md), and [references/brand-qa.md](references/brand-qa.md). The generic pattern (no client media) is in [examples/storyboard/](examples/storyboard/). Showreel kinetic type for that lane is in [references/motion-design.md](references/motion-design.md) (2026-10-25). Taste numbers, the cue sheet, house launch recipes, and the BRIEF / fresh-reviewer gate are in the skill as of the same day (section below).

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

1. **Optional code:** a first-party SFX helper next to `beats.py`. The cue-sheet pattern (same `b(n)` as the picture, −14 LUFS, kick/impact ideas) is already in [references/music.md](references/music.md). Do not vendor a course file, and do not add that helper until a job needs generated hits the bed cannot cover.
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
- **[LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)** — timing, easing, and choreography numbers are in `motion-design.md`. Do not vendor the repo.

### Reference only (do not fold as dependencies)

- **[JohnHeibel/PDoomVideo](https://github.com/JohnHeibel/PDoomVideo)** — multi-chapter music-video pattern and `ANIMATION_GUIDE` (skim only).
- Skip: [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase), [buildwithhanif/claude-animation-skill](https://github.com/buildwithhanif/claude-animation-skill), [WinterArc21/Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film) — niche cartoon or long-form, not the Reelsmith template path.

**When:** the parked remainder waits until other release gates are stable, unless the owner asks for a spike sooner.

## Taste, sound, harness, launch recipes (2026-10-25)

**Status:** in the skill. Docs plus the HyperFrames pin and the vendored lottie-web player. No sidecar, no Playwright studio, no vendored skill tree.

| Folded into | From | What landed |
|---|---|---|
| [references/motion-design.md](references/motion-design.md) | [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill), [dylantarre/animation-principles](https://github.com/dylantarre/animation-principles) | Duration bases, directional easing, stagger budgets, selected Disney-12 micros. Display type stays at 0% overshoot. |
| [references/music.md](references/music.md) | [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion), [Sunwood-ai-labs/hyperframes-motion-reel-skill](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill) | Cue sheet on the picture clock, `b(n)`, stdlib kick/impact ideas, −14 LUFS. No `sfx` package. |
| [references/templates.md](references/templates.md) | [AbubakrChan/product-launch-motion](https://github.com/AbubakrChan/product-launch-motion), [kaventro/motion-designer](https://github.com/kaventro/motion-designer) | House launch recipes: device-framed real UI, cursor as a function of time, one-shape morph as a launch accent, bar-accurate cuts. |
| [references/storyboard.md](references/storyboard.md), [references/brand-qa.md](references/brand-qa.md), [references/review-and-qa.md](references/review-and-qa.md) | Asteri and rewind02 craft rules, applied without fetching posts | Frame-numbered BRIEF, stills before playback, fresh reviewer, worst three, scores to 8+, `seek(t)`. |
| [references/client-sizzle.md](references/client-sizzle.md) | same | One brand per session (lock / worst-three / campaign). Skills stay on. |
| [references/remotion.md](references/remotion.md) | beamnxw-style campaign matrix, light | Two hooks × three formats as props after the master locks. |
| [references/brand-kit.md](references/brand-kit.md) | [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) brand-intake | Feeling and one never, stored on `brand.json`. No `MOTION.md`. |

**Pinned:** HyperFrames `0.8.188` → `0.8.197` (lint and check pass on `hyperframes-example/` and `lottie-example/`). Remotion `4.0.538` and GSAP `3.15.0` were already the latest stable and were left there. Vendored lottie-web `5.12.2` → `5.13.0` (check and snapshot still pass). No Remotion lockfile change.

**Skipped on purpose:** CapCut, FilmCraft, paid MotionVideo packs, Manim/3b1b as a new path, influencer-growth packs, [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) (an index; the verify loop and vertical safe zone are already house rules), Playwright subframe rendering, `HYPERFRAMES_SKIP_SKILLS` on client work.

## Optional / parked (2026-10-26)

**Status:** documented. Neither item is the default. No package, no key, no version bump. Distinct from the taste, sound, and harness pack above.

- **SageCut brand QA (optional, parked spend).** Principles and a measurement recipe in [references/brand-qa.md](references/brand-qa.md), with short pointers in [references/remotion.md](references/remotion.md) and [references/review-and-qa.md](references/review-and-qa.md). Ladder: local frame measurements (OCR/pixel: text size, blank frames, frozen frames, brand colors, delivery spec) → Sage triage when a key is present → Opus critics only on flagged frames. `gate --no-sage` is the upstream local switch (zero API). The house default for client sizzle and live footage stays the BRIEF plus `review.py`. SageCut 0.3 does not support camera footage. Sage API and Opus critics stay **HOLD** until Marc lifts paid-gen spend. Do not require `SAGE_API_KEY`. Do not install the plugin or vendor the skill tree. Sources: [levantolabs/sagecut-release](https://github.com/levantolabs/sagecut-release) (MIT), [Shann³](https://x.com/shannholmberg/status/2114396613468910070).
- **`poster-grid` (optional recipe, in the skill).** One grid recipe in [references/kinetic-type.md](references/kinetic-type.md), beside the even end-card row, the logo grid, and template `endcard()`. `mask-reveal-up` stays the default for body and headline lines. Look reference, not installed: [Typographic poster grid](https://21st.dev/@21st/components/lp-ex-poster-grid).

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
