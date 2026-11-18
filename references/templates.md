# Templates

A template = `template.json` (contract: slots, budgets, required, aspects, energy, caption style) +
`build.py` (scenes -> HyperFrames HTML) + `sample.json` (working example content). Every template renders
16:9, 9:16 and 1:1 from one content file, takes `brand.json`, and is beat-snapped when music is given.

    reelsmith.py list
    reelsmith.py sample howto-tutorial > content.json          # edit this
    reelsmith.py render --template howto-tutorial --content content.json --brand brand.json \
        --aspect 16x9,9x16,1x1 --out out/howto [--music track.mp3|synth|none] [--vo auto|none] [--draft] [--dry-run]

| Template | Use for | Length | Required slots | Music | VO |
|---|---|---|---|---|---|
| product-launch | launch reel, feature drop, app promo | 16-24 s | product, headline, features[3], cta | led by it | optional |
| event-recap | conference, meetup, offsite highlights | 15-35 s | event, photos[3-10] | led by it | optional |
| testimonial | customer quotes, reviews, social proof | 12-30 s | quotes[] | soft bed | optional |
| countdown-teaser | "coming soon", launch/date teaser (loopable) | 10-20 s | title, date_text | led by it | no |
| stat-callout | data story, report highlight, milestone | 14-30 s | title, stats[1-3], source | bed | optional |
| slides-presentation | talk loop, booth/kiosk screen, explainer deck | any | title, slides[] | bed | optional (VO-paced) |
| howto-tutorial | screen walkthroughs, tutorials, onboarding; emits YouTube chapters | 30-120 s | title, sections[] | low bed | yes (Kokoro free) |
| feature-explainer (Remotion) | narrated product explainer with captions | 20-60 s | edit `src/plans/feature-explainer.ts` | bed | yes |

Notes per template
- **product-launch / event-recap / countdown:** pass `--music`. Scene lengths snap to bars/half-bars. Countdown
  numbers scale on a steady background (no luminance flashes, WCAG 2.3.1). Product-launch also follows the house recipes below.
- **testimonial:** only real quotes the user has permission to use. Name, role, company and rating are optional.
- **stat-callout:** `source` is required and shown on screen. Numbers count up; the bar chart uses brand colors.
- **slides-presentation:** slide kinds: title, section, bullets, stat, quote, image, question. Deck chrome shows
  "n of N". `--loop` makes the last frame match the first; then `reelsmith.py loop VIDEO --times 10 -o kiosk.mp4`
  (stream copy) and `reelsmith.py seam VIDEO` (first-vs-last PSNR; >= 30 dB counts as seamless).
- **howto-tutorial:** section kinds: intro, step (screenshot + `focus` {x,y,zoom} camera move + `callout`),
  three (key points), compare, checklist, outro. Coordinates are fractions of the image. Each scene carries a
  `chapter` name in job.json, which `youtube_prep.py` merges into YouTube chapters. When captions are burned (vertical by default), the step body text is hidden so they never collide.
- **feature-explainer:** Remotion engine (`templates/feature-explainer/render.sh [OUT] [--draft] [--brand brand.json]`):
  unpacks the starter kit, free VO, 3 aspects, loudnorm, SRT/VTT/ASS. `reelsmith.py render` refuses it and points here.

## Media slots
`image`/`photos` accept a local path, a file from `stock.py fetch`, or `../_media/*` placeholders (free CC0/CC
images, credited in `_media/credits.json`). Never hotlink. Missing media fall back to a branded gradient.

## Content budgets
Each slot has a character budget (for example `title: 28`). Over budget -> the contract check warns and the
build shrinks type. Better: rewrite shorter. `script_lint.py script.json --preset reels` checks VO pace,
on-screen text length, the 3-second hook and the CTA (see scriptwriting.md).

## House launch recipes

For `product-launch`, and for a product beat inside a client sizzle. Short rules. Do not install a launch skill, and do not render with Playwright. HyperFrames (skills on) or Remotion is the path. Taste numbers: `motion-design.md`. Cues: `music.md`. Frames: `storyboard.md`.

1. **Real UI in a device.** A real screenshot or capture sits inside a phone or a laptop frame. A close-up may crop the top and bottom. The device edge stays visible so the shot still reads as a device. Full-bleed invented chrome is a fail. Missing screens are not filled with generated UI.
2. **The cursor drives the change.** Position comes from the closed-form spring in `motion-design.md`. The click lands on a beat. Press scale lasts a few frames. The path is written down. It is not `Math.random()`. One cursor.
3. **One-shape morph.** On a launch reel, one container may change width, height, and corner radius while the content inside swaps. The outgoing content leaves early, at about 65–75% of the enter time. A few pixels of blur on the swap clear before the hold. Do not morph display type. On a client sizzle the primary seam stays a hard cut (`transitions.md`). A morph is one accent, and only when the same real screen is what continues.
4. **Bar-accurate cuts.** Every event is `b(n)` on the `beats.py` grid. One visual change per beat. The result holds long enough to read (about 1–2 s, still on the grid). The biggest reveal is a downbeat. `seek(t)` is the paused GSAP timeline or `useCurrentFrame()`, including a seek backwards.
5. **Beat SFX.** The cue sheet uses the same `b(n)` as the picture. Fill a launch role bank (`music.md`): whoosh on the primary seam, tap or click on the cursor and the chips, one reverse swell into the drop, one impact on the drop, chime on the end mark. Each row carries `offset_ms` and `bed_db`. The bed is the licensed track or `beats.py synth`. Idle stays silent.

Storyboard the beats before the build. Snapshot the open, the device, the drop, and the end, and Read those stills before a delivery render (`brand-qa.md`).

### Optional poster grid

`poster-grid` is one grid recipe in `kinetic-type.md`. Use it when the storyboard names it. The template ending stays `endcard()` (logo, kicker, CTA, URL). The partner lockup stays the even end-card row (`brand-qa.md`). `mask-reveal-up` stays the default for body and headline lines. Do not install a poster-grid package.

### Launch story shapes

Pick one by the material you actually have. None of them is the default, and the seconds are a guide, not a contract. All three keep the house recipes above and `endcard()`.

| Shape | When | Beats |
|---|---|---|
| **Proof** | A software feature with real before, action, and result captures | Problem (the real before state, tight) → action (real capture in a device) → change → **verify hold** → CTA. About 15 s. |
| **Detail** | A physical product, a space, or a small photo and video set | Object (hero frame) → one meaningful detail → use or context → name and CTA. About 12 s. Fewer words, longer holds. |
| **Rhythm** | The user hands over a reference clip | Run `review.py check` on the reference and read its `cuts.json`, then write a map: reference time → new shot → new asset. Re-check every hold after the swap; new material often needs longer to read. |

- **Verify hold.** After the change, hold the real result for 1.5–2 s on the grid with no competing copy, so the viewer can check it. It is a read, not a freeze (rule 1 in `motion-design.md`).
- **Detail needs different views.** One photo repeated under new adjectives is not a detail beat. Do not fake 3D or a light sweep from a flat photo. With stills only, say it is a stills edit.
- **Rhythm keeps pace, not content.** A detected cut is not a scene. The reference's footage, words, and music stay out of the film (`storyboard.md`, Breaks).

### Exploded reveal (optional product shot)

A physical product, drawn in code as separate parts, turns, shows its details, comes apart and goes back together in one continuous take. It is one optional shot for the **Detail** shape, or the one named spectacle on a client cut. It is never a default, and its paper-and-ink look is one look among many, not a house style.

**Rights first.** Only the client's own product, built from what they supply: dimensions, CAD or a parts list, and photos of every face the camera visits. An inside nobody has shown us is a `NEED`, or the shot stays on the outside. This is a model built from real measurements, not fake 3D from a flat photo (Detail shape, above). Never a competitor's or another brand's product, never a guessed interior, never generated parts. A drawn object that could pass for a photo is labelled as illustration (`brand-qa.md`, item 12).

**Rhythm** (10 s base, 30 fps): drift, whip, hold, repeated, then apart and back. Nothing stops until the hero, and the hero ends in ambient idle, not a frozen last second (`motion-design.md`, rule 1).

| Beat | Numbers |
|---|---|
| Tumble in | About 1.5 s. The object turns about half a revolution into a three-quarter view while its tilt rights itself; slow start, fastest midway, settle. It fills about 60% of the frame width |
| Whip | About 0.24 s (7 frames), the same length every time. Speed-based motion blur (`transitions.md`, Polish recipes) |
| Detail hold | 0.6–1.0 s at 4–8× zoom on a real detail, with a slow slide or push. Something on it moves if it really does (a dial, a latch) |
| Feature | About 1.2 s. One real mechanism works and comes back |
| Explode | About 0.4 s, ease out. Assemblies separate along their own axes; outer parts lead |
| Apart hold | About 0.9 s, a 10–15° turn and a slight zoom out |
| Implode | About 0.65 s, ease in-out, turning to face the viewer |
| Hero | About 1.1 s. Front three-quarter at about 75% of the width; a slow push that eases into a 1–2% breathing drift |

- **Retime, do not slow down.** Whips keep their length. Every other segment scales by one factor. Under about 3 s the holds cannot be read. Past about 12 s, add beats (a second detail pass, a cross-section hold, a second feature, a longer apart hold with a slow orbit) instead of stretching.
- **One set of keys for every aspect.** Write the keys for 9:16. On shorter frames, wide shots zoom out until the whole object and its explode fit; detail shots keep their zoom. Snapshot each delivered aspect before rendering.
- **Choose angles from stills.** Render four or five candidate poses as stills and pick by eye; do not guess numbers. Then snapshot every beat.
- **Build in the existing stack.** Each part is its own layer with a fixed isometric projection (screen x = (x − y) · cos 30°, screen y = (x + y) · sin 30° − z), painted far to near. Every pose is a function of `t` (HyperFrames timeline or Remotion frame). The device notes in `remotion.md` apply. No 3D package and no new renderer.
- **Sound** from the launch role bank: a whoosh per whip, a tick on the feature, a swell into the explode, an impact when the parts lock (`music.md`).

*Source: the shot rhythm, the fixed whip length, the retime rule, one-key-set framing, and pose stills after annnguyentt/anatomy-reveal-skill (MIT, Copyright (c) 2026 Ann Nguyen, github.com/annnguyentt/anatomy-reveal-skill @dd01e1c), `references/shots.md`, which builds on wheresryan22/anatomy (MIT, Copyright (c) 2026 Ryan, @1482e84). Rewritten as an optional shot. Their kit, materials, template object, scripts and demo media are not used.*

### Direction cards at plan approval

When the user should choose, show two or three cards built on different shapes or looks, not three tints of one idea. Each card has six lines:

```text
Opening: the exact first frame and line
Story: shots with seconds
Material: what is HAVE, and the gaps (NEED)
Look: the LOOK.md or recipe it uses
Preview: a still path, or "text only, not rendered"
Trade-off: what this direction gives up
```

"You decide" is a valid answer. Record the pick in `EDIT_LOG.md`. Card labels and sample names never appear in the film.

*Source: proof, detail and reference-rhythm outlines, the verify hold and the direction card after nexu-io/openmotion (Apache-2.0, github.com/nexu-io/openmotion @664be50) (`skills/openmotion-template-to-video/references/recipes.md`). Our words.*

### Campaign cuts

After the master scores 8 or higher, a second hook and the other aspects are props, not a new film. Two hooks × three formats: `remotion.md`. Do not redesign the UI per cell.

## Scout notes

- [AbubakrChan/product-launch-motion](https://github.com/AbubakrChan/product-launch-motion) — cursor-driven UI, one-shape morph, beat SFX. The Playwright subframe renderer is not adopted.
- [kaventro/motion-designer](https://github.com/kaventro/motion-designer) — real UI in a device frame, cuts written as beats, `seek(t)` checked out of order. Not installed.
- [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) — launch shape (one sentence, real screens, CTA that holds) and brand intake. Intake is two lines on `brand.json` (`brand-kit.md`), not a new `MOTION.md`. A `LOOK.md` (`motion-design.md`) holds motion language only, never brand.
- [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) launch preset — the role bank in recipe 5 (whoosh, tap, swell, impact, chime), with sync taps and bed-relative levels in `music.md`. The sound bank is not installed.
- [annnguyentt/anatomy-reveal-skill](https://github.com/annnguyentt/anatomy-reveal-skill) (MIT) on [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) (MIT) — the exploded reveal above. The kit, its Puppeteer renderer, the interactive figure page and the worked example object are not installed or copied.
- [nexu-io/openmotion](https://github.com/nexu-io/openmotion) (Apache-2.0) — the story shapes and direction cards above. Its bundled Product Promo template is a HyperFrames registry example and is not copied.

## Adding a template
Copy the smallest template folder, rename it, edit `template.json`, and write `build(content, ctx) -> scenes` using
`templates/_shared/kit.py` helpers (`stage`, `cut_js`, `endcard`, `words_in`, `rollnum`, `attach_vo`) and the
`rs.js` runtime (`enter`, `exit`, `drift`, `kenburns`, `roll`, `wipe`, `camera`). Styles live in `_shared/base.css`. Then render the 3 aspects with `--draft` and check every scene's frame.
