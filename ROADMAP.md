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

1. **Optional code:** a first-party SFX helper next to `beats.py`. The cue-sheet pattern (same `b(n)` as the picture, −14 LUFS, kick/impact ideas) is already in [references/music.md](references/music.md). The 2026-10-27 earshot fold did not start this helper: sync taps and the role bank are docs. Generated hits stay the stdlib sketches. Do not vendor a course file or a sound bank, and do not add that helper until a job needs generated hits the bed cannot cover.
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

## Motion-video-kit craft (2026-10-26)

**Status:** in the skill. Docs only. No package, no npm, no key, no Three.js runtime, no sidecar skill tree.

**Source:** [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) (MIT, Copyright (c) 2026 echris6), read at `e4b1c0004080`. Adapted into house voice. The upstream tree is not vendored.

| Folded into | From | What landed |
|---|---|---|
| [references/brand-qa.md](references/brand-qa.md), [references/review-and-qa.md](references/review-and-qa.md) | `gauntlet.md`, `critic-prompts.md` | Independent-critic loop on the existing fresh reviewer: builder ≠ judge, item-by-item FIXED / PARTLY / STILL PRESENT, a ledger, house prompts. Stills and `review.py` stay the artifacts. |
| [references/motion-design.md](references/motion-design.md), [references/storyboard.md](references/storyboard.md) | `motion-grammar.md` | Six rules and net-new mechanisms. House timing, overshoot, idle, and the 2 s end card stay. A links-only pointer to upstream `launch-film-notes.md`. No footage. |
| [references/remotion.md](references/remotion.md) | `product-hero-realism.md`, `three-js-patterns.md` | Optional product-hero notes: seekable `pose(t)`, realism checklist, one measured unfold as a study example. Not a dependency, and not a third renderer. |

Client sizzle and HyperFrames skills-on rules are unchanged. `mask-reveal-up` stays the line default. `poster-grid` stays optional. The SageCut ladder stays optional and off. Do not require `SAGE_API_KEY`. Do not install SageCut.

**Parked from the same kit:**

- **`business-offers.md`** — verticals, price anchors, and the pilot-offer template. Do not quote them. Re-verify any commercial offer with the buyer. Honesty rules already in the skill (labelled concepts, no invented testimonials) cover the part that overlaps.
- Sample commercials (`case-study-alder.md`, `case-study-duo.md`, `case-study-home-display.md`) and their footage. Not copied.
- Upstream scripts (frozen-time, loudness, contact sheet, SFX mix) and `templates/component-lab.html`. House `review.py` and `export.py loudnorm` stay the measurements.

Liquid-chrome shaders below stay parked. These notes do not start that work.

## Scout dig (2026-10-27)

**Status:** in the skill. Docs only. No package, no npm, no key, no sound bank, no new skill tree.

**Sources:** [LexnLin — earshot v0.4](https://x.com/LexnLin/status/2113393065427620076), [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) (MIT). [francescoinweb3 — six-file harness](https://x.com/francescoinweb3/status/2114428225103261971), with the [five-step chain](https://x.com/francescoinweb3/status/2111190424647782538) and the [five mistakes](https://x.com/francescoinweb3/status/2111918374301155804). Principles rewritten in house voice. Upstream trees are not vendored.

| Folded into | What landed |
|---|---|
| [references/music.md](references/music.md), [references/templates.md](references/templates.md), [references/review-and-qa.md](references/review-and-qa.md), [references/loudness-accessibility.md](references/loudness-accessibility.md) | Launch SFX: `offset_ms` sync taps, `bed_db` levels, a role bank on the cue sheet, timeline / sheet / critique checks on house artifacts. Shapes stay stdlib and ffmpeg. |
| [references/hyperframes.md](references/hyperframes.md), [references/remotion.md](references/remotion.md), [references/storyboard.md](references/storyboard.md), [references/scriptwriting.md](references/scriptwriting.md), [references/client-sizzle.md](references/client-sizzle.md) | Six stations mapped onto house files: reference on the direction block, sourced data, story before motion, the existing comp, a one-line timing fix, stills, then the user's yes. |

**Left upstream:** the earshot sound bank, `skills/earshot`, `skills/real-sound`, forge recipes, and the MCP server. An optional local CPU MCP is future work, out of scope for this fold, and not a Reelsmith dependency. No paid audio model. Francesco's Remotion-and-motion-design skill pack is not a second tree here. HyperFrames stays the sizzle engine. Skills stay on. The SageCut ladder and the motion-video-kit fold are unchanged.

## Video Decompiler craft (2026-11-15)

**Status:** in the skill. Docs only. No vendored code, tools, or text.

**Source:** [JimGHTB12/video-decompiler](https://github.com/JimGHTB12/video-decompiler) (MIT, James Dimachkie), commit 57a7525.

| Folded into | What landed |
|---|---|
| [references/storyboard.md](references/storyboard.md) | Take-apart dossier: structured reference breakdown (seen / measured / take) covering spine, world, formal idea, hand-overs, weak spots, keeps/breaks. Take shape and pace only, never the reference's subject, words, pictures, or music. |
| [references/transitions.md](references/transitions.md) | Five kinds of boundaries: becomes / carried / matched / door / change of ground. "Next" is not a reason. |
| [references/motion-design.md](references/motion-design.md) | Measure a reference move: fit its speed curve as cubic-bezier by plotting frame-by-frame travel. The rebuild must match the curve, not just the look. |
| [references/review-and-qa.md](references/review-and-qa.md), [scripts/review.py](scripts/review.py) | One-frame pop scan: flag frames whose change is far larger than neighbors' (swap, reset, flash). Implemented with behavioral test. |

**Skipped on purpose:**

- **video-decompiler and raea as an engine:** FSL 1.1 license. It competes with Remotion and HyperFrames, which are already Reelsmith's render paths.
- **woodxbt 19-repo listicle:** It's an index. Items already covered in other ROADMAP sections or parked. Hairline is a web widget, not a render path.

## Three-source harvest: cuts, cut QA, edit memory, story-short camera (2026-11-17)

**Status:** in the skill. One new review check with tests; the rest is docs. No vendored code.

**Sources:** [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) `skills/reverse-any-video` and `measure cuts` (Apache-2.0) @d317abc · [browser-use/video-use](https://github.com/browser-use/video-use) (MIT) @43cfc56 · [mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) (MIT) @e3b817b.

| Folded into | What landed |
|---|---|
| `scripts/review.py`, `scripts/test_cut_detection.py` | `cuts.json` cut list (cut / flash / fast / transition) and a WARN for clicks at cuts. |
| `references/review-and-qa.md` | Cut list and clicks; self-eval at every cut with a three-pass cap; `EDIT_LOG.md` session memory. |
| `references/storyboard.md` | Dossier "Measured": cuts per minute from `cuts.json`, consecutive frames at events, one-topic look reports in numbers. |
| `references/motion-design.md` | Story-short camera numbers; switch-versus-tween; ink-sized type; blur, trail, sweep and flash recipes. |
| `references/helpers.md`, `references/captions.md` | Filler and pause cut numbers; captions on a cut film. |
| `SKILL.md`, `references/music.md` | Read the edit log first; lock picture timing before the cue sheet. |

**Skipped on purpose:**

- **reverse-any-video as a tool:** HyperFrames Pro only (HeyGen sign-in, credits, usage beacon); it re-shoots people with HeyGen and regenerates painted shots with paid video generation. Its free measuring ideas are folded above.
- **video-use as a tool:** its transcription needs `ELEVENLABS_API_KEY` (Scribe). The free path stays `$HF transcribe -e parakeet` or WhisperX. Already "pattern only" in `helpers.md`.
- **Claude Animated Shorts reference frames and sheets:** another channel's frames, "for style study only". Not copied.

### Parked: storybook 3D story-short look (optional three.js path)

A Remotion + `@remotion/three` + `postprocessing` world (ink outline pass before lens blur, painted Canvas2D textures, billboard 2D characters, synthesized march score and SFX). MIT, free, offline. Not folded: it adds three.js packages that `remotion.md` keeps out, needs Kenney CC0 models (~1.3 GB `public/`), and a short is a multi-day hand-built project (2K renders about 4 fps). Revisit when a CGAI series wants a recurring character world; start from its `templates/bridge/` in a separate project, never in this repo.

## Motion list harvest: springs by feel, motion audit, exploded reveal (2026-11-18)

**Status:** in the skill. One new script command with tests; the rest is docs. No vendored code, no new package, no paid generation, no new keys.

**Source list:** [@HeLi8866's 20 motion repos](https://x.com/HeLi8866/status/2122773874706452604).

| Repo | Commit | License | Folded into |
|---|---|---|---|
| [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) | 2e1f3c0 | MIT | Phase shares inside one move, ambient layers, symptom table, signature curves (`motion-design.md`); motion findings by severity (`brand-qa.md`) |
| [motiondivision/ai-kit](https://github.com/motiondivision/ai-kit) | 1e42494 | MIT (package and README; no LICENSE file) | Springs by feel (`motion-design.md`); audit shape for `review.py audit` (`review-and-qa.md`) |
| [annnguyentt/anatomy-reveal-skill](https://github.com/annnguyentt/anatomy-reveal-skill) on [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) | dd01e1c · 1482e84 | MIT · MIT | Exploded reveal shot (`templates.md`); speed-based whip blur (`transitions.md`) |
| [pmndrs/react-postprocessing](https://github.com/pmndrs/react-postprocessing), [fand/vfx-js](https://github.com/fand/vfx-js), [Alchemist0823/three.quarks](https://github.com/Alchemist0823/three.quarks) | e07ef9a · 1d9bb68 · 9d0445c | MIT | Polish recipes rebuilt in CSS, GSAP or `ffmpeg` (`transitions.md`) |

**librosa:** already covered. `beats.py grid` uses librosa's onset envelope, beat tracker and tempo, plus a low-band onset envelope for the downbeat phase and RMS sections. It does not export discrete onset times (off-beat accents); that is a possible follow-up, not part of this fold.

**Skipped on purpose:**

- **ai-kit's audit method, MCP servers and paid tier:** the scoring method is served by a sign-in server and is part of a paid plan. Not read, not rebuilt. Its Motion-library and web-UI rules (hover, layout animations, reduced motion) do not apply to rendered video.
- **LottieFiles emotion and color tables, web accessibility rows, Lottie export notes:** UI-specific, or already in `helpers.md`.
- **The anatomy kit, renderer, interactive figure page and worked example:** a separate Puppeteer and ImageMagick toolchain, and a third renderer. The shot rhythm is kept; the build stays in HyperFrames or Remotion.
- **theatre-js/theatre** (Apache-2.0 core, AGPL-3.0 studio): a keyframe editor. Our paused GSAP timeline and Remotion frames already cover seekable keyframes. Nothing new.
- **lucasmarkes/hairline** (MIT): pointer-driven web figures; no render path (also noted in the Video Decompiler section). Nothing new.
- **AudioCraft:** generated music is against the house music rule, and its weights are non-commercial.
- **blender-agents:** needs a local Blender and paid 3D.
- **HyperFrames, Remotion, Remotion Skills, three.js, GSAP, Manim, WhisperX, FFmpeg:** already covered. Nothing new.

## Animation list harvest: shot ledger, beat lock, generic tells (2026-11-17)

**Status:** in the skill. One new script command with tests; the rest is docs. No vendored code.

**Source list:** [@0xnicc0's 20 free animation repos](https://x.com/0xnicc0/status/2122668685324128570).

| Repo | Commit | License | Folded into |
|---|---|---|---|
| [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video) + [videomd/videomd](https://github.com/videomd/videomd) | bb11b13 · 0837221 | Apache-2.0 | Shot ledger (`storyboard.md`); `beats.py lock` (`music.md`) |
| [heydamir/unslop](https://github.com/heydamir/unslop) | 620163e | CC BY 4.0 | Generic-AI tells (`brand-qa.md`) |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | d41d986 | Apache-2.0 | Generic-AI tells (`brand-qa.md`) |
| [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | 00a7f9e | MIT code; CC BY-NC 4.0 docs | Reading time per text block (`review-and-qa.md`), from MIT code only |
| [patch-gg/pixelfx](https://github.com/patch-gg/pixelfx) | 5294518 | MIT | Acted effects (`motion-design.md`) |

**For KREW music visualizers (notes, not in the KREW skill):** a Suno-Visuals-style piece breaks down well in a shot ledger: lyric type is packaging, the waveform or color field is a code shot, any filmed or AI insert is its own unit, and `beats.py lock` says whether the cuts ride the beat. Rebuild code shots in HyperFrames; filmed or AI inserts stay `NEED` until paid generation is approved.

**Skipped on purpose:**

- **rea-video as a tool:** its VLM checks and remake runs need model API keys (`REA_VLM_*`, Gemini or Doubao) and paid generation (capsule-cinema). Its case reports break down other people's videos (TikTok ads, a rap MV) and quote their lyrics; not copied. No conforming VIDEO.md package is produced.
- **awesome-opus5-5-videos:** MIT on the repo, but its 703 prompts are reverse-engineered from other creators' viral AI videos; rights unclear. Not used.
- **lemo-opuscar docs and the 99 styles:** every Markdown file and the image prompts are CC BY-NC 4.0. The extra permission covers making our own films, not folding the docs into a shared skill. Some films redraw third-party interfaces and Anthropic's Clawd. Only the MIT reading-time idea is taken.
- **PixelFX catalog and font:** 244 effects stay out; the Patch Pixel font is not MIT. Effects publishing needs Patch Desktop.
- **EffectCraft:** a full desktop compositor (MIT or Apache-2.0; ArtCraft marks excluded). A third render path; nothing to fold.
- **unslop and impeccable as skills, their detectors, and UI-only rules** (RTL, browser states, hover, focus): installs and web-only checks.
- **Blender MCP:** MIT, but it drives a local Blender install, has telemetry, and its AI 3D generators are a paid premium tier or need keys. Parked with the three.js path.
- **ComfyUI:** GPL-3.0 and a generative stack; paid generation is on hold.
- **anime.js, Lottie, Manim, HyperFrames, Remotion, Remotion Skills, Anthropic Skills, three.js, GSAP, FFmpeg, WhisperX:** already covered (`helpers.md`, `hyperframes.md`, `remotion.md`) or an engine we do not need. Nothing new found.

## OpenMotion harvest: look file, launch story shapes (2026-11-17)

**Status:** in the skill. Docs only. No vendored code, files, or catalog entries.

**Source:** [nexu-io/openmotion](https://github.com/nexu-io/openmotion) (Apache-2.0) @664be5086141b09fe08b2638e43a8728c3a615b7. Shared by Tom Huang ([@tuturetom](https://x.com/tuturetom/status/2122633782654370068)).

| Folded into | What landed |
|---|---|
| `references/motion-design.md` | `LOOK.md`: keep, swap with measured capacity, timing, materials, check; evidence status; series variety rule. |
| `references/templates.md` | Launch story shapes (proof, detail, rhythm), the verify hold, direction cards. |
| `references/storyboard.md` | Optional Check line per shot; spectacle as four moments. |
| `references/brand-qa.md` | Type complaint triage. |

**Skipped on purpose:**

- **OpenMotion as a tool** (Studio, MCP server, CLI, npm app, editor fork): it would be a third render pipeline beside HyperFrames and Remotion.
- **Model gateway and multimodal generation** (GPT Image, Seedance, Suno, Eleven via BYOK or the OpenDesign Go subscription): needs new API keys or a paid plan. Paid generation stays on hold.
- **The 287-entry motion catalog ("300+ Motion.md")**: breakdowns of other companies' brand films. Their footage, brands, screenshots and fonts keep their original rights, and many guides are Chinese prose tied to OpenMotion's demo player. Ideas only, nothing copied.
- **The 152 brand design systems and Brand Kit catalog**: adapted from nexu-io/open-design; many are named after real companies (Airbnb, Apple, BMW and others). Trademarks and brand look-alikes; not copied. Our brand intake stays `brand.json`.
- **Bundled Product Promo, NYT Graph, Decision Tree templates**: HeyGen HyperFrames registry examples we can already reach through HyperFrames. Not copied.
- **Motion Package v0.2 manifest** (`motion-package.json`, hashed inventory, materializer): packaging for sharing, which we do not need. Revisit only if CGAI starts publishing looks for others.
- **Design-remix profiles and vendored three.js / GSAP builds**: three.js stays out (`remotion.md`); GSAP comes from HyperFrames.
- **Presenter-story edit map** (source time versus output time): already covered by captions on a cut film (`captions.md`) and the cut list (`review-and-qa.md`).

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
