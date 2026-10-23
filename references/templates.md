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
  numbers scale on a steady background (no luminance flashes, WCAG 2.3.1).
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

## Adding a template
Copy the smallest template folder, rename it, edit `template.json`, and write `build(content, ctx) -> scenes` using
`templates/_shared/kit.py` helpers (`stage`, `cut_js`, `endcard`, `words_in`, `rollnum`, `attach_vo`) and the
`rs.js` runtime (`enter`, `exit`, `drift`, `kenburns`, `roll`, `wipe`, `camera`). Styles live in `_shared/base.css`. Then render the 3 aspects with `--draft` and check every scene's frame.
