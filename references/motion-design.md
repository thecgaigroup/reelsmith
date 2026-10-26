---
description: Load after client-sizzle.md for taste numbers (timing, easing, choreography), motion grammar, ambient idle, bans, camera words, and the one spectacle. Recipe ids live in kinetic-type.md. Seams live in transitions.md. Cues live in music.md.
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
Use real screenshots, the real logo, and the brand colors. Crop and move the real interface. List the assets before animating. Never redraw buttons, dashboards, or marks from imagination. Paid image or video generation does not fill a missing UI (`ai-generation.md`). A product beat sits in a device frame and cuts on `b(n)` (`templates.md` house launch recipes). Cues share that clock (`music.md`).

A physical device, drawn in code, is optional and only when the storyboard names it. Notes for that beat (seekable pose, screens, light) are in `remotion.md`. They do not add a Three.js package, and they do not add a third renderer. Client sizzle stays real selects plus kinetic type, HyperFrames skills on.

### Which renderer
| Prefer | When |
|---|---|
| **HyperFrames + GSAP** | Client sizzle default: custom kinetic, overlays, logo grids, page-like comps. Skills on. |
| **Remotion** | Speech-locked kinetic type, a series, or a data-driven plan in the shipped kit. Word timings and `spring()`. |
| **Neither a raw browser `seek(t)` loop** | Reelsmith does not ship a third renderer. |

A logo grid is a field of real marks at even optical size. `poster-grid` is a separate optional type grid in `kinetic-type.md`. Body and headline lines stay `mask-reveal-up`.

### Critique before the full render
Before a delivery render, and before a client draft leaves the box:
1. Draft or stills at each beat. HyperFrames: `$HF snapshot --at …`. Remotion: `npx remotion still` at those frames. Then `review.py check` so `contact.jpg` and `phone.jpg` exist.
2. Look at the sheets. Automatic checks do not judge type.
3. Score 1–10 as a fresh reviewer, from the stills: **hook** (first 2 s; frame 0 is already a finished composition), **phone** (readable on `phone.jpg`), **motion** (weight, no dead frames), **variety** (a new event every 2–4 s), **brand** (real logo, colors, type; none of the banned defaults), **sound** (on the beat grid, `music.md`).
4. Fix the three worst scores. Repeat until each is 8 or higher, then render full quality. The author of the comp does not grade it. A later pass marks each prior finding FIXED, PARTLY, or STILL PRESENT (`brand-qa.md`).
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

## Taste layer

Numbers an agent can apply. Sources are cited under Scout notes. Do not install those repos. House springs in `kinetic-type.md` still win on display type, logos, and numbers: **0% overshoot**. UI chrome may use the small spring already in Showreel kinetic type (`back.out(1.15)` at most). Squash, elastic, and bounce are not a client-sizzle entrance.

Name the feeling before the ease (`brand.motion.energy`, or `voice.tone` from `brand-kit.md`). Map energy to a base duration, then scale:

| Energy | Base | Quick (×0.5) | Slow (×1.5) | Dramatic (×2) |
|---|---|---|---|---|
| Low (premium, calm) | 500 ms | 250 ms | 750 ms | 1000 ms |
| Medium (most client sizzles) | 300 ms | 150 ms | 450 ms | 600 ms |
| High (launch sting) | 180 ms | 90 ms | 270 ms | 360 ms |

Element caps, then multiply by distance (50 px ×0.8, 100 px ×1.0, 200 px ×1.3, 300 px ×1.5, full frame ×1.8–2.0). A type reveal still caps near 800 ms (`kinetic-type.md`). Exit duration is 65–75% of the entrance. Entrance eases out. Exit eases in. A move that stays on screen eases in-out. Ambient loops use `sine.inOut`. Linear is for rotation, progress, and timers, not for position.

| Element | Duration | Ease |
|---|---|---|
| Cursor press, toggle | 80–180 ms | snappy UI; tiny overshoot allowed |
| Icon, chip, badge | 150–250 ms | `power2.out` |
| Card | 200–350 ms | `power2.out` / `power3.out` |
| Panel | 300–400 ms | `power3.out` |
| Display line, default | ~700 ms | `elegant-editorial` |
| Short hook word | ~400 ms | `snappy-headline` |
| Logo lockup | ~950 ms | `heavy-logo` |
| Ambient idle | 2–8 s | 1–2% breathing scale |

At 24 fps, quick is 4–6 frames, standard 8–12, deliberate 16–24. At 30 fps multiply those frame counts by 1.25. At 60 fps multiply by 2.5. A hit-stop on an impact is 1–2 frames, then motion returns. The hold after a result is part of the timing, not a bug, as long as the frame is not frozen (ambient idle).

Stagger, same ease family, vary only the start: characters 20–40 ms, lines 60–100 ms, a dramatic cascade 100–200 ms. The whole cascade stays under 500 ms, except `kinetic-center-build`, which is sequential on purpose. Exits stagger in reverse. A shared trigger starts its elements within 50 ms of each other.

### Disney micro principles (selected)

Apply these. Skip the rest of any upstream skill tree.

| Principle | Apply | Do not |
|---|---|---|
| Squash and stretch | UI chrome only. Impact 2–4 frames, recovery 4–8. Keep volume (wider means shorter). | Display words, logos, premium holds |
| Anticipation | 100–200 ms, 10–20% of the main move, opposite direction, on a panel or cursor | Moves under 150 ms, and mask reveals of type |
| Staging | One hero. Supports sit at 40–60% opacity and enter 100–200 ms earlier | Blur on glyphs. A second focal |
| Pose to pose | `fromTo` or `spring` from time. Every frame is seekable | Simulating frame 0..N to reach N |
| Follow-through | Child or shadow 50–150 ms behind the parent. Housing lands a frame later | A second ease on the word itself |
| Slow in / slow out | Table above | Linear slides |
| Arcs | Objects and camera: about 5 px of perpendicular offset when energy is low, up to 20 px when energy is high | Glyph paths. `mask-reveal-up` stays on axis |
| Secondary action | 30–50% of the primary amplitude, 50–100 ms later, a different ease (shadow, plate) | A particle burst |
| Timing contrast | A fast hit reads fast because the shot before it was slower. One hold per idea | Uniform duration on every element |
| Exaggeration | The one named spectacle. Premium type stays at 0% | Confetti, glow, a bounce on the lockup |
| Solid drawing | One light direction. Scale and position agree | `will-change` or a filter on scaled type |
| Appeal | Varied timing, no abrupt stop, idle under the hold | Jerky cuts inside a shot, a frozen last second |

### Choreography

Each shot is setup (20–30% of its length), action (30–40%), resolution (30–40%). Inside the shot, leave 100–200 ms of settled read before the next idea. A beat-locked cut can be the punctuation. Do not add a fade to make that gap.

- One hero. Supports are quieter in distance and ease.
- Elements share an origin. Mixed entry directions read as noise.
- Counter-motion: the background shifts against the hero at 20–30% of the hero's travel.
- Depth speed: foreground 1.0, mid 0.5, background 0.2.
- Travel past about a third of the frame gets an intermediate key or an arc.
- With three or more moving elements, at most a third of them are in transit at once.
- Overshoot budget, after the house rule: premium and display type 0%. UI success 5–10% and still inside `back.out(1.15)`. Celebration overshoot belongs only on the named spectacle.

## Motion grammar

Six rules and a mechanism catalog, adapted from [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) `business-motion-film/references/motion-grammar.md` (MIT, Copyright (c) 2026 echris6; read at `e4b1c0004080`). That file distills 28 SaaS launch films. Timing, stagger, overshoot, idle, and the end-card hold stay the house numbers above (sizzle ideas about 1.5–4 s, end card at least 2 s, idle 1–2%). This section names grammar and moves those numbers did not.

These are storyboard ideas. They are not new recipe ids, not HyperFrames registry blocks, and not a second seam language. `transitions.md` still names the real blocks. One primary seam, at most two accents. HyperFrames skills stay on.

### Six rules

1. **The foreground is the transition.** A headline, logo, or shape scales through the camera while the next scene is already underneath. The join has no empty gap (`transitions.md`: both shots hand off together). The traveling shape may streak. Readable type that remains does not take a CSS filter.
2. **One persistent actor.** A selected photo, cursor, card, rail, or measured shape keeps its identity across shots. A run of unrelated reveals reads as a slideshow, however clean each reveal is.
3. **Density is hierarchy.** One primary move keeps going. Supports stagger around it, with a little tertiary detail (an edge sweep, a status tick), overlapping. At most a third of the moving elements are in transit at once (choreography, above).
4. **Change speed.** A readable hold, a fast exit, a slowing arrival. Durations and eases are the taste table above. Linear stays on rotation, progress, and timers.
5. **A hard cut can be the smooth join.** When subject, scale, direction, and material continue, cut. Motion continues after the cut. Client sizzle keeps a hard cut as the primary seam.
6. **Cause, then effect.** A scan produces findings, a prompt produces an artifact, a button produces a state. The result is true, or it is labelled as a concept. Invented product UI stays banned.

### Composition

- On a feature beat the lead subject fills most of the usable frame. The studied proportion is about 60–85%. Platform safe zones still win (`platform-specs.md`), especially the top 13% and bottom 32% on a vertical cut.
- Vary the setup across the film: physical macro, wide space, plan view, UI close-up, typographic hit. Repeating "heading over three cards" wastes the catalog below.
- Hand an object across a seam at the same pixel. Pre-position the destination so the carried object lands on it.
- Through a run of similar shots, keep one wipe direction and one title position. The outgoing title leaves before the wipe. The incoming title enters after it.
- Frame 0 is a finished composition. A reading hold still breathes (ambient idle). The end card stays readable for at least 2 s.

A 30 s product film in the studied set used about 12–15 compositions inside the house pace. A client sizzle still fills its six beats with real selects. Extra compositions sit inside those beats.

### Mechanism catalog

Write the one you need onto the storyboard. Build it in GSAP on the paused timeline, or with `useCurrentFrame` when the job is Remotion. Do not add a package.

| Mechanism | What it does | Studied in |
|---|---|---|
| Foreground fly-through | The claim or logo scales past the camera and reveals a scene that is already in place | Contra, Wonder, Bolt |
| Logo-as-portal | The brand shape grows until its opening is the next frame | Bolt |
| Selection → expansion | A selected frame expands into the workspace of the next beat | Wonder, AsideHQ |
| Materializing result | A shell appears, then its regions fill in order, then the completed state holds | Replit |
| Persistent rails | A path survives a text swap and connects two states | Replit |
| Continuous canvas | The camera travels one layout. The selected item stays sharp. Neighbours may blur. Glyphs that the camera scales stay sharp | Replit |
| Artifact ring | Small artifacts orbit one stable sentence | Taste |
| Card stack / fan | Screens arrive and occlude, or one card becomes a fan, or a fan resolves to one | Bevel, Tembo |
| Perspective fold | A panel folds to a strip. The next panel rises out of it | AgentArcade |
| Exploded layers | A physical product separates into real layers, then recombines. Optional, and only when the storyboard names a physical beat (`remotion.md`) | Work Louder |
| Registered decomposition | The source stays recognisable while regions lift into categories | Extend |
| Wall → one actor | A field of items collapses to one subject, then that subject produces a result | Contra |
| Carousel emphasis | One bright active item. Neighbours recede | MadeThis |
| Request → picker → confirmation | A message stays anchored while a sheet rises, a choice is made, and the state confirms | Poke |
| Colour-field handoff | One soft field behind a real lockup, once, and only if the storyboard names it. A centered gradient title card stays banned | Conduit |
| Tile chapter break | A grid of tiles as a single accent between chapters, storyboard-named. Not a new primary seam, and not a new block name | Pilot Protocol |

### Launch-film notes (links only)

Per-film links and timestamps live in upstream [launch-film-notes.md](https://github.com/echris6/motion-video-kit/blob/main/business-motion-film/references/launch-film-notes.md). The films stay with their owners. Do not download them into this repo, and do not redistribute the footage. Strongest motion references named there: Contra, Wonder, Bolt, Work Louder, Replit, Extend, Poke, AsideHQ. Reach numbers on those posts are studio claims.

## Gallery themes (style only)

Browse the free [MotionVideo gallery](https://motionvideo.xyz/) for density, not for files. Useful public themes: Bold kinetic type, Kinetic type music machine, Pencil line, Beat-synced generative, Photo print launch, Claude motion designer showreel. Do not buy or paste the paid pack. A photo-print or product launch still uses real screenshots and the real logo. Launch beats follow the house recipes in `templates.md`.

## Scout notes

Principles rewritten here. Nothing from these repos is installed.

- [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) — duration tables, directional easing, stagger budgets, choreography shares.
- [dylantarre/animation-principles](https://github.com/dylantarre/animation-principles) — selected Disney-12 micros (timing frames, anticipation, follow-through, staging). The rest of that tree stays out.
- House overrides that those sources do not share: 0% overshoot on display type, no blur on glyphs, no third `seek(t)` renderer.
- [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) (MIT, Copyright (c) 2026 echris6) — six motion-grammar rules and the mechanism catalog above. Timing numbers in that file that repeat this page were left out. `business-offers.md`, sample commercials, and their scripts were not folded.
