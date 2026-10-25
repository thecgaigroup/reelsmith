---
description: Load first for an awards, partner, or client sizzle from real footage (about 30–60s). Holds the density-and-type bar, the anti-patterns, and the six-part skeleton. Then load storyboard.md, kinetic-type.md, transitions.md, motion-design.md, hyperframes.md, and brand-qa.md.
---

# Client sizzle (footage-first editorial)

Awards, partner, or brand sizzle from real selects. Not a product-launch template. Not an AI talk-head.

## Bar

Match a denser cut than the last Reelsmith pass on this kind of brief. That cut won on **real footage density** and **kinetic type**. The weak pass lost because skills were skipped, selects were thin, type was a fade card, and the job drifted into an interview TEMP. Rights did not force that. Do not treat the current sizzle as already at that bar.

Fail the draft if you see any of these:

- `HYPERFRAMES_SKIP_SKILLS=1`, or a comp written before `/hyperframes` is loaded
- One still per beat, or a grey card, when phone / iPad / Day-Of selects exist
- Centered title on a gradient, or a fade-in as the whole idea
- Invented UI, or a Flashtalk / interview TEMP the user did not ask for
- Paid image or video generation used to fill a hole

Do these instead:

- Several real pictures per beat. A new picture or a new type event every 2–4s.
- Storyboard first (`storyboard.md`, copy `examples/storyboard/`). HAVE plays. ID waits. NEED and TEMP stay out of the client draft unless labelled.
- Default type is house recipe `mask-reveal-up`, built in GSAP (`kinetic-type.md`). It is not a HyperFrames registry block.
- One named spectacle (`motion-design.md`). One primary seam and at most two accents (`transitions.md`).
- `brand-qa.md` and the six scores before a delivery render.
- HyperFrames skills on for the whole job. Remotion only when type locks to speech.

## Skeleton (fill this before the build)

Paste into the HyperFrames prompt. Six parts. Quote the copy. Timestamps come from the storyboard.

```
/hyperframes
Skills on. Do not set HYPERFRAMES_SKIP_SKILLS.

Spec: 45s 1920x1080 client sizzle, 16:9 first. Brand: <brand.json>.

Beats:
- 0.0–2.4 OPEN — <picture>. Words: "<LINE>". Recipe: mask-reveal-up (implement in GSAP).
- <t0>–<t1> <BEAT> — <picture from a real select>. Words: "<LINE>" | none.
- Spectacle (name one shot or drop it): <id> <what happens> <when it settles>.
- Breather (name one): <id>.

Copy: "<every on-screen line, quoted>".

Technique: hard cut on most seams. One accent: whip-pan. House recipes only — do not ask for a block named mask-reveal-up. If speech is on screen, one caption block for the section (caption-editorial-emphasis or caption-clip-wipe).

Negatives: no fade-card titles, no grey selects, no invented UI, no corner labels, no frame borders, no glitch default, no Flashtalk, no interview TEMP, no paid gen, no HYPERFRAMES_SKIP_SKILLS.
```

Speech-locked type uses Remotion instead of `/hyperframes`, same six parts, `useCurrentFrame` + `spring` (`remotion.md`).

## When this route wins
- Multi-beat script with named talent, partners, or event footage
- Real photos or video already exist
- The cut should feel like a client film, not grey cards
- Length typically 30–60s, 16:9 (export 9:16 after lock)

Do not open Fal, Higgsfield, or Flashtalk while this lane is open unless the user explicitly pivots.

## Beat map (default)
Fill every beat with real media before polish. Skip none.

1. **Open** — logos / title sting (hook in ≤3s)
2. **Studio / talent** — named people or spaces from selects
3. **Expand** — world / IP / product language (type + B-roll)
4. **Power / conversation** — real interview or dialogue only when the brief already has that audio. Do not invent an interview TEMP. Music can duck.
5. **Takeover montage** — fast cuts: event, stage, animation, game, product
6. **End card** — lockup line + even logo row (partners)

Customize beat names to the brief; keep the “no skipped beats” rule.

## Storyboard first
Copy `examples/storyboard/storyboard.json` and `storyboard.html`. Swap beats, words, and sources. Keep HAVE / ID / NEED / TEMP. Show the HTML before a long render. The edit reads the JSON. Do not invent shots that are not on the board (`storyboard.md`).

## Selects ingest
1. Scout small files first (phone/iPad, Day-Of MP4s/PNGs). Defer multi‑GB camera originals until selects exist.
2. Stage into `assets/footage/` as short **loops** (2–6s) and **stills**; name by beat (`loop-studio-*.mp4`, `talent-*.jpg`).
3. Build a shot list: beat → asset path → in/out → on-screen text → VO/captions.
4. Prefer real media over placeholders. If a beat is missing media, mark **TBD in NOTES only** — never ship grey “FOOTAGE TBD” cards in a client draft.

## Engines
| Engine | Use when |
|---|---|
| **HyperFrames + GSAP** | Default for client sizzle: custom kinetic, overlays, logo grids, page-like comps |
| **Remotion** | Speech-locked kinetic type, word timings, data-driven or series comps — see `remotion.md` |

Default engine is HyperFrames. Load `/hyperframes` before writing the comp (`hyperframes.md`). Never set `HYPERFRAMES_SKIP_SKILLS`. Remotion (`remotion.md`) only when words lock to speech. Do not add a third renderer.

Type moves: `kinetic-type.md`. Seams: `transitions.md`. Speech on screen: `captions.md`. Bans and the spectacle: `motion-design.md`.

## Kinetic type
Implement `mask-reveal-up` unless the storyboard names another house recipe. One display face, one UI face, one accent. No overshoot on display type. Real screenshots and the real logo. Zero typos (`brand-qa.md`). Score hook / phone / motion / variety / brand / sound before a delivery render.

## Brand / logo QA (hard gate before delivery)
- Follow the brief’s logo rules exactly (e.g. which mark on light vs dark).
- Even end-card row: equal optical size, consistent gaps, no random plates behind marks unless brief requires.
- Snapshot frames at open / power / takeover / end; Read them before sending.
- See also `brand-qa.md`.

## Audio
- Music bed on a beat grid (`beats.py`); duck under interview/VO.
- Prefer real interview audio when present; captions speech-locked.
- Free local VO (Kokoro) only when the brief allows; never substitute robotic TTS for a hero interview line without approval.
- Loudness: ~−14 LUFS, ≤ −1 dBTP.

## Workflow
1. Read brief + brand rules; list every beat.
2. Ingest selects → shot list (no grey cards).
3. Plan approval: duration, aspects, music, VO vs interview audio, logo set.
4. Build HyperFrames or Remotion comp with skills **on**.
5. Draft render → `review.py check` + manual brand QA snapshots. Fill the kinetic scores in `review.md` before a delivery render.
6. Fix → user yes → delivery render + export presets.
7. Deliver MP4 + timecoded shot list + note which beats used real media.

## Anti-patterns (learned)
The fail list at the top of this file is the bar. These two are easy to miss beside it:
- The wrong logo variant, or a plate the brief forbids
- A typo in on-screen type
