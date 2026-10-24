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

## Commands
```bash
# HyperFrames
npx hyperframes@0.8.188 snapshot --at 1,12,28,42
# Reelsmith review
python3 scripts/review.py check VIDEO --out OUT/_review --preset youtube --job OUT/job.json
```

## Typo denylist (extend per job)
STUIO→STUDIO, POSSIBLITY→POSSIBILITY, performace→performance, untill→until, teh→the
