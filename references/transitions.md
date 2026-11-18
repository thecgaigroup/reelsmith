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

## Five kinds of boundaries

Every change of scene must be one of these. "Next" is not a reason. Name the boundary type on your storyboard.

| Kind | What it is | Example |
|---|---|---|
| **becomes** | The thing turns into the next thing | A typed line grows into a card; a word morphs into its meaning |
| **carried** | Something stays through the change: a shape, a person, the camera's own move | A logo persists while the background cuts; a push-in continues across the seam |
| **matched** | A cut with the subject in the same place, size, or motion vector | Two shots of a phone, centered, at the same scale |
| **door** | A visible threshold into another ground | Through a screen, into a card, entering an interface |
| **change of ground** | The whole frame changes color, texture, or world on the music | A beat hits and the scene shifts to a new visual environment |

The word can become the thing it names. Put the next thing where the eye already is. When something carries across or a match holds, cut — the picture stays continuous and needs no dissolve.

*Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525)*

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

### Polish recipes (numbers, no new package)

The same restraint, as numbers you can build in HyperFrames (CSS, SVG and GSAP on the paused timeline), in Remotion, or as one `ffmpeg` pass on the export. Pixel sizes are written at 1080 high; scale by `height / 1080`. Every random value comes from one seed and the frame index. Each one is named on the storyboard, or it is not in the film.

| Finish | Build | Numbers |
|---|---|---|
| Chromatic fringe | Red and blue copies of a plate, shifted opposite ways, or `rgbashift=rh=-2:bh=2` | About 0.1% of the width horizontally (2 px at 1920), half that vertically. On a whip or a still plate, ramped on and off over 3–4 frames |
| Glitch (only when the brief asks for the tone) | 3–6 horizontal bands copied with `clip-path` and shifted sideways, plus a short fringe | Bursts of 2–4 frames, at least 1.5 s apart, offsets 8–40 px. No brightness flip, so the flash rule (≤3 per second) holds. Never on a line the viewer must read |
| Rack focus | CSS `blur()` on the far plate and the near plate, crossed | Far plate 0 → 10–16 px over 12–18 frames while the near plate clears. Never on glyphs; type sits on its own sharp layer. If blur is costly, crossfade three or four pre-blurred copies |
| Trail behind a moving subject | Draw the subject's closed-form position at `t`, `t − 1/fps`, … | 6–10 ghosts, opacity `(1 − i/N)²`, scale 1 → 0.6. One trail on the one subject that moves (a cursor path, the product on a whip). Not a particle burst |
| Whip motion blur | Average sub-frames inside each output frame | Sub-frames per frame = `ceil(fastest on-screen px moved per frame / 4)`, capped at 24 (`remotion.md`); 1 when nothing moves fast. A fixed small count shows separate copies on a whip. Off an engine render at N× the frame rate: `tmix=frames=N,select='not(mod(n\,N))',setpts=N/<fps>/TB` |
| Grain | `noise()` in Remotion, or at export: `noise=alls=6:allf=t:all_seed=7` | Off by default (it bloats the file and smears after platform re-encode). The fixed seed gives the same grain on every re-export. Check the export size before and after |
| Vignette | Radial gradient over the plate, or `vignette=angle=PI/5` | Edges only, under the type layer |
| Practical-light bloom | Footage only: keep the brightest pixels, blur, screen them back. `split[b][h];[h]lutyuv=y='if(gte(val,230),val,16)':u=128:v=128,gblur=sigma=20[g];[b][g]blend=all_mode=screen:all_opacity=0.35` | Only on real lamps, screens or sun in the footage, at 0.3–0.4. Never on type, logos or UI chrome (the ban stands) |

The `ffmpeg` lines above were run on a synthetic 1080p clip for this page; they need no build beyond the `ffmpeg` already required. Run `review.py check` after any finishing pass: grain and glitch can trip the flash and pop checks.

*Source: technique survey of pmndrs/react-postprocessing (MIT, @e07ef9a; effect parameters in `docs/effects/`), fand/vfx-js (MIT, @1d9bb68; its effect list), Alchemist0823/three.quarks (MIT, @9d0445c; ribbon trails), and the speed-based shutter in annnguyentt/anatomy-reveal-skill (MIT, @dd01e1c, `references/shots.md`). None of those packages is used; every recipe above is a CSS, GSAP or `ffmpeg` rebuild in our words.*
