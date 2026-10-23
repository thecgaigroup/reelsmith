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

## Rules
- All motion from `useCurrentFrame()` + `interpolate`/`spring`; CSS animations don't render.
- Beat = `fps*60/bpm` frames; transition = half a beat; Sequence = scene frames + outgoing transition.
- Measure VO in `calculateMetadata` (`computeDuration()`); never hard-code durations.
- Music: `loop`, fade in 0.5 s / out 1.5 s, duck to ~35% under VO.
- OOM: `--concurrency=2`, then `--disallow-parallel-encoding`. Transition TS errors: cast to
  `TransitionPresentation<Record<string, unknown>>`. Video shorter than audio: a transition was counted twice.
