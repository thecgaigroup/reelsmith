---
description: Load before a client draft leaves the box. BRIEF frame stills first, then review.py contact.jpg and phone.jpg. Fresh reviewer, worst three, scores to 8+. Fails skills-skipped animatics, gradient title cards, free fades, invented UI, sparse selects, and interview-TEMP drift.
---

# Brand QA gate (client video)

Run before any client draft leaves the box. Fail = do not send.

## BRIEF frames

The storyboard is the BRIEF (`storyboard.md`). Before trusting playback, snapshot every shot at its frame numbers and Read the PNGs. HyperFrames: `$HF snapshot --at` with those times. Remotion: `npx remotion still <id> out/f.png --frame=N`. Then run `review.py check` so `contact.jpg` and `phone.jpg` exist. A moving preview does not replace the stills. Seek the same `t` twice before you call a frame done (`motion-design.md`). Pixels match, including a seek that jumps backwards.

## Fresh reviewer

The author of the comp does not grade it. A second pass scores from the stills alone, without the author's intent. Score 1–10: hook, phone, motion, variety, brand, sound. Fix the three worst. Re-snapshot those frames and score again. Do not send a client draft while any score is under 8. `review.py` prints the table. You still fill it.

## Checklist
1. **Typography** — zero typos; high contrast; tight tracking on display; no clipped glyphs.
2. **Logo variants** — correct mark for light vs dark backgrounds per brief; never the forbidden variant.
3. **Logo plates** — no ad-hoc solid plates behind logos unless the brief requires them.
4. **End-card grid** — even optical sizes, equal gaps, single row/grid; all required partners present.
5. **Safe zones** — key type/faces inside platform safe areas (`platform-specs.md`).
6. **Flash / accessibility** — ≤3 flashes/s; captions on speech.
7. **AI disclosure** — only when AI faces/voices/gen media are in the cut; not required for licensed real footage alone.
8. **Contact sheet** — snapshot open, mid (power/talent), takeover, end; Read PNGs before delivery.
9. **Kinetic type** — showreel rules in `motion-design.md`: one display face, one UI face, one accent; mask/stagger; no overshoot on display type; something new every 2–4s. Fail the ban list: centered gradient title cards, free fades, invented product UI, corner labels, frame borders, glow on UI chrome, generic particle bursts, blurry scaled text.
10. **Scores before full render** — fresh reviewer, stills first, then `contact.jpg` and `phone.jpg`. Six scores, worst three, each at 8 or higher before a delivery render.
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
