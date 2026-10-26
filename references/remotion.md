---
description: Load for feature-explainer, for a client sizzle whose type locks to speech, or for a campaign matrix after the master locks. Not the default sizzle engine. useCurrentFrame and spring only. Typewriter is string slicing. Optional product-hero notes do not add Three.js.
---

# Remotion (narrated explainers)

Use the shipped kit: `remotion-starter-kit.tgz` (complete project; brand-driven theme, layout units, captions,
lower thirds, transitions, free/paid VO script, caption export). Fastest path: `templates/feature-explainer/render.sh`.

**License:** free for individuals, teams of up to 3, non-profits and evaluation. Companies of 4+ need a company
license (remotion.pro/license). If use is commercial and the headcount is unknown, ask once and save the answer.
Otherwise, use HyperFrames (Apache-2.0).

## Setup
1. `node -v`: 20.19+ or 22.13+.
2. `mkdir -p /workspace/remotion-video && tar xzf remotion-starter-kit.tgz -C /workspace/remotion-video && cd $_ && npm i`.
3. `npx remotion browser ensure`. If Chrome fails, `ldd` its `chrome-headless-shell` and apt-install missing libraries.
Without the kit: `npx create-video@latest --yes --blank`, then `npx remotion add @remotion/transitions @remotion/media
@remotion/google-fonts @remotion/media-utils` and `npm i -D tsx @types/node`.

## Workflow
1. `python3 scripts/brand.py bundle brand.json --out public` and set `brandFile` in the plan.
2. Write `src/plans/<slug>.ts` (scene kinds: hook, feature, stat, quote, logo/CTA; 1-3 sentence `vo` each).
3. `npx tsx scripts/generate-voiceover.ts src/plans/<slug>.ts --dry-run`, then run it without `--dry-run`. The provider
   is auto: free Kokoro/espeak unless a paid provider is named and allowed.
4. `npx tsc --noEmit && npx remotion compositions` (never `remotion studio`).
5. Stills: `npx remotion still <id> out/f.png --frame=N --scale=0.5`. Final: `npx remotion render <id>
   out/<slug>-16x9.mp4 --codec=h264 --crf=18` (draft: `--scale=0.5 --crf=28`).
6. **Remotion doesn't normalize loudness:** `python3 scripts/export.py loudnorm in.mp4 out.mp4` on every final.
7. Captions: `npx tsx scripts/export-captions.ts <slug>` -> words.json -> `captions.py build`.

## Kinetic type
Prefer Remotion when type locks to speech, or the job is a series / data-driven plan in this kit. The frame number **is** `seek(t)`: `useCurrentFrame()` plus `interpolate` / `spring` only.
- Display type and logo lockups: `spring({ frame, fps, config: { damping: 200, mass: 1, stiffness: 80, overshootClamping: true } })`. Presets: `kinetic-type.md`. Seams: `transitions.md` (the half-beat rule below still governs feature-explainer templates).
- UI chrome: `spring({ frame, fps, config: { damping: 14, mass: 0.7, stiffness: 160 } })` — a hair of overshoot, not a bounce on the words.
- A value with several targets is the sum of one spring per change from its own start frame. Do not store velocity in a ref.
- One display face, one UI face, one accent, from the brand bundle. Mask or clip; do not fade the whole card in. Real screenshots and logos only.
- A typewriter is `text.slice(0, n)` from the frame. Never per-character opacity (`kinetic-type.md`).
- Stills at each beat (`npx remotion still`) before the full render, then the same contact-sheet scores as HyperFrames (`motion-design.md`). Client sizzle that is a designed page, not a word-locked explainer, stays on HyperFrames.
- Body and headline lines stay `mask-reveal-up` unless the storyboard names another house recipe. `poster-grid` is one optional grid (`kinetic-type.md`).

## Optional frame ladder (demo)

A Remotion motion-graphics review can follow the SageCut ladder in `brand-qa.md` after the stills and `review.py`: local OCR and pixel checks first (`gate --no-sage`, zero API), Sage triage only with a key, Opus critics only on flagged frames. That is the cost cut versus sending every frame to a critic. Sage API and Opus critic spend stay **HOLD** with the rest of paid-gen spend. Do not require `SAGE_API_KEY`. SageCut 0.3 does not support camera footage. The house gate is still the BRIEF and `brand-qa.md`. Do not install the plugin.

## Campaign cuts (two hooks × three formats)

After the master scores 8 or higher (`brand-qa.md`), extra cuts are props on one composition. Do not rebuild the film per aspect.

```tsx
type CampaignProps = {
  hook: "a" | "b";
  format: "16x9" | "9x16" | "1x1";
};
```

`calculateMetadata` sets width, height, and duration from `format`. The two hooks are copy and the first shot, not two designs. On a Remotion master, render the six cells from those props. A HyperFrames master stays one composition: change aspect with the project resolution, and swap the hook in the copy. Skills stay on. Do not start a third renderer. Real UI stays the same screens (`templates.md`). This is tier C in `client-sizzle.md`.

`seek` is the frame index. The same frame twice is the same pixels. CSS animations do not render.

## Rules
- All motion from `useCurrentFrame()` + `interpolate`/`spring`; CSS animations don't render.
- Beat = `fps*60/bpm` frames; transition = half a beat; Sequence = scene frames + outgoing transition.
- Measure VO in `calculateMetadata` (`computeDuration()`); never hard-code durations.
- Music: `loop`, fade in 0.5 s / out 1.5 s, duck to ~35% under VO.
- OOM: `--concurrency=2`, then `--disallow-parallel-encoding`. Transition TS errors: cast to
  `TransitionPresentation<Record<string, unknown>>`. Video shorter than audio: a transition was counted twice.

## Optional: product-hero realism

A code-built device, only when the storyboard names a physical product. No Three.js package, no `npm` add, no SageCut, no `SAGE_API_KEY`. Client sizzle stays real selects plus kinetic type on HyperFrames, skills on. If this beat is Remotion, `useCurrentFrame()` is the clock. If it sits inside a HyperFrames comp, the paused timeline calls the same pose, and skills stay on. The canvas is not a third renderer.

Adapted from [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) `references/product-hero-realism.md` and `references/three-js-patterns.md` (MIT, Copyright (c) 2026 echris6; read at `e4b1c0004080`). Their component lab, overlay module, and sample films are not in this repo. Study a brand film locally. It never enters the export, and it is not redistributed from here.

Use a dimensional scene when it explains something physical. Type, reports, and forms stay crisp HTML or SVG on the house engines. Flat vector type remains the client default (`ROADMAP.md`).

### Pose contract

Every transform comes from time. No `requestAnimationFrame` loop, no timer, no physics history, no `Math.random()`.

```js
function pose(t) { /* set every transform from t only */ }
function render(t) { pose(t); renderer.render(scene, camera); }
function anchors(t) { pose(t); return points.map(project); } // screen pixels for HTML labels
```

Load textures and font weights before the first frame. Retime with `(t - start) * speed`. A shared `pose` on both sides of a cut keeps the handoff pixel-matched. Seek the same `t` twice, including backwards.

### Realism checklist

- **Layers.** Build the object in its own axes. Separate real parts (courses, deck, housing). Lift along the normal with smootherstep, `x*x*x*(x*(x*6-15)+10)`, and a few milliseconds of stagger. A cubic ease-out that starts at full speed pops one frame. After the lift, keep a slow separation so the hold is not frozen. Scale breathing on type and logos stays the house 1–2%.
- **Callouts.** `anchors(t)` every frame. Labels sit in an even column with leaders. Equal gaps matter more than pinning each label to its anchor. The label matches its photo.
- **Pinned photos.** Real photos, opaque cards, a shadow that fades on the handoff. Cards land on the next scene's pixel rectangles. Pin the side that faces the camera.
- **Option patches.** One piece airborne at a time. Each option has a distinct end state. Moving parts stay inside the card.
- **Mark.** If a dimensional mark assembles, the same artwork moves into the end-card lockup so the identity survives.
- **Camera.** Pitch about 35–55°, a minimum distance, no roll. A near top-down on a large texture tiles. Pull back rather than ending tight on a slab. Lock the camera during the hero move. Recenter the object. Move a reframe to after the landing.
- **Light.** A soft key from the side you want lit, shadows readable on lifted layers, a warm or cool rim. Keep at least about 60% of the glass reflections through a fold. Dimming them to hide a flash also hides the angle. Kill a one-frame glint by widening the source so the highlight builds over about 6 frames. On a black stage, a broad soft source at the mirror of the camera gives the cover an edge.
- **Color.** Tone mapping shifts the brand field. Measure the rendered pixel and compensate until it matches `brand.json`. Fog uses that same color. Author the stage color to the value that survives encode (one studied stage written as `#f5f5f7` decoded near `#f3f5f5`). Measure through the encoded file. A lossless still can disagree with the MP4 and tell you nothing about the materials.
- **Model, or photo.** A maquette (cream, real material textures, a base) reads as designed. Fake photoreal fails when gutters float, glass is flat black, a ridge is an open notch, or flashing looks like a plinth. Add the cap, the reflection, and the flush piece.
- **Contact.** After a close, hold still. The studied close was pixel-identical for about 17 frames. A camera jolt reads as fake. A rebound, if the storyboard wants one, stays under about a third of a degree.

### Match a real move

Measure the brand's own film. Tile it and the render at the same frame rate and compare. Estimate angle from the projected width of the moving part and write keys (seconds after the start → degrees). Interpolate with a monotone cubic and flat end slopes (Fritsch–Carlson). Plot degrees per frame: one peak, then a dwell near edge-on, then a soft land. Blending those keys with a smoothstep afterwards moves the dwell and adds a mid-swing hiccup.

One measured unfold, a foldable phone, study only, not a house preset: 0→180° in about 0.8 s, fastest through the middle. Keys: `0→0, .08→20, .15→58, .23→82, .31→98, .39→116, .49→140, .59→159, .69→172, .80→180`.

Screens are half the realism:

- Before the move, the outer display shows home, via a staged unlock: the lock lifts and fades, then home scales in from about 1.06. A crossfade doubled a clock and counted as a text collision.
- During the move, the outer display blurs and stays lit, and sleeps near edge-on. Sleeping at the lift left a black hole on a black stage.
- The inner display's continuing half is a crop of the same texture as the outer display, so the layout matches by construction.
- The newly revealed half keeps a sharp wallpaper under a white frost veil (about 0.3). New widgets arrive as frosted cards (about 40 px blur, 0.6 opacity, 0.97 scale) and resolve over about 0.35 s after the landing. Blur the cards. Leave the wallpaper sharp. A handful of pre-rendered blur levels, crossfaded, keeps the frame a function of `t`.

Motion blur, if the storyboard asks for it, is deterministic accumulation: N sub-frames inside the shutter, averaged, every frame a function of `t`. In the studied fold, 10 sub-frames left a comb on a fast edge; 24 across the fastest half-second cleared it. A 180° shutter looked too crisp; about 300° through the fast swing, easing back to 180°, matched the footage. Ramp the shutter on over about 6 frames so it does not switch in one frame. Cover every fast fold, not only the hero.

### Seek traps on a device comp

These showed up on a real HyperFrames device film. They apply whenever a canvas or DOM type shares the house clock:

- Freeze `devicePixelRatio` at load. Reading it per frame flickered line weights inside a high-resolution capture. If you supersample, use one fixed ratio for the whole film (the studied pass used 1.5×) and size depth of field to the drawing buffer.
- Headless Chrome draws `-apple-system` as Times. Bind `@font-face` to a font file you are allowed to ship, beside the CSS. Do not redistribute a system font.
- A WebGL canvas inside HyperFrames captured reliably with fast capture off (`--experimental-fast-capture=false` on that render). Skills stay on. This flag does not install a package.
- `will-change` broke seek determinism. Leave it off (already the type rule).
- DOM type under a slow scale re-rasterises in visible steps. For a device line that must rise with the camera, draw the line once to a bitmap and reveal words with a clip. Keep a transparent DOM line if you still need layout checks. Client-sizzle display type stays `mask-reveal-up` in the comp. This bitmap path is for the device beat only.
- Preload every font weight before mounting overlays. A line measured inside `display: none` is 0 px wide and then overlaps. Lay segments out while you measure, then hide them.
- Register the render-ready promise before the first capture, or frame 0 is blank.
- One NaN blacks one frame. Scan the contact sheet for a single near-black frame.
- A hard threshold on a continuous value flashes for one frame when the sample lands on the wrong side of the cut. Crossfade the change.
- A whole-frame pop flag can be the move you wanted (a screen blooming, a full stroke). Read the frame-to-frame difference across about five frames on either side. A ramp is motion. A lone spike is a bug.
- Open on a finished frame by remapping the shot clock (`t → t0 + rate·t`). Rebuilding the scene is the long way. Frame 0 of the film is still a finished composition (`motion-design.md`).

Prove the beat with stills, and a few seconds of motion, before it enters the film (`brand-qa.md`). Do not add the upstream component lab.
