# Client sizzle (footage-first editorial)

Use this when the job is an **awards / partner / brand sizzle** built from real selects — not a product-launch template and not an AI talk-head mock.

## When this route wins
- Multi-beat script with named talent, partners, or event footage
- Real photos/video already exist (Drive, vault, Day-Of, phone/iPad rips)
- Target feels like a **client cut**, not a boardomatic of grey cards
- Length typically 30–60s, 16:9 (also export 9:16 after lock)

Do **not** divert to Fal/Higgsfield talk-heads, Flashtalk, or fictional lookalikes while this lane is open unless the user explicitly pivots.

## Comparison bar

On the same awards brief, the Claude cut is the quality bar. It won on **dense real footage** and **kinetic type**. Reelsmith on that pass did not match it. Rights did not force the weaker cut. Execution did: HyperFrames skills were skipped, selects were thin, type was fade cards, and the job drifted into an interview TEMP the brief did not ask for. Treat that Claude cut as the bar to reach. Do not describe the current sizzle as already there.

What closed the gap on the stronger cut, and what this lane now requires:

- Several real pictures per beat (phone, iPad, Day-Of), a new picture or a new type event every 2–4 s.
- Named recipes (`kinetic-type.md`), client default mask/clip. Not a centered fade on a gradient.
- Skills on for the whole job. Never `HYPERFRAMES_SKIP_SKILLS=1`.
- A storyboard that tells the truth (`examples/storyboard/`): HAVE plays, ID waits, NEED and TEMP stay out of the client draft unless they are labelled.
- One spectacle beat, written down (`motion-design.md`). One primary seam plus at most two accents (`transitions.md`).
- brand-qa and the six scores before a delivery render.
- Paid image/video generation stays hold (`ai-generation.md`). Do not thicken a thin select with a generated face or a fake UI.

## One-shot skeleton

Write this before the build. Source: [HyperFrames anatomy](https://hyperframes.heygen.com/prompting/anatomy). Six parts, all filled from the storyboard:

1. **Route** — client-sizzle. `/hyperframes` with skills on, or Remotion when type locks to speech.
2. **Spec** — length (often ~45 s), 16:9 first, brand, aspects.
3. **Beats** — timestamps from the board. Include the breather and the spectacle.
4. **Copy** — on-screen lines quoted. Unquoted lines get paraphrased.
5. **Technique** — recipe id, spring preset, seam, caption block if speech is on screen.
6. **Negatives** — fade-card type, grey selects, invented UI, corner labels, glitch-by-default, Flashtalk / interview TEMP, `HYPERFRAMES_SKIP_SKILLS`, paid gen.

## Beat map (default)
Fill every beat with real media before polish. Skip none.

1. **Open** — logos / title sting (hook in ≤3s)
2. **Studio / talent** — named people or spaces from selects
3. **Expand** — world / IP / product language (type + B-roll)
4. **Power / conversation** — interview or dialogue; music can duck
5. **Takeover montage** — fast cuts: event, stage, animation, game, product
6. **End card** — lockup line + even logo row (partners)

Customize beat names to the brief; keep the “no skipped beats” rule.

## Storyboard first
Read **storyboard.md**. Author `storyboard.py` → `storyboard.json` + `storyboard.html` (timeline + shot cards + HAVE/ID/NEED/TEMP) and get user eyes on the HTML **before** a long render. The edit builder reads the JSON; do not invent off-board shots.

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

Both stay on the existing render paths. Do not add a raw `seek(t)` browser renderer. Full type recipe: `motion-design.md` and `kinetic-type.md`. Seams: `transitions.md`. Captions in-comp: `captions.md`.

**Never set `HYPERFRAMES_SKIP_SKILLS=1` on client sizzle work.** Read the project `AGENTS.md` / `CLAUDE.md` skill tree (`/hyperframes`, `/media-use`, treatments) before writing or rendering. For Remotion, install/use agent skills: `npx skills add remotion-dev/skills` and kinetic-typography patterns (split/stagger/mask, word lock to speech).

## Kinetic type (production-house bar)
Read **motion-design.md** (Showreel kinetic type) and apply it on this lane.
- Static type first: tracking, weight, contrast on dark.
- One display face (`fonts.heading`) + one UI face (`fonts.body`) + one accent, unless the brief names more.
- Split by **word** for taglines; by **line** for longer reads; character only for short hits.
- Mask/clip reveals + stagger (60–100ms lines, 40–70ms words). Do not fade the whole card in as the idea.
- No overshoot on display type or logo lockups. A hair of overshoot only on UI chrome. Motion is a pure function of time (paused GSAP timeline or Remotion frame).
- Something new every 2–4s. Hook in ≤3s. Lock the accent word to speech or a beat.
- 2–6 words per kinetic card; one idea per screen.
- Zero typos — run a denylist pass (common: STUDIO, POSSIBILITY, performance).
- Product or UI shots use real screenshots, the real logo, and brand colors. Never invent a UI. This craft does not unlock paid generation (`ai-generation.md`).
- Before a full render: contact sheet + `phone.jpg`. Score hook / phone / motion / variety / brand / sound, 1–10 (`brand-qa.md`). Fix the three worst. Do not delivery-render while any score is under 8.

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
- Shipping placeholder-heavy animatics when selects exist
- Skipping HyperFrames/Remotion skills to “go faster”
- Leaving the sizzle lane for AI talk-head TEMP without an explicit user pivot
- Blue/wrong logo variants or white plates when brief forbids them
- Typo’d kinetic type
- Centered title on a gradient, fade-in-everything, corner labels, frame borders, glow on UI chrome, particle bursts, blurry scaled text
- Redrawing a product UI instead of using the real screenshot, logo, and colors
- A full render before the contact-sheet scores are in
