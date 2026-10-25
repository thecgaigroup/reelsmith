---
description: Load after client-sizzle.md for ambient idle, bans, camera words, and the one spectacle. Recipe ids and timing live in kinetic-type.md. Seams live in transitions.md.
---

# Motion design rules

Distilled from the HyperFrames motion guide, classic animation principles, and platform best practices.
The templates already follow these rules. Custom work starts here. Client sizzle and showreel kinetic type add the stricter section below.

1. **Nothing fully stops.** Every hold has slow drift (scale 1.00 -> 1.03, background parallax). A frozen last
   second reads as a bug; end on motion or a deliberate logo settle.
2. **The camera is an actor.** Push in to focus attention (screenshots: zoom 1.4-2.0x onto the target), pull out to
   reveal. One move per idea, eased (`power2.inOut`/`power3.out`).
3. **Overlap.** Stagger entrances (60-90 ms per word or item); the next element starts before the last one lands.
4. **Overshoot, then settle.** Templates may use a small `back.out(1.4)` on short labels and numbers; not on body text. Client sizzle and big kinetic type do not overshoot display words or logo lockups — see Showreel kinetic type.
5. **Depth.** Foreground type, a mid-ground card, a soft blurred background. A short blur on an exit is a transition. Readable type stays sharp (no filter or `will-change` on glyphs the camera scales).
6. **Pace by genre.**
   | Genre | Seconds per idea | Cut on |
   |---|---|---|
   | Sizzle / teaser | 1.5-3 | every beat or bar |
   | Promo / launch | 2-4 | bars |
   | Explainer / how-to | 4-8 (VO-led) | sentences |
   | Kiosk loop / slides | 5-8 | slide change |
7. **Hook in the first 1-3 s:** motion + the strongest words. Logo and CTA last, held at least 2 s.
8. **Readability:** about 0.3 s per word plus 1 s; 2-6 words per kinetic card; one idea per screen.
9. **Consistency:** one ease family, one transition style per piece, from `brand.motion.energy`
   (low = fades/slides, medium = slides + scale, high = whip, blur, slam).
10. **Vertical:** larger type (about 1.3x), centered, inside the safe area (keep clear of the top 13% and bottom
    32% in Reels/TikTok UI); captions above the UI band; never put key content behind the like/comment rail.
11. **Beat sync:** cut on downbeats, hit accents on the beat; transitions are half a beat long. Music starts at its
    first downbeat (`beats.py grid`).
12. **Flash-safe:** no more than 3 flashes per second; animate scale, blur and opacity instead of luminance flips.
13. **Engine rules:** animate only transforms and opacity (GPU-cheap, deterministic); seekable timelines only (no
    random values, timers or CSS animations).

Parameterized templates keep rules 1–13. Client sizzle and hand-authored kinetic pieces follow the stricter section below. Do not retrofit a template to this section unless the job asks for a showreel-grade type pass.

## Showreel kinetic type

Production-house density for awards, partner, and client sizzles, and for custom kinetic pieces. Named recipes: `kinetic-type.md`. Seams: `transitions.md`. Operational checklist: `client-sizzle.md`. Gate: `brand-qa.md`. The quality bar on an awards sizzle is dense real footage plus this type — see the comparison bar in `client-sizzle.md`. We are not there until the contact-sheet scores say so.

Public sources, rewritten here: [Movez — motion studio with Opus 5.5](https://x.com/0xMovez/status/2104216919033192746) and the free [MotionVideo gallery](https://motionvideo.xyz/) (browse public prompts only). Do not buy, copy, or redistribute the MotionVideo paid skill pack. Render stays HyperFrames or Remotion. There is no third `seek(t)` browser pipeline in this repo.

### Time is the only input
Every frame is a pure function of time. Seeking to `t` twice paints the same pixels.
- **HyperFrames:** one `gsap.timeline({paused:true})` on `window.__timelines["main"]`. No CSS transitions, `setTimeout`, `requestAnimationFrame`, or `Math.random()` in the composition. `fromTo` with explicit end states so a cold seek is correct (`hyperframes.md`).
- **Remotion:** `useCurrentFrame()` plus `interpolate` / `spring`. CSS animations do not render (`remotion.md`).
- When a note says `seek(t)`, map it onto that paused timeline or that frame number. Do not add a Playwright frame-dump renderer.

### Weight (closed-form springs)
A fixed ease from A to B feels cheap. Showreel motion has mass: it accelerates and settles. Overshoot is a hair on UI, and none on big type.
- **UI chrome** (buttons, cursors, tab indicators, small labels): underdamped spring, barely visible overshoot. GSAP: `back.out(1.15)` at most. Remotion: `spring({ frame, fps, config: { damping: 14, mass: 0.7, stiffness: 160 } })`.
- **Display type, logo lockups, big numbers:** no overshoot. GSAP: `power3.out` or `expo.out`. Remotion: `spring({ frame, fps, config: { damping: 200, mass: 1, stiffness: 80, overshootClamping: true } })`. Named presets (snappy headline, elegant editorial, heavy logo): `kinetic-type.md`.
- Stiffer reads snappy (UI). Heavier reads expensive (type, lockups). Do not put a playful bounce on words.
- A value that changes target more than once (cursor x, container width) is the sum of one spring per change, each starting at its own time. Frame N must not depend on having simulated frames 0..N−1.

Paste into a HyperFrames composition when a single ease cannot retarget. Do not add a package.

```js
// 0 at t<=0, settles at 1. UI: spring01(t, 180, 22). Display type: spring01(t, 64, 16) (critical, no overshoot).
function spring01(t, stiffness, damping) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(stiffness);
  const z = damping / (2 * w0);
  if (z < 1) {
    const wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
  }
  return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
}
// Retarget: start + sum of (next - prev) * spring01(t - tChange, stiffness, damping)
```

### Faces, accent, pace
Timing, stagger, and recipe ids are in `kinetic-type.md`. Do not restate them in the prompt.
- One display face (`brand.fonts.heading`), one UI face (`brand.fonts.body`; `mono` only for code or figures), one accent (`colors.accent`, else `colors.primary`).
- Lock static type before motion: display line-height ~1.05–1.15, tracking from the brand font (typically −1% to −3%).
- Accent color only on the speech-locked or beat-locked word. The rest of the line stays high-contrast `fg` on `bg`.
- Hits and cuts land on the `beats.py` grid. Music is the supplied track, a credited bed, or `beats.py synth`. Do not block the job on synthesized SFX. Loudness stays about −14 LUFS, at most −1 dBTP.

### Banned defaults
Fail the shot on a client or custom kinetic piece:
- Centered title on a gradient (vertical safe-zone placement from rule 10 is fine; the ban is the gradient title card)
- Everything fading in
- Corner labels, timecode bugs, or frame borders the brief did not ask for
- Glow, bloom, or gradient fills on UI chrome
- Generic particle bursts
- Blurry scaled text (`will-change`, CSS filters, or a raster scale on the glyphs; push in on a real screenshot instead of scaling the type)
- Invented product UI

A template may still fall back to a branded gradient when media is missing (`templates.md`). That fallback is not a client-sizzle shot.

### Product and UI films
Use real screenshots, the real logo, and the brand colors. Crop and move the real interface. List the assets before animating. Never redraw buttons, dashboards, or marks from imagination. Paid image or video generation does not fill a missing UI (`ai-generation.md`).

### Which renderer
| Prefer | When |
|---|---|
| **HyperFrames + GSAP** | Client sizzle default: custom kinetic, overlays, logo grids, page-like comps. Skills on. |
| **Remotion** | Speech-locked kinetic type, a series, or a data-driven plan in the shipped kit. Word timings and `spring()`. |
| **Neither a raw browser `seek(t)` loop** | Reelsmith does not ship a third renderer. |

### Critique before the full render
Before a delivery render, and before a client draft leaves the box:
1. Draft or stills at each beat. HyperFrames: `$HF snapshot --at …`. Remotion: `npx remotion still` at those frames. Then `review.py check` so `contact.jpg` and `phone.jpg` exist.
2. Look at the sheets. Automatic checks do not judge type.
3. Score 1–10: **hook** (first 2 s), **phone** (readable on `phone.jpg`), **motion** (weight, no dead frames), **variety** (a new event every 2–4 s), **brand** (real logo, colors, type; none of the banned defaults), **sound** (on the beat grid).
4. Fix the three worst scores. Repeat until each is 8 or higher, then render full quality.
5. Hunt overlaps during swaps, slides with no ease, blurry type, and a pop at a loop seam.

`review.py` prints this table into `review.md`. It does not change pass/fail. The generic 1–5 rubric in that file stays for every job.

## Premium motion (HyperFrames eight)

Source: [HyperFrames motion](https://hyperframes.heygen.com/prompting/motion). Rules 1–3 and 7 already sit in the numbered list above (idle, camera, overlap, pace). These are the ones that change a client cut:

1. **Ambient idle.** A hold is not a freeze. Write “settles into a 1–2% breathing scale or a slow drift.” A frozen last second fails review. The one named breather (`storyboard.md`) stays quieter than the rest; it still does not end as identical frames.
2. **Camera.** One move per shot (push, pan, parallax). It does not decay to a dead stop at the cut. Words: [vocabulary](https://hyperframes.heygen.com/prompting/vocabulary) — slow push-in is 4–8% scale, whip is a fast slide into the next frame, parallax is layers at different rates.
3. **Overlap.** The next element starts while the last is still settling. Offset shorter than the move. Delay supports, never the focal.
4. **One claim per move.** Combine properties only when they say the same thing (rise + fade = arriving). Do not also rotate, scale, and blur that same object.
5. **Overshoot on transforms only.** A physical flap or a small UI control may pass its target. A number, a display word, and a logo lockup do not. Follow-through (shadow, housing) lands a frame later.
6. **Depth.** Far plane slower, subject at full rate, one foreground element faster and allowed to cross in front. A second blurred ornament is clutter.
7. **Genre pace.** Showreel ideas land in about 1.5–4 s. Hard cuts, not a dissolve between every idea (`transitions.md`).
8. **Handmade stays seeded.** Paper, curtain, or a stepped hold uses one seed at the start (mulberry32 or a fixed frame index). `Math.random()` is banned. Glitch is not a default.

## Density contract and one spectacle

From the shared preamble on [HyperFrames examples](https://hyperframes.heygen.com/prompting/examples). State it once on a client sizzle, then name **one** spectacle beat. An unnamed burst gets dropped.

- One focal element at display scale. Supports enter on their own cues.
- Chrome only when the brief asks. Corner labels and frame borders stay banned.
- Entrances overlap. Overshoot stays on transforms, not on type or figures.
- End on ambient idle, not a frozen frame.
- **Spectacle:** one exaggerated moment, written on the storyboard (which shot, what happens, when it settles). Everything else stays restrained. On this lane the spectacle is a real select or a real number, not confetti and not a generated burst.

## Easing and camera words

Say the word; use the ease. Source: [vocabulary](https://hyperframes.heygen.com/prompting/vocabulary). Display type still does not use bouncy or springy.

| Say | GSAP | Use on |
|---|---|---|
| smooth | `power2.out` | UI, ordinary continues |
| snappy | `power4.out` | Short headlines (`snappy-headline`) |
| dramatic | `expo.out` | A reveal that should arrive fast and glide |
| dreamy | `sine.inOut` | Calm camera only |
| bouncy / springy | `back.out` / `elastic.out` | Small UI only. Not display type, not numbers |

iart reveal curve, when you need a cubic-bezier instead of a named GSAP ease: `cubic-bezier(0.16, 1, 0.3, 1)`. Timing shorthand: fast ~0.2 s, medium ~0.4 s, slow ~0.6 s.

| Camera word | Build |
|---|---|
| slow push-in | 4–8% scale, gentle ease, through the hold |
| pull back | scale down as the next element enters |
| pan across | translate the scene layer |
| whip to | fast slide into the next frame; blur only the whip, not the type |
| parallax | two or three layers, different rates |
| crane | vertical drift |

Drone orbit, extruded type, and glitch are not the client default.

## Choreography one-liners

From [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill). Do not vendor that repo.

- Name the emotional intent before the ease.
- Each move is setup → action → resolution.
- One primary action, a secondary support, ambient idle under both.
- Travel stays inside about a third of the frame.
- One hero. At most two or three things active at once.

## Gallery themes (style only)

Browse the free [MotionVideo gallery](https://motionvideo.xyz/) for density, not for files. Useful public themes: Bold kinetic type, Kinetic type music machine, Pencil line, Beat-synced generative, Photo print launch, Claude motion designer showreel. Do not buy or paste the paid pack. A photo-print or product launch still uses real screenshots and the real logo.
