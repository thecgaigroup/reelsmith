---
description: Load before a client draft leaves the box, after review.py contact.jpg and phone.jpg exist. Fails skills-skipped animatics, fade-card type, sparse selects, and interview-TEMP drift.
---

# Brand QA gate (client video)

Run before any client draft leaves the box. Fail = do not send.

## Checklist
1. **Typography** — zero typos; high contrast; tight tracking on display; no clipped glyphs.
2. **Logo variants** — correct mark for light vs dark backgrounds per brief; never the forbidden variant.
3. **Logo plates** — no ad-hoc solid plates behind logos unless the brief requires them.
4. **End-card grid** — even optical sizes, equal gaps, single row/grid; all required partners present.
5. **Safe zones** — key type/faces inside platform safe areas (`platform-specs.md`).
6. **Flash / accessibility** — ≤3 flashes/s; captions on speech.
7. **AI disclosure** — only when AI faces/voices/gen media are in the cut; not required for licensed real footage alone.
8. **Contact sheet** — snapshot open, mid (power/talent), takeover, end; Read PNGs before delivery.
9. **Kinetic type** — showreel rules in `motion-design.md`: one display face, one UI face, one accent; mask/stagger; no overshoot on display type; something new every 2–4s. Fail banned defaults (centered title on a gradient, everything fading in, corner labels, frame borders, glow on UI chrome, generic particle bursts, blurry scaled text, invented UI).
10. **Scores before full render** — after looking at the contact sheet and `phone.jpg`, score 1–10: hook, phone, motion, variety, brand, sound. Fix the three worst. Do not send a client draft while any score is under 8. `review.py` prints the table; you still have to fill it.
11. **Comparison bar** — the cut is dense real footage plus kinetic type (`client-sizzle.md`). Fail a skills-skipped animatic, a fade-card title, a sparse select when footage exists, or an interview TEMP / Flashtalk drift the user did not ask for.

## Commands
```bash
# HyperFrames
npx hyperframes@0.8.188 snapshot --at 1,12,28,42
# Reelsmith review
python3 scripts/review.py check VIDEO --out OUT/_review --preset youtube --job OUT/job.json
```

## Typo denylist (extend per job)
STUIO→STUDIO, POSSIBLITY→POSSIBILITY, performace→performance, untill→until, teh→the
