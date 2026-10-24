# Client sizzle (footage-first editorial)

Use this when the job is an **awards / partner / brand sizzle** built from real selects — not a product-launch template and not an AI talk-head mock.

## When this route wins
- Multi-beat script with named talent, partners, or event footage
- Real photos/video already exist (Drive, vault, Day-Of, phone/iPad rips)
- Target feels like a **client cut**, not a boardomatic of grey cards
- Length typically 30–60s, 16:9 (also export 9:16 after lock)

Do **not** divert to Fal/Higgsfield talk-heads, Flashtalk, or fictional lookalikes while this lane is open unless the user explicitly pivots.

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
| **HyperFrames + GSAP** | Custom kinetic sizzle, overlays, logo grids (default for client sizzle) |
| **Remotion** | Speech-locked kinetic type, `KineticText`, beat-synced comps — see `remotion.md` |

**Never set `HYPERFRAMES_SKIP_SKILLS=1` on client sizzle work.** Read the project `AGENTS.md` / `CLAUDE.md` skill tree (`/hyperframes`, `/media-use`, treatments) before writing or rendering. For Remotion, install/use agent skills: `npx skills add remotion-dev/skills` and kinetic-typography patterns (split/stagger/mask, word lock to speech).

## Kinetic type (production-house bar)
- Static type first: tracking, weight, contrast on dark.
- Split by **word** for taglines; by **line** for longer reads; character only for short hits.
- Prefer mask/clip reveals + stagger (60–100ms lines, 40–70ms words).
- Lock highlights to speech or beat accents; one accent color from brand.
- Zero typos — run a denylist pass (common: STUDIO, POSSIBILITY, performance).
- 2–6 words per kinetic card; one idea per screen (`motion-design.md`).

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
5. Draft render → `review.py check` + manual brand QA snapshots.
6. Fix → user yes → delivery render + export presets.
7. Deliver MP4 + timecoded shot list + note which beats used real media.

## Anti-patterns (learned)
- Shipping placeholder-heavy animatics when selects exist
- Skipping HyperFrames/Remotion skills to “go faster”
- Leaving the sizzle lane for AI talk-head TEMP without an explicit user pivot
- Blue/wrong logo variants or white plates when brief forbids them
- Typo’d kinetic type
