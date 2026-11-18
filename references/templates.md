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
- [nexu-io/openmotion](https://github.com/nexu-io/openmotion) (Apache-2.0) — the story shapes and direction cards above. Its bundled Product Promo template is a HyperFrames registry example and is not copied.

## Adding a template
Copy the smallest template folder, rename it, edit `template.json`, and write `build(content, ctx) -> scenes` using
`templates/_shared/kit.py` helpers (`stage`, `cut_js`, `endcard`, `words_in`, `rollnum`, `attach_vo`) and the
`rs.js` runtime (`enter`, `exit`, `drift`, `kenburns`, `roll`, `wipe`, `camera`). Styles live in `_shared/base.css`. Then render the 3 aspects with `--draft` and check every scene's frame.
