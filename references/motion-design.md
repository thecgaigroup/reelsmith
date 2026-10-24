# Motion design rules

Distilled from the HyperFrames motion guide, classic animation principles, and platform best practices.
The templates already follow these rules. Apply them to custom work too.

1. **Nothing fully stops.** Every hold has slow drift (scale 1.00 -> 1.03, background parallax). A frozen last
   second reads as a bug; end on motion or a deliberate logo settle.
2. **The camera is an actor.** Push in to focus attention (screenshots: zoom 1.4-2.0x onto the target), pull out to
   reveal. One move per idea, eased (`power2.inOut`/`power3.out`).
3. **Overlap.** Stagger entrances (60-90 ms per word or item); the next element starts before the last one lands.
4. **Overshoot, then settle.** Small `back.out(1.4)` on key words, logos and numbers; not on body text.
5. **Depth.** Foreground type, a mid-ground card, a soft blurred background; blur and scale on exits.
6. **Pace by genre.**
   | Genre | Seconds per idea | Cut on |
   |---|---|---|
   | Sizzle / teaser | 1.5-3 | every beat or bar |
   | Promo / launch | 2-4 | bars |
   | Explainer / how-to | 4-8 (VO-led) | sentences |
   | Kiosk loop / slides | 5-8 | slide change |
7. **Hook in the first 1-3 s:** motion + the strongest words. Logo and CTA last, held at least 2 s.
8. **Readability:** about 0.3 s per word plus 1 s; 2-6 words per kinetic card; one idea per screen.
9. **Consistency:** one ease family, one transition style per piece, from `brand.motion.energy`
   (low = fades/slides, medium = slides + scale, high = whip, blur, slam).
10. **Vertical:** larger type (about 1.3x), centered, inside the safe area (keep clear of the top 13% and bottom
    32% in Reels/TikTok UI); captions above the UI band; never put key content behind the like/comment rail.
11. **Beat sync:** cut on downbeats, hit accents on the beat; transitions are half a beat long. Music starts at its
    first downbeat (`beats.py grid`).
12. **Flash-safe:** no more than 3 flashes per second; animate scale, blur and opacity instead of luminance flips.
13. **Engine rules:** animate only transforms and opacity (GPU-cheap, deterministic); seekable timelines only (no
    random values, timers or CSS animations).

## Kinetic typography (client bar)
Distilled for awards/partner sizzles (see also `client-sizzle.md`).

1. Lock static type before motion (line-height ~1.1–1.2 display, tracking −1% to −3%).
2. Split granularity: line (premium) → word (energetic taglines) → character (short hits only).
3. Prefer **mask/clip reveals** over blur-heavy stacks; stagger words 40–70ms, lines 60–100ms.
4. Ease-out expo feel (`power3.out` / cubic-bezier(0.16,1,0.3,1)); cap a reveal near ~800ms.
5. Accent color from brand on speech-locked keywords; rest of line stays readable white/cream on dark.
6. Never ship typo’d kinetic — run `brand-qa.md` denylist before render.
