---
description: Load when joining shots on a client sizzle or custom kinetic piece, after kinetic-type.md. One primary seam plus at most two accents. Name only real HyperFrames blocks or Remotion presentations in the starter kit.
---

# Transitions and polish

How two shots join. Type inside a shot is `kinetic-type.md`. This does not add packages. HyperFrames skills stay on (`HYPERFRAMES_SKIP_SKILLS` stays unset on client work). The feature-explainer kit still uses a half-beat transition (`remotion.md`). Client sizzle and custom kinetic work use the bands below, snapped so the join ends on the beat grid.

Sources: [HyperFrames transitions](https://hyperframes.heygen.com/prompting/transitions), [Remotion TransitionSeries](https://www.remotion.dev/docs/transitioning).

## Rules

1. **One primary, one or two accents.** Most seams share one join. Spend the bold accent on a topic change or the climax. A different transition on every seam reads as noise.
2. **Hard cut when continuity holds.** If a shape, screen, prop, or word carries across, cut. A match cut beats a dissolve. In Remotion that is no `TransitionSeries.Transition`, or `none` from `@remotion/transitions/none`.
3. **The join is one move.** Do not fade the outgoing shot out and then fade the next one in. That dips to empty. Both shots hand off together.
4. **Name a real block.** On HyperFrames, name a block the skill already ships. Do not invent `page-curl` or guess GLSL. The starter kit already depends on `@remotion/transitions@4.0.538`. Do not add `@hyperframes/shader-transitions` or any other package from this doc.
5. **Write the split on the storyboard.** Example: hard cut throughout, one whip into the takeover. End the join on a beat (`b(n)` in `music.md`).
6. **A one-shape morph is a launch accent, not a new primary.** On `product-launch`, one container may change size and radius while its content swaps (`templates.md`). On a client sizzle the primary stays a hard cut. Do not morph display type.

## Duration

| Energy | Length | Feels like |
|---|---|---|
| Calm (wellness, luxury, brand story) | 0.5–0.8 s | Slow, soft |
| Medium (corporate, SaaS, explainer, most client sizzles) | 0.3–0.5 s | Directional |
| High (promo, music, launch sting) | 0.15–0.3 s | Fast |

Say the number. Pin it to the beat.

## Energy → block

HyperFrames names are the skill's blocks (shader when the handoff is the moment, CSS for an ordinary continue). Remotion names are export paths under `@remotion/transitions/` in the starter kit. Import the presentation from that path. Do not import one that is not listed there.

| Energy | HyperFrames shader | HyperFrames CSS | Remotion |
|---|---|---|---|
| Calm | `cross-warp-morph`, `thermal-distortion` | `transitions-blur`, `transitions-dissolve` | `fade`, `dissolve`, `dreamy-zoom` |
| Medium | `whip-pan`, `cinematic-zoom` | `transitions-push`, `transitions-cover` | `slide`, `wipe`, `linear-blur` |
| High | `ridged-burn`, `glitch`, `chromatic-radial-split` | `transitions-scale`, `transitions-light` | `film-burn`, `clock-wipe` |

Special seams, still accents, not a new primary:

| Block | Use |
|---|---|
| `flash-through-white` | One bright frame on an impact beat |
| `sdf-iris` | Iris into a hero. Remotion: `iris` (needs width and height) |
| `light-leak` | One warm seam. Remotion: overlay, not a second transition |
| `beat-freeze-cut` | Hold a frame on the downbeat, then a hard cut. The picture freezes; the bed does not. Not a frozen ending |

`glitch` is not the client default. Name it only when the brief asks for that tone.

## Mood, when the brief names one

Energy sets tempo. Mood picks among the blocks in that row.

| Mood | HyperFrames | Remotion |
|---|---|---|
| Warm / luxury | `light-leak`, `cross-warp-morph`, `transitions-blur` | `dreamy-zoom`, `fade` |
| Editorial | `whip-pan`, `transitions-push` | `slide`, `wipe` |
| Tense | `ridged-burn`, `glitch` | `film-burn` |
| Playful | `ripple-waves`, `swirl-vortex` | `ripple` |

Client sizzle default when the brief is silent: **hard cuts**, medium energy, one `whip-pan` / `slide` accent. Not a unique shader per seam.

## Remotion timing

`TransitionSeries` overlaps the two sequences and **shortens** the total by the transition length. A transition cannot be longer than either neighbor. Two transitions cannot sit next to each other. A transition and an overlay cannot sit next to each other.

```tsx
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={sceneA}>…</TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={slide()}
    timing={linearTiming({ durationInFrames: Math.round(0.4 * fps) })}
  />
  <TransitionSeries.Sequence durationInFrames={sceneB}>…</TransitionSeries.Sequence>
</TransitionSeries>
```

Use `springTiming` only with a clamped config, and only on a seam that is not display type: `springTiming({ config: { damping: 200, overshootClamping: true } })`. A bouncing seam fights the type presets in `kinetic-type.md`. Check `getDurationInFrames({ fps })` so the overlap is not longer than either shot.

`blurSlide` (`@remotion/transitions/blur-slide`) is a whip accent, one per film. Do not blur the type that has to be read on the next frame.

A light leak or flash that should not shorten the timeline is a `TransitionSeries.Overlay`, centered on the cut. It cannot sit next to a `Transition`.

```tsx
import { TransitionSeries } from "@remotion/transitions";

<TransitionSeries.Overlay durationInFrames={Math.round(0.3 * fps)}>
  {/* one leak or flash; not on body copy */}
</TransitionSeries.Overlay>
```

## Failure modes

- Fade the outgoing shot out, then fade the next one in. That is a dip, not a join.
- A different transition on every seam.
- “Add some transitions” with no energy and no primary.
- An invented block name.
- `glitch` or a particle seam as the default on a client sizzle.

## Not a slideshow

Inside a shot, the eight rules in `motion-design.md` apply. Across shots, two more things have to be true or the film is a deck of cards ([HyperFrames motion](https://hyperframes.heygen.com/prompting/motion)):

1. **Something crosses the seam** — a shape, a prop, a word, a frame, or a sound.
2. **Energy varies** — quiet against one hero moment. Uniform motion is as flat as no motion.

| Method | What crosses | Where the emphasis is |
|---|---|---|
| Match cut | Shared shape, color, or motion vector. HyperFrames: `text-match-cut` when the word itself is the join | Break the rhyme once, on the spectacle |
| Hero prop | The product, screen, or chart stays up while the room cuts | Push in on the prop; still the rest |
| Persistent chrome | A HUD or ruler the brief asked for. Not a corner label | Chrome falls away for one beat |
| Audio spine | One sentence or one musical phrase across the cut | A rest before the number lands |
| Beat-locked cut | Cuts on the `beats.py` grid | One card holds through a downbeat |
| Accumulation | Nothing exits; the frame reflows | Older elements drop to idle |

Name the two properties on the storyboard. The device can change. A 6-second stat card may just cut.

## Polish (sparingly)

Not a default. Not on body copy, captions, or UI chrome. One grade for the film, not a new look per shot. These are not new Reelsmith dependencies — do not add them to the starter kit or to HyperFrames setup. On a Remotion job that already has the package, or when the user explicitly asks for finish and you are already in that project:

| Look | Where | Restraint |
|---|---|---|
| Grain / noise | [`noise()`](https://www.remotion.dev/docs/effects/noise) | Low amount, one seed. HyperFrames: a faint tiled overlay, opacity under ~0.08. |
| Soft chromatic fringe | [`chromaticAberration()`](https://www.remotion.dev/docs/effects/chromatic-aberration) | A few pixels, on a whip or a still plate. Never on readable type. |
| Light leak | [`lightLeak()`](https://www.remotion.dev/docs/effects/light-leak) or a `TransitionSeries.Overlay` | One accent seam. Drive `progress` from the frame. An overlay does not shorten the timeline. |
| Soft vignette | [`vignette()`](https://www.remotion.dev/docs/effects/vignette) | Edges only. HyperFrames: a soft radial gradient over the plate, not over the type. |
| Motion blur | [Remotion motion blur](https://www.remotion.dev/docs/motion-blur) | Whips and fast camera moves only. |

Glow, bloom, and particle bursts stay on the banned list in `motion-design.md`. Polish does not excuse a thin select or a fade-card title.
