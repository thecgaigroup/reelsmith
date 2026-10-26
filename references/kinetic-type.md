---
description: Load on a client sizzle or custom kinetic piece, after client-sizzle.md. House recipe ids are implemented in GSAP or Remotion. They are not HyperFrames registry block names.
---

# Kinetic type recipes

Implement these in the composition. Do not install animate-text, iart-ai, or a MotionVideo pack. HyperFrames skills stay on.

## Which id goes where

| Id | Pass it to |
|---|---|
| `mask-reveal-up`, `per-character-rise`, `kinetic-center-build`, `spring-scale-in`, `typewriter`, `typewriter-collapse-spring`, `stagger-from-center`, `stagger-from-edges`, `soft-blur-in`, `bottom-up-letters`, `top-down-letters`, `focus-blur-resolve`, `shared-axis-y`, `short-slide-right`, `short-slide-down` | Your GSAP timeline or Remotion `spring` / `interpolate`. **Not** a `/hyperframes` registry block. |
| `poster-grid` | Optional grid recipe below. GSAP or Remotion. Not a line reveal, and not a registry block. |
| `snappy-headline`, `elegant-editorial`, `heavy-logo` | The spring preset table below. Remotion: fields inside `config`, including `overshootClamping`. |
| `text-match-cut`, `match-cut`, `svg-mask-reveal`, `lt-mask-reveal`, `kinetic-type-swap`, `paper-collage-reveal`, `curtain-reveal` | `/hyperframes` only if that block is in the loaded skill catalog. |
| `whip-pan`, `slide`, `caption-editorial-emphasis`, `caption-clip-wipe`, `caption-kinetic-slam`, `caption-highlight` | Real seam and caption blocks. See `transitions.md` and `captions.md`. |

If a house id is not in the table's HyperFrames row, describe the move in the prompt. Do not invent a block name.

Sources: [Movez](https://x.com/0xMovez/status/2104216919033192746), the free [MotionVideo gallery](https://motionvideo.xyz/), public animate-text ids, and public HyperFrames / iart-ai reveal patterns.

## Client default

Mask or clip, staggered by **line** (a read) or **word** (a tagline). Character splits only for a one- or two-word hit.

- Line stagger 60–100 ms. Word stagger 40–70 ms. Character stagger 20–40 ms. Cap a reveal near 800 ms. The cascade stays under 500 ms unless the recipe is `kinetic-center-build`. Duration bases, exits at 65–75% of the entrance, and anticipation (UI only) are the taste layer in `motion-design.md`. Do not put anticipation on `mask-reveal-up`.
- Ease: `power3.out`, `expo.out`, or `cubic-bezier(0.16, 1, 0.3, 1)`. No overshoot on the words.
- Preview-only CSS (not the render): `animation-delay: calc(var(--i) * 40ms)`. The render uses a GSAP or Remotion stagger of that same 40 ms. CSS animations do not seek.
- Something new every 2–4 s (a new line, a cut, or a UI state). A card that only fades in fails.
- One display face, one UI face, one accent (`motion-design.md`).

`mask-reveal-up` is the default for body and headline lines. Reach for the other recipes on purpose, not once per shot.

## Spring presets

`overshootClamping` sits **inside** `config`. Display type never bounces. UI chrome is a separate, smaller spring (`motion-design.md`), not one of these.

| Preset | Use | GSAP | Remotion `config` |
|---|---|---|---|
| `snappy-headline` | Short display words, a hook hit | `expo.out`, ~0.40 s | `{ damping: 200, stiffness: 180, mass: 0.55, overshootClamping: true }` |
| `elegant-editorial` | Line and word masks, the default | `power3.out`, ~0.70 s | `{ damping: 200, stiffness: 80, mass: 1, overshootClamping: true }` |
| `heavy-logo` | Logo lockup, end mark | `power3.out`, ~0.95 s | `{ damping: 220, stiffness: 60, mass: 1.4, overshootClamping: true }` |

Remotion shape: `spring({ frame: frame - start, fps, config })`. A value with several targets is the sum of one spring per change from its own start. Do not store velocity in a ref.

## Recipes

All of these are a pure function of timeline time or frame. Wrapper clips (`overflow: hidden`); do not animate a CSS transition. No `will-change` on glyphs the camera scales.

### `mask-reveal-up` (default)

Per line. Outer box clips. Inner line moves from `y: 110%` to `y: 0` with `elegant-editorial`. Opacity stays 1 inside the mask so the move is a reveal, not a fade. Next line starts 60–100 ms later. Exit, if needed, is a shorter mask up (`y: -110%`), not a blur.

### `per-character-rise`

One or two words only. Each glyph `y: 100%` → `0` inside its own clip, stagger ~30 ms, `snappy-headline` or `elegant-editorial`. No blur. Do not use this on a sentence.

### `stagger-from-center`

Short hit. Delay each glyph by how far it sits from the middle index (center first, edges last), same rise or mask as `per-character-rise`. One shot per film at most.

### `kinetic-center-build`

Tagline, word by word. The first word sits at center. Each next word enters from the right (`x`, opacity) and the whole line re-centers. Hold the previous words sharp — no blur stack, no scale-up on the glyphs. Stagger is sequential (~200–400 ms per word), still inside a 2–4 s payoff. `elegant-editorial`.

### `spring-scale-in`

A number, a short lockup, or a single word. Scale `0.92` → `1` with `snappy-headline` or `heavy-logo`, opacity with it. Not a bounce. Not a paragraph. Not a blurred zoom.

### `typewriter` and `typewriter-collapse-spring`

Hook or end sting only. Not the default card.

**Remotion types by slicing the string.** `text.slice(0, n)` from the frame. Never per-character opacity (a row of faint glyphs is not a caret). HyperFrames does the same: show a prefix, hide the rest, caret at the end. Stepped, no interpolation.

1. On a solid brand field, a caret types the line (about 20–40 ms per character). The line is done inside ~2 s.
2. Optional in-place word swap: hard cut the last word, do not fade it.
3. The line collapses to center (`scaleX` → 0, ~0.25 s) and clears.
4. The real mark settles with `heavy-logo`, then the wordmark unmasks beside it.

Use the real logo file. Do not draw a mark, and do not add a glow on the lockup. If this recipe runs long, the type-finish and the mark-settle are the two payoffs — do not let the caret blink on an empty hold. `typewriter` alone is steps 1–2. The collapse and the mark are `typewriter-collapse-spring`.

### More house names

Public animate-text ids, rewritten. Not a package. Blur recipes resolve to sharp type before the hold; they are not the client default (`mask-reveal-up` is).

| Id | Move | Limit |
|---|---|---|
| `soft-blur-in` | Glyphs rise a few pixels and a tiny blur clears to 0 | One headline. Not body copy |
| `bottom-up-letters` | Characters rise from below, 20–40 ms | One or two words |
| `top-down-letters` | Characters drop from above, same stagger | One or two words |
| `focus-blur-resolve` | The whole lockup starts soft and is sharp by the hold | A single word. Then it stays sharp |
| `shared-axis-y` | Words hard-cut on a shared vertical axis, stepped, no fade | A swap, not an entrance |
| `stagger-from-edges` | Outer glyphs first, center last | Short hit, once per film |
| `short-slide-right` | The line slides in; words appear by opacity in order | Tagline. No scale-up |
| `short-slide-down` | Words drop into a centered stack of at most three lines | Tagline |

### HyperFrames blocks (only these names)

Use a block only when the loaded `/hyperframes` catalog lists it. Otherwise implement the house recipe.

- `text-match-cut` or `match-cut` — the shared word or shape is the seam.
- `svg-mask-reveal`, `lt-mask-reveal` — a mask reveal the catalog already ships. The default line reveal is still the house recipe `mask-reveal-up` if those blocks are the wrong layout.
- `kinetic-type-swap` — a word swap. Not `kinetic-center-build` (that one you build).
- `paper-collage-reveal`, `curtain-reveal` — one handmade reveal, seeded. Not the default entrance.
- Transcript captions — `$HF transcribe`, then one caption block for the section (`captions.md`).

### Scene arc

A kinetic card, and the film around it, runs **Hook → Build → Punch → Resolve**.

- Hook: the first words, inside 3 s.
- Build: the line or the picture fills.
- Punch: one or two `emphasis_words` (accent color, or a marker). Not every word.
- Resolve: settle, idle, or the end mark.

Primitives, pick only what the recipe needs: split (line / word / character), mask, stagger, spring, caret, collapse, emphasis word, type match-cut, marker.

### Markers

One accent on a payoff word, not a scribble on the sentence. HyperFrames modes: `highlight` (sweep), `circle` (one word), `burst` (the spectacle only). `scribble` and `sketchout` only when the brief is a strike-through. Remotion: a rough-notation underline on the payoff word, drawn from the frame, seeded, not random. Source: [vocabulary — marker highlights](https://hyperframes.heygen.com/prompting/vocabulary).

## Pick one

| Shot | Recipe | Preset |
|---|---|---|
| Headline lines, most cards | `mask-reveal-up` | `elegant-editorial` |
| Two-word hit | `per-character-rise` or `stagger-from-center` | `snappy-headline` |
| Tagline that builds | `kinetic-center-build` | `elegant-editorial` |
| Stat or single word | `spring-scale-in` | `snappy-headline` |
| Hook or end mark | `typewriter-collapse-spring` | `heavy-logo` on the mark |
| Typographic poster, only when the storyboard names it | `poster-grid` | `elegant-editorial` on the cells |

Name the recipe on the storyboard shot (`storyboard.md`). The open example is `examples/storyboard/`.

## Grid recipes

Line recipes above stay as they are. `mask-reveal-up` stays the default for body and headline lines.

| Treatment | Where it lives | When |
|---|---|---|
| Even end-card row | `brand-qa.md`, `client-sizzle.md` | Default partner and logo lockup. Even optical size, equal gaps, one row or one simple grid. Real marks. |
| Logo grid | HyperFrames page (`hyperframes.md`, `motion-design.md`) | A field of real marks inside a sizzle. Same optical-size rule. |
| Template end card | `endcard()` in `templates.md` | Default template ending: logo, kicker, CTA, URL. |
| `poster-grid` | This section | Optional. Only when the storyboard names it. |

### `poster-grid` (optional)

One grid recipe among the rows above. A typographic poster: words and short items sit on a grid and move to introduce one idea. About 6 s. 16:9, 9:16, and 1:1. Colors and faces come from the brand (one display face, one UI face, one accent). Items are the real words or the real marks.

Build it in GSAP or Remotion as a function of time. Cells may mask-reveal with `elegant-editorial` (0% overshoot). The card is not the default line reveal. Partner end cards stay the even row. Template endings stay `endcard()`.

Do not install a registry block. Look reference: [Typographic poster grid](https://21st.dev/@21st/components/lp-ex-poster-grid) (listed MIT). That install asks for a 21st API key. Reelsmith does not take the dependency.

## Still banned

Centered title on a gradient, fade-in as the whole idea, corner labels and frame borders, glow on UI chrome, particle bursts, blurry scaled text, invented UI. Do not extrude type. Do not use a paid letter-morph component.

## Before the full render

Score hook / phone / motion / variety / brand / sound as a fresh reviewer, from stills (`brand-qa.md`). Variety means a new event every 2–4 s. If the sheet is fade cards and one still per beat, it is not done. Cues for those hits are `b(n)` in `music.md`.
