---
description: Load on every client sizzle, right after client-sizzle.md. Copy examples/storyboard/ and replace the fictional beats. The JSON is the frame-numbered BRIEF. Reference breakdown and sourced figures land here before motion. HAVE plays, ID waits, NEED and TEMP stay labelled and out of the client draft.
---

# Storyboard (client sizzle source of truth)

For awards / partner / client sizzles, build a **storyboard before the edit**.
Marc’s Clio Unhinged board (`storyboard.py` → `storyboard.json` + `storyboard.html`) is the craft bar:
dark film-room HTML, proportional timeline, PDF-beat alignment, shot cards with thumbs, HAVE/ID/NEED/TEMP status, production bible.

## Why
Grey animatic cards and mid-job talk-head pivots happen when there is no shot-level source of truth.
The storyboard is what the edit builder and humans both read. It is the reference spec and the data file in the harness (`hyperframes.md`). Motion waits on it.

## Outputs
| File | Role |
|---|---|
| `storyboard.py` (or equivalent) | Authoring: shots, beats, sources, VO, status |
| `storyboard.json` | Machine read for the edit builder |
| `storyboard.html` | Human review (timeline + cards + brand rules) |
| `thumbs/` | Optional 16:9 stills per shot |

## Every shot must name
1. **Time** — `t0` / `t1` (seconds)
2. **Brief beat** — which PDF/script beat it serves (skip none)
3. **Picture** — description + source (still/video/render) + in-point
4. **On-screen words** — kinetic / lower-third / none. Kinetic shots name the on-screen line (2–6 words) and a house recipe from `kinetic-type.md` (default `mask-reveal-up`, implemented in GSAP or Remotion, not passed as a HyperFrames block). One display face, one UI face, one accent (`motion-design.md`). No invented UI.
5. **Voice** — narrator / interview / mute
6. **Audio** — music / duck / SFX
7. **Story intent** — one line
8. **Status** — `HAVE` \| `ID` (identity confirm) \| `NEED` \| `TEMP` (placeholder by design)
9. **Cue** — `b(n)` from `music.md`, or `none`. Same clock as `t0`. A designed hit also names the role, `offset_ms`, and `bed_db` (`music.md`). A launch reel uses the role bank (whoosh, tap, click, knock, reverse swell, impact, chime).

## BRIEF (frame-numbered)

The storyboard JSON is the BRIEF. Do not add a second spec the edit can drift from. Set `fps` (30 unless the render is 60). For each shot, frame numbers are `round(t * fps)`.

### Reference, then data

The direction block is the spec. Before the shots, name one reference the user actually pointed at (or a house cut already in this repo) and write four lines: pacing, where the first motion lands, the cut rhythm, and where the payoff lands. A mood word ("clean and modern") is not a spec.

Every number on screen has a source on the shot (`src`, or a `source` string) or in `content.json`. No source: stop and ask. Do not animate a guessed figure. A wrong number inside a finished move is still wrong.

Story intent is filled before the comp: one point, one hero number, three beats — hook, proof, payoff (`scriptwriting.md`). A note such as "the title is a beat late" changes one `t0` or one `b(n)`. It does not rebuild the board.

Write one line per shot before the build, and keep it next to the board:

```
f{frame0}–f{frame1}  {t0}–{t1}s  {id}  {picture}  |  {words}  |  {kinetic}  |  {cue}
```

`frame0 = round(t0 * fps)`, `frame1 = round(t1 * fps)`. Snapshot those times and Read the stills before trusting playback (`brand-qa.md`). A product shot also names the device (phone or laptop) and the real screen (`templates.md`).

The open example sets `"fps": 30` in `examples/storyboard/storyboard.json`.

## HTML craft bar (keep these)
- Dark screening-room theme; display + body + mono font trio
- Proportional timeline: PDF beats on top row, color-coded shot bars, glitch markers
- Brief-alignment table (beat → VO → picture requirement)
- Shot cards in act order with thumb, status chip, picture/words/voice/intent
- Characters / ID queue / word art / audio strategy / splice notes as needed
- No grey “FOOTAGE TBD” cards in a client-facing draft — TBD lives in status chips + NOTES

## Workflow hook
1. Lock brief beats (verbatim from PDF/script).
2. Author storyboard → generate JSON + HTML; open HTML with the user before long renders.
3. Ingest only `HAVE` (and approved `ID`) into the edit; keep `NEED`/`TEMP` out of client drafts unless labelled.
4. Edit builder reads `storyboard.json` — do not invent shots not on the board.
5. Brand QA (`brand-qa.md`) on the rendered cut; storyboard HTML is not a substitute for frame snapshots of the MP4.

## Direction block (once per film)

Source: [HyperFrames storyboards](https://hyperframes.heygen.com/prompting/storyboards). Say this once. Shots inherit it. The machine shape stays the shot list above; these fields sit beside it (`direction` on the example JSON).

- **Message** — one sentence. A shot that does not serve it comes off the board.
- **Arc** — for a kinetic sizzle, Hook → Build → Punch → Resolve, mapped onto the brief beats.
- **Audience** — who it is for, in a phrase.
- **Mood** — one energy line. Pacing agrees with it.
- **Two-color** — ground and ink. A bigger moment gets bigger by scale, weight, inversion, or density. A third hue is the one brand accent, and only on emphasis words.
- **One breather** — name the calmer shot. It is a held read, not a second animation pass. It still does not freeze (ambient idle in `motion-design.md`).
- **Callback** — plant a motif (a door, a word, a mark) and say how it returns, denser.
- **Actor** — one object that keeps its identity across shots (motion grammar in `motion-design.md`). Frame 0 of the open is a finished composition.
- **Spectacle** — one beat, named, or it gets dropped (`motion-design.md`).
- **Standing negatives** — the ban list in `motion-design.md`, plus no invented UI, no Flashtalk drift, no `HYPERFRAMES_SKIP_SKILLS`.

Each shot still names picture, words, and kinetic recipe. Also name, in one line each when they are not obvious: **type** (hook, proof, cta), **persuasion** (before/after, enumeration, callback), **beat** (recognition, punch, resolve), **focal** (the one thing the eye hits).

The open board is `examples/storyboard/` (fictional Harbor Atelier, all four statuses, a named spectacle, no client media).

## Take-apart dossier (optional, for studying reference films)

When a client or awards brief points at one exceptional film, read it before building your board. This structured breakdown captures what makes it work, so you can take its **shape and pace** without copying its **subject, words, pictures, or music**.

Write a dossier in your film folder as `REFERENCE.md`, under these sections:

1. **Seen.** Pin the reference: watch it, note what you observe frame by frame (stills at two frames per second), where motion lands, and where it rests. Evidence comes before interpretation.

2. **Measured.** Numbers that describe the reference: duration, cuts per minute, how long type stays readable, when the loudest moments fall, where the music peaks. Measurements keep your rebuild honest — a "fast-paced" reference may cut every 1.5 seconds, or every 4, and your board must match the real number.
   - Cuts: run `review.py check REF.mp4 --out ref/_review` and read `cuts.json`. Count `cut` rows per minute; `flash`, `fast` and `transition` rows are not new shots. Shot lengths are the gaps between cuts.
   - Events: wherever something enters, leaves, or changes, read the consecutive frames a few either side, not a once-a-second sheet. Note how it arrives (pop, scale, fade, wipe, type-on) and the frame it lands. A thing fully there on one frame is a hard switch; tween only what you saw move across several frames.
   - Look: for a "make it look like X" brief, measure one topic per pass (motion, depth of field, outlines, textures, characters, light, grade), each written as numbers, not adjectives: median luma, darkest non-black percentile, saturation p90, line width in px at 1080 wide, blur radius per shot size, push-in % per frame. Those numbers, not the frames, are what later passes compare against. The reference frames stay private study material.

3. **Take.** What you adopt and what stays theirs:
   - **Spine:** The film's structure on a time ruler — its parts, topic changes, and where one moment hands to the next.
   - **World:** What everything on screen is made of, and why that material belongs to the subject. The ground's job (a question it answers, or depth it reveals).
   - **Formal idea:** The one move the whole film follows.
   - **Hand-overs:** At every boundary between moments, what carries the eye across: a thing that becomes the next thing, a thing that stays, a matched cut, a visible threshold (a door), or a change of ground. "Next" is not a reason.
   - **Weak spots:** Where the reference drops or feels thin. Do not carry those forward.
   - **Keeps:** The shape, the order of its parts, its formal idea, its hand-overs, its pace, the job its ground does.
   - **Breaks:** Its subject, its words, its pictures, its characters, its music. A viewer of both films should say "the same kind of film," never "a copy."

This dossier is your board's foundation. Where your product has no honest answer to one of the reference's parts, cut that part rather than faking it.

For the five kinds of boundaries between moments (becomes / carried / matched / door / change of ground), see **transitions.md**.

*Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525). Cut and event measurement after heygen-com/hyperframes (Apache-2.0, github.com/heygen-com/hyperframes @d317abc) (`skills/reverse-any-video`, `measure cuts`); one-topic look reports after mromidev/claude-animated-shorts (MIT, Copyright (c) 2026 Mr omi, github.com/mromidev/claude-animated-shorts @e3b817b) (`SKILL.md`, look-match loop). Our words.*

## Anti-patterns
- Skipping the board and jumping to Flashtalk / AI talk-heads
- Shipping placeholder-heavy animatics when selects exist (`HAVE`)
- Putting unconfirmed faces on screen without `ID` clearance
- Encoding client secret paths or private media into the public skill examples — use placeholders in repo examples

## Repo layout (suggested)
```
examples/storyboard/     # generic minimal demo (no client media)
references/storyboard.md # this file
scripts/storyboard_*.py  # optional shared generator later
```
