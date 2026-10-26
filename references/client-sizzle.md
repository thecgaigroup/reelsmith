---
description: Load first for an awards, partner, or client sizzle from real footage (about 30–60s). Holds the density-and-type bar, the anti-patterns, and the six-part skeleton. Then load storyboard.md (BRIEF), kinetic-type.md, transitions.md, motion-design.md (taste numbers), music.md (cue sheet), hyperframes.md, and brand-qa.md. Remotion only when type locks to speech.
---

# Client sizzle (footage-first editorial)

Awards, partner, or brand sizzle from real selects. Not a product-launch template. Not an AI talk-head.

## Bar

Match a denser cut than the last Reelsmith pass on this kind of brief. That cut won on **real footage density** and **kinetic type**. The weak pass lost because skills were skipped, selects were thin, type was a fade card, and the job drifted into an interview TEMP. Rights did not force that. Do not treat the current sizzle as already at that bar.

Fail the draft if you see any of these:

- `HYPERFRAMES_SKIP_SKILLS=1`, or a comp written before `/hyperframes` is loaded
- One still per beat, or a grey card, when phone / iPad / Day-Of selects exist
- Centered gradient title card, or a free fade as the whole idea
- Invented UI, or a Flashtalk / interview TEMP the user did not ask for
- Paid image or video generation used to fill a hole

Do these instead:

- Several real pictures per beat. A new picture or a new type event every 2–4s.
- Storyboard first (`storyboard.md`, copy `examples/storyboard/`). HAVE plays. ID waits. NEED and TEMP stay out of the client draft unless labelled.
- Default type is house recipe `mask-reveal-up`, built in GSAP (`kinetic-type.md`). It is not a HyperFrames registry block.
- One named spectacle (`motion-design.md`). One primary seam and at most two accents (`transitions.md`). Taste numbers (timing, easing, choreography) live in that same file.
- Cues on `b(n)`, the same clock as the picture (`music.md`).
- Frame-numbered BRIEF, then stills, then a fresh reviewer to 8+ (`storyboard.md`, `brand-qa.md`).
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

Technique: hard cut on most seams. One accent: whip-pan. House recipes only — do not ask for a block named mask-reveal-up. Timing from motion-design.md. If speech is on screen, one caption block for the section (caption-editorial-emphasis or caption-clip-wipe).

BRIEF: one line per shot, f{frame}–f{frame} at the render fps (storyboard.md). Cues on b(n), same clock as the picture (music.md).

Negatives: no centered gradient title cards, no free fades, no grey selects, no invented UI, no corner labels, no frame borders, no glitch default, no Flashtalk, no interview TEMP, no paid gen, no HYPERFRAMES_SKIP_SKILLS.
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

Type moves: `kinetic-type.md`. Seams: `transitions.md`. Taste numbers and bans: `motion-design.md`. Cues: `music.md`. Speech on screen: `captions.md`. Gate: `brand-qa.md`.

## Kinetic type
Implement `mask-reveal-up` unless the storyboard names another house recipe. One display face, one UI face, one accent. No overshoot on display type. Real screenshots and the real logo. Zero typos (`brand-qa.md`). Score hook / phone / motion / variety / brand / sound before a delivery render.

## Brand / logo QA (hard gate before delivery)
- Follow the brief’s logo rules exactly (e.g. which mark on light vs dark).
- Even end-card row: equal optical size, consistent gaps, no random plates behind marks unless brief requires. That row is the end-card default. `poster-grid` is optional, and only when the storyboard names it (`kinetic-type.md`).
- Snapshot frames at open / power / takeover / end; Read them before sending.
- See also `brand-qa.md`.

## Audio
- Music bed on a beat grid (`beats.py`); duck under interview/VO.
- Cue sheet on that same grid (`music.md`). One impact, one riser. Idle stays quiet.
- Prefer real interview audio when present; captions speech-locked.
- Free local VO (Kokoro) only when the brief allows; never substitute robotic TTS for a hero interview line without approval.
- Loudness: ~−14 LUFS, ≤ −1 dBTP.

A product beat inside this film uses the house launch recipes (`templates.md`): real UI in a device, cursor as a function of time, bar-accurate cuts. The sizzle primary seam stays a hard cut.

## Workflow
1. Read brief + brand rules; list every beat.
2. Ingest selects → shot list (no grey cards).
3. Plan approval: duration, aspects, music, VO vs interview audio, logo set.
4. Build HyperFrames or Remotion comp with skills **on**.
5. Draft render → `review.py check` + manual brand QA snapshots. Fill the kinetic scores in `review.md` before a delivery render.
6. Fix → user yes → delivery render + export presets.
7. Deliver MP4 + timecoded shot list + note which beats used real media.

## Effort (one brand per session)

| Tier | When | Stop when |
|---|---|---|
| A. Lock | First session on this brand | BRIEF is filled, key-frame stills are Read, six scores exist. Do not open a second brand in this session. |
| B. Worst three | Any score is under 8 | Fix only those three. Re-snapshot those frames. Score again. |
| C. Campaign | The master is 8+ and the user wants more cuts | Same picture. Two hooks × three formats (`remotion.md`). Do not redesign. |

HyperFrames skills stay on at every tier. Never `HYPERFRAMES_SKIP_SKILLS`.

## Anti-patterns (learned)
The fail list at the top of this file is the bar. These two are easy to miss beside it:
- The wrong logo variant, or a plate the brief forbids
- A typo in on-screen type
