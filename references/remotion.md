---
description: Load for feature-explainer, for a client sizzle whose type locks to speech, or for a campaign matrix after the master locks. Not the default sizzle engine. useCurrentFrame and spring only. Typewriter is string slicing.
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
