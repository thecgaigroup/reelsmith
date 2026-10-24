# Storyboard (client sizzle source of truth)

For awards / partner / client sizzles, build a **storyboard before the edit**.
Marc’s Clio Unhinged board (`storyboard.py` → `storyboard.json` + `storyboard.html`) is the craft bar:
dark film-room HTML, proportional timeline, PDF-beat alignment, shot cards with thumbs, HAVE/ID/NEED/TEMP status, production bible.

## Why
Grey animatic cards and mid-job talk-head pivots happen when there is no shot-level source of truth.
The storyboard is what the edit builder and humans both read.

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
4. **On-screen words** — kinetic / lower-third / none
5. **Voice** — narrator / interview / mute
6. **Audio** — music / duck / SFX
7. **Story intent** — one line
8. **Status** — `HAVE` \| `ID` (identity confirm) \| `NEED` \| `TEMP` (placeholder by design)

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
