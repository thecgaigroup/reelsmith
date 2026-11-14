# Signal Shorts Explainer Format

<!-- Adapted from codepawl/creator-generalist (MIT), commit d3ab529a, read 2026-11-14 -->

A 9:16, ~55-second editorial explainer format for Signal Shorts, inspired by Vox's measured 2018–2026 style: flat paper cards, print-bordered real photos, highlighters, maps, charts, and true-scale timelines. This format sits **alongside** the existing Signal Short product-launch style as an option, not a replacement.

**Brand anchors stay:** Signal badges, burned captions, end card, and blog hero art remain as specified in Reelsmith's existing references. This format adds the **explainer visual grammar** to that foundation.

## When to use

- An educational or how-it-works piece (not a product launch)
- Content where charts, maps, timelines, or archival photos carry the story
- Pieces where credibility and clarity matter more than kinetic energy

For launch reels and product drops, use the existing `product-launch` template. For dense footage with kinetic type, use `client-sizzle.md`.

## Core visual laws (measured from Vox 2018–2026)

1. **Real Pictures, Never Redrawn**
   - Every real-world thing (vehicle, person, place, product, document, logo) is a **real photo or scan** found online, never redrawn from SVG shapes.
   - Measured Vox shows archival photos as plain black-and-white scans. Duotone, halftone, and torn edges are **stylized options**, not the default Vox look.
   - Draw only arrows, rulers, charts, and abstract ideas with no existing picture.

2. **Flat Paper, Real Documents**
   - Graphic cards are flat near-white with **no grain** by default (measured `#F9F9F6`, `#F9F8EB`, `#F1ECE6`; grey bed `#D1D1D1`).
   - Pure white reserved for real web pages and documents.
   - Dark maps use deep desaturated slate or navy.

3. **Print Borders, Not Torn**
   - A cut-out photo gets a thin straight **white print border** (a few pixels), a 2–8 degree tilt, and a faint shadow.
   - **No torn edge** was seen in six measured Vox videos (2018–2026). The two-pass torn border technique is a stylized option only.

4. **No Added Halftone**
   - Halftone appears only **inside scanned newspaper photos**, as part of the source.
   - Do not lay a halftone or duotone over photos for a Vox look. That is a stylized option.

5. **Pre-Drawn Ruler Timeline Law**
   - Never space unequal time intervals evenly.
   - Draw an evenly spaced ruler/tick scale **first**, then place events at their true proportional coordinates so clusters and gaps tell the story.

6. **Dual Highlighter Law**
   - **Digital/screen text:** Clean `#FFE600` stroke (no wobble), `Multiply` blend mode, stroke band **135–150% of cap height**.
   - **Archival/book page:** Three-pass roughened edges (horizontal marker streaks + border + rough edge) + `Bulge` turbulent displacement, placed in 3D space with a `35mm` camera and shallow depth of field tracking the line.
   - Other text is **never dimmed**.

7. **No Stiff Repeats**
   - No two neighboring elements with the same size, angle, and timing.
   - Stagger entrances by 2–6 frames and vary scale ±10%.
   - **Holds are still** (measured Vox: 0.00–0.03 of 255 luma change per 0.125 s). No boil or wobble by default.
   - 2–4 fps boil, Roughen Edges, and slight rotation apply only when the look is explicitly stylized.

8. **Camera Speed Graph** (when camera moves)
   - All 2D/3D camera pans and zooms use a **35mm focal length** equivalent, Null controller parenting, and a **Continuous Bezier bell-curve** speed graph (slow ease-in → fast snap → slow settle), never linear keyframes.
   - Exception: infinite zoom is exponential scale, so zoom speed looks constant.

## Structure (30–90 seconds)

Adapted from `explainer-script.md` in creator-generalist:

1. **Hook (0–3 s):** The question or the wrong belief, with the picture already moving.
2. **Stakes (3–10 s):** Why it matters, one concrete number or image.
3. **Context (two steps):** Minimum background, each step one picture (a map, a chart, a document).
4. **Turn:** The surprising fact that breaks the expected answer. Hold it a beat longer.
5. **Answer:** The mechanism, shown in at most three steps.
6. **Kicker:** A last fact or image that sends the viewer back to the start or to the comments.

Every line adds a fact, a reason, or a surprise. Cut lines that only describe what is on screen.

## Voice and pace

- **2.6–3.0 words per second** (slower than a typical Short's 3.4–3.6), so a viewer can absorb a map or chart while it speaks.
- Write for the ear: short sentences, one number per sentence, round numbers when the exact one adds nothing.
- Every factual claim has a source.

## Visual hierarchy and asymmetric scale

From creator-generalist `vox-psychology-and-design.md`:

1. **One huge anchor:** Pick 1 element that carries the main message. Scale it up so it clearly dominates, and place it off-centre.
2. **A tiny secondary element:** Shrink the element it is compared with. This creates visual tension.
3. **Generous negative space:** Keep 45–65% of the frame as empty textured paper background.
4. **Connecting path:** Use a stroke line, dashed line, or ruler axis to connect the large anchor to the small element.

### The Look-Away / Look-Back Test

Before animating, export the still frame. Look away for 3 seconds, then look back:
- Where does the eye land first?
- Where does the eye move second?

Animate only when the eye follows the story order while the picture is **still**.

## QA gates

Before sending the preview:

1. **Look match:** Run `scripts/compare_look.py --style styleframes/picked.png <frames...>` to check that rendered frames stay inside the luma, saturation, and hue band of the approved style frame.
2. **Beat table check:** Every beat (line of VO) must have a new picture within 1.5 seconds. A beat with no visual change fails the dead-air gate.
3. **Show-before-tell:** The picture lands 4–8 frames **before** the word it shows.
4. **Caption sync:** Burned-in captions synced to voice within 0.05 s.
5. **Safe zone:** Text and faces inside the safe zone (see `platform-specs.md`).

## Differences from the existing Signal Short style

| Aspect | Existing Signal Short (product-launch) | Signal Shorts Explainer (this format) |
|---|---|---|
| **Pace** | Fast, music-led, 2.5 words/s | Slower, 2.6–3.0 words/s to absorb charts/maps |
| **Visual style** | Kinetic type, dense motion, brand colors | Flat paper cards, real photos, charts, timelines |
| **Music** | Beat-synced to cuts and transitions | Present but supporting, not driving |
| **Captions** | Burned brand style | Burned, synced to speech within 0.05 s |
| **Use case** | Launch, feature drop, promo | Educational, how-it-works, historical/data story |

Both formats keep Signal badges, burned captions, end card, and blog hero art.

## Tools and references

- **Maps:** Real geodata (OpenStreetMap, Natural Earth) rendered in QGIS, Blender, or code
- **Charts/timelines:** Pre-drawn with true scale (see Pre-Drawn Ruler Timeline Law)
- **Photos:** Archival photos and scans found online, never redrawn
- **Rendering:** Remotion, Blender Grease Pencil, or DaVinci Resolve Fusion (`ImagePlane3D`, `Camera3D`)
- **QA:** `scripts/compare_look.py` (deterministic luma/saturation/hue check)

## Notes

- This format is an **option**, not a replacement. Use it when the content calls for it.
- **Reconcile with existing Signal style:** Signal badges, burned captions, end card, and blog hero art stay. This format adds the explainer grammar on top of that foundation.
- If Reelsmith's loudness numbers conflict with creator-generalist's platform targets, **keep Reelsmith's numbers** (see `loudness-accessibility.md` and `platform-specs.md`).

---

**Source:** Adapted from [codepawl/creator-generalist](https://github.com/codepawl/creator-generalist) (MIT), commit d3ab529a1270217f70666f0566af3110a9e4f74d, read 2026-11-14. See `THIRD_PARTY_NOTICES.md` for full license.
