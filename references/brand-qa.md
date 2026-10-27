---
description: Load before a client draft leaves the box. BRIEF frame stills first, then review.py contact.jpg and phone.jpg. Fresh reviewer, builder ≠ judge, item-by-item, worst three, scores to 8+. Fails skills-skipped animatics, gradient title cards, free fades, invented UI, sparse selects, and interview-TEMP drift. The SageCut ladder at the bottom is optional and off.
---

# Brand QA gate (client video)

Run before any client draft leaves the box. Fail = do not send.

## BRIEF frames

The storyboard is the BRIEF (`storyboard.md`). Before trusting playback, snapshot every shot at its frame numbers and Read the PNGs. HyperFrames: `$HF snapshot --at` with those times. Remotion: `npx remotion still <id> out/f.png --frame=N`. Then run `review.py check` so `contact.jpg` and `phone.jpg` exist. A moving preview does not replace the stills. Seek the same `t` twice before you call a frame done (`motion-design.md`). Pixels match, including a seek that jumps backwards.

## Fresh reviewer

The author of the comp does not grade it (builder ≠ judge). A second pass scores from the stills alone, without the author's intent. Score 1–10: hook, phone, motion, variety, brand, sound. Fix the three worst. Re-snapshot those frames and score again. Do not send a client draft while any score is under 8. `review.py` prints the table. You still fill it. When a previous report exists, the next pass is item-by-item and writes a ledger (Independent critic, below).

## Checklist
1. **Typography** — zero typos; high contrast; tight tracking on display; no clipped glyphs.
2. **Logo variants** — correct mark for light vs dark backgrounds per brief; never the forbidden variant.
3. **Logo plates** — no ad-hoc solid plates behind logos unless the brief requires them.
4. **End-card grid** — even optical sizes, equal gaps, single row/grid; all required partners present. That even row is the end-card default. `poster-grid` is an optional type grid (`kinetic-type.md`), and only when the storyboard names it. Marks inside it still pass this item.
5. **Safe zones** — key type/faces inside platform safe areas (`platform-specs.md`).
6. **Flash / accessibility** — ≤3 flashes/s; captions on speech.
7. **AI disclosure** — only when AI faces/voices/gen media are in the cut; not required for licensed real footage alone.
8. **Contact sheet** — snapshot open, mid (power/talent), takeover, end; Read PNGs before delivery.
9. **Kinetic type** — showreel rules in `motion-design.md`: one display face, one UI face, one accent; mask/stagger; no overshoot on display type; something new every 2–4s. Fail the ban list: centered gradient title cards, free fades, invented product UI, corner labels, frame borders, glow on UI chrome, generic particle bursts, blurry scaled text.
10. **Scores before full render** — fresh reviewer, stills first, then `contact.jpg` and `phone.jpg`. Six scores, worst three, each at 8 or higher before a delivery render. A later pass marks each prior finding FIXED, PARTLY, or STILL PRESENT.
11. **Comparison bar** — the cut is dense real footage plus kinetic type (`client-sizzle.md`). Fail a skills-skipped animatic, a fade-card title, a sparse select when footage exists, or an interview TEMP / Flashtalk drift the user did not ask for.

## Commands
```bash
# HyperFrames
npx hyperframes@0.8.197 snapshot --at 1,12,28,42
# Reelsmith review
python3 scripts/review.py check VIDEO --out OUT/_review --preset youtube --job OUT/job.json
```

## Typo denylist (extend per job)
STUIO→STUDIO, POSSIBLITY→POSSIBILITY, performace→performance, untill→until, teh→the

## Scout notes

Harness rules applied here, not fetched as posts and not installed as skills: a frame-numbered BRIEF, stills before playback, a fresh reviewer, worst-three until 8+, the ban list above, and `seek(t)` on the HyperFrames or Remotion clock. One brand per session is the effort tier in `client-sizzle.md`.

## Independent critic (Gauntlet)

The fresh reviewer above is this loop. A second pass scores the stills. When a prior report exists, that pass checks every prior item and writes a ledger. HyperFrames skills stay on. This loop does not install a critic product, does not call a paid API, and does not require `SAGE_API_KEY`. The SageCut ladder below stays off.

Adapted from [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) `business-motion-film/references/gauntlet.md` and `critic-prompts.md` (MIT, Copyright (c) 2026 echris6; read at `e4b1c0004080`). That kit credits the Gauntlet Loop idea. House artifacts replace their lab scripts: BRIEF stills, `contact.jpg`, `phone.jpg`, and `review.py`.

### Rules

1. **Bar first.** The BRIEF says what done means. Each of the six scores at 8 or higher is the house bar.
2. **Split the cut.** A scene, a type move, a seam, and the mix are separate parts. Fix the largest gap first. Polish the open before you polish the end card.
3. **Builder ≠ judge.** The reviewer gets the stills, the brief, the client's words, and, on a verify pass, the previous report. Leave the builder's reasoning and the list of intended fixes out of that prompt.
4. **Pixels and the sheets.** Judge the frames. `review.py` already measures black frames, frozen stretches, flashes, and loudness. The reviewer still Reads the PNGs. Seek the same `t` twice (`motion-design.md`).
5. **Item by item.** The next pass marks each prior finding **FIXED**, **PARTLY**, or **STILL PRESENT**, then looks for regressions. A fix often covers one element and clips another.
6. **Stop** when every score is 8 or higher, the remaining items are cosmetic, or the user says stop.
7. **Ledger.** One table in the job notes: round, artifact, top findings, changes, what `review.py` measured.

| Round | What the reviewer sees | Verdict |
|---|---|---|
| Storyboard | Board plus rough frames | Chronology, true claims, a distinct composition per beat |
| Beat | Stills of one move | Readability, collisions, pops, what information the move adds |
| Full film | Contact sheet plus `phone.jpg` | Holds, empty space, seams, pacing, mute clarity, sound on the hits |
| Verify | New stills plus the previous report | FIXED / PARTLY / STILL PRESENT, regressions, then READY or one more pass |

READY means the draft can go to the user. It still needs their yes (`review.py approve`).

### What a fresh pass catches

Lessons from upstream rounds, rewritten onto this gate:

- A one-frame pop when an ease starts at full speed. Display type uses `power3.out` or `expo.out`. A physical lift uses smootherstep, with a few milliseconds of stagger on a repeating part.
- A wipe that splices two titles into one word. The outgoing title leaves before the wipe. The incoming title enters after it (`transitions.md`).
- A camera that goes near top-down and tiles a textured plane. Keep a three-quarter view and a minimum distance (product-hero notes in `remotion.md`).
- A card that goes blank between states. Crossfade the contents in place.
- Type crossing type. Leave, then arrive. Check every frame of a crossfade, including the middle.
- A heading that drifts because its parent is still scaling. Give the overlay the same move.
- One tween driving two captions, so the label names the wrong picture.
- Music that ends before the logo, or hits that bury the hero move (`music.md`). A hold that is actually frozen frames. Ambient idle is the house fix (`motion-design.md`).

### Prompts

Copy, fill the slots, and send each to a fresh pass. Keep the builder's notes out.

**Beat**

```
You did not build this. Judge the stills.

Artifact: BRIEF frames and contact.jpg for <shot id> (<t0>–<t1>). Brand: <palette>, <type>. It should show <one sentence>. Client words: <verbatim, or "none">.

Read the PNGs. Look at joins, type, collisions, and a one-frame pop.

Under 450 words:
- KEEP / REVISE / REJECT
- Defects by severity, with timestamps
- The 3 highest-value fixes, on HyperFrames (skills on; never HYPERFRAMES_SKIP_SKILLS) or Remotion (useCurrentFrame)
```

**Full film**

```
You did not build this. Judge pixels and the review.py measurements.

Artifact: <video or contact.jpg + phone.jpg> (<duration>, <size>). <What the film sells.> Brand: <palette>, <type>.
Previous report, if any: <path>. Check which items are fixed.
Client words, verbatim: <paste>.

Read the BRIEF stills, contact.jpg, and phone.jpg. Use the review.py loudness, frozen-stretch, and flash lines. Do not install SageCut. Do not call a paid critic API. HyperFrames skills stay on. Do not set HYPERFRAMES_SKIP_SKILLS. Do not suggest a third renderer.

Under 900 words:
1. Per scene: range, what is on screen, empty space, seconds it could lose, ranked problems.
2. Layout and seam defects with timestamps. Frame 0 is a finished composition.
3. The top 6–8 changes, concrete, on this clock.
```

**Verify**

```
You did not build this. New stills: <path>. Previous report: <path>. Timings moved by about <x>s.

For every prior item: FIXED / PARTLY / STILL PRESENT, with timestamps. Then new defects: overlaps, clipped type, one-frame pops. Check the hit at <time> against music.md.

Under 500 words. End with READY or ONE MORE PASS (at most 3 fixes). READY means the six scores in brand-qa.md are each 8 or higher. The user still approves before delivery.
```

**Storyboard**

```
Review this storyboard for a <length>s film for <business>. You did not write it. Check: the chronology matches the real service; every claim is true or labelled; each beat has a distinct composition and a job; which beats are filler; the CTA reads on mute at phone size. Ranked problems, one concrete fix each. HyperFrames skills stay on for the build that follows.
```

### Compressed schedule

When the user shortens the schedule: land the beats that work, drop a half-built move, render the delivery size, run one full-film pass, apply its top fixes, run one verify pass, and list every beat whose last fix was not re-checked.

### After the scores clear

The client still reviews. On one upstream 20 s spec, the critic said ship and the client then found empty UI space, text over text mid-crossfade, a state label that contradicted the number, a weak opening frame, a lingering first shot, music that did not match, and three rounds of effect level. Put these on the verify pass:

- Overlaps on every frame of a crossfade.
- A label that matches the value on screen.
- A glanceable layout with no dead band. Each tile earns its space.
- Hero moves stay audible on the cue sheet (`music.md`): the role's sync tap and a bed-relative level, not one gain copied onto every stem. House loudness stays about −14 LUFS, true peak at most −1 dBTP (`loudness-accessibility.md`).

Studied progress on one upstream film, not a house quota: frozen time fell across four rounds, and a flat mix gained range. `review.py` remains the measurement. Their frozen-time and loudness scripts are not in this repo.

## Optional: SageCut measurements

Off unless a Remotion motion-graphics job asks for it. Client sizzle and live footage stay on the BRIEF, the stills, and `review.py` above. This ladder is not the taste, sound, and harness pack. Do not install SageCut, do not vendor it, and do not add a sidecar skill tree.

Sources, cited only: [levantolabs/sagecut-release](https://github.com/levantolabs/sagecut-release) (MIT), [Shann³ — cheaper frame review](https://x.com/shannholmberg/status/2114396613468910070).

**SageCut 0.3 does not support camera footage.** It is tested on motion graphics. Frozen-frame and color checks on camera footage are out. Live selects stay on the gate above.

### Ladder

1. **Local frame measurements** (OCR and pixels): text size, blank frames, frozen frames, brand colors, delivery spec. Zero API.
2. **Sage triage**, only when a Sage key is already present and the hold below is lifted.
3. **Opus critics only on the frames triage flags.** Open a frame when a measurement and triage disagree. Critics do not watch the whole film.

The upstream local switch is `gate --no-sage`: measurements only, no upload. Reelsmith does not ship that binary. On the house path, `review.py check` still covers black frames, frozen stretches, flashes, and loudness. Read `contact.jpg` and `phone.jpg`.

### Measurement recipe

Motion-graphics frames. OCR at full resolution. Spec on the file you send. Pixel floors are for 1080 px wide; scale them with width.

| Check | Measure |
|---|---|
| Text size | OCR height. Floor: headline 60 px, body 40 px, captions 30 px, URLs and legal 26 px. `phone.jpg` still sets the house phone score. |
| Blank frames | Ink on every frame of a transition. An empty frame between two fades fails. |
| Frozen frames | A run of identical pixels. A BRIEF hold with ambient idle (1–2% drift) is not a frozen frame. |
| Brand colors | Sampled pixels against `brand.json`. An off-palette field fails. |
| Delivery spec | H.264, integrated loudness about −14 LUFS, true peak at most −1 dBTP (`loudness-accessibility.md`). |

### Hold

Sage API calls and Opus critics stay **HOLD** until Marc lifts paid-gen spend. Do not require `SAGE_API_KEY`. Do not prompt for it. Do not send frames out.

Demo framing, Remotion motion graphics only: an Opus critic on every frame is the slow, expensive review. The ladder measures locally and would send only flagged frames. A published Levanto reference rate is about $0.10 and 8.6 s per critic frame view. That figure is not a Reelsmith quote, and it does not lift the hold.

`review.py` pass/fail stays as it is.
