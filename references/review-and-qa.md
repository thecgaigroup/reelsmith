# Review gate and QA

Nothing final ships, and nothing paid is generated, without a recorded user OK.

## Before spend or long renders: approve the plan
Show the shot list (scene, on-screen text, VO line, seconds, transition), the template/engine, the music and its
license, the voice (free or paid with a quote), and the aspects. Use `--dry-run` to print the resolved job
(`job.json`) without rendering. Attach one draft still if you can (`--draft` renders fast at lower quality).

## After the draft: review package
    review.py check out/x-9x16.mp4 --out out/_review --preset reels --job out/job.json --music-credits credits.json
Writes `preview.mp4` (low-res, timecoded), `contact.jpg`, `safe.jpg` (platform safe-zone overlay),
`scenes.jpg` (one labeled frame per scene), `phone.jpg` (frames at phone size: can you read it?), `review.md`
and `review.json`.

Automatic checks: resolution/fps/duration vs preset; loudness (integrated LUFS + true peak); black frames;
dead air; frozen stretches and frozen endings; photosensitive flashes (WCAG 2.3.1 heuristic: at most 3 per
second); scene timing vs job.json (each scene long enough to read).

The agent must also look at the images: clipped or overflowing text, literal `*`, overlaps (captions vs UI),
blank scenes, logo legibility, text inside safe zones, spelling of names and numbers, and credits present.

## Deterministic look match (optional)

For pieces with an approved style frame, run `scripts/compare_look.py` to check that rendered frames stay inside
the luma, saturation, and hue band of the picked look. This catches drift: shots rendered darker, greyer, or in
another color cast. It does not judge composition or taste.

```bash
python3 scripts/compare_look.py --style styleframes/picked.png out/frames/*.png \
    [--luma-band 20] [--saturation-band 0.08] [--hue-shift 20] [--json report.json]
```

Exit code 0 = all frames pass, 1 = one or more fail, 2 = cannot read. Default bands: luma ±20 (0-255),
saturation ±0.08 (0-1), hue shift ≤20°. Adjust thresholds when the style is intentionally varied (e.g., day/night).

## Motion audit (static, before the first draft render)

Read the composition source before you spend a render on it. No render, no network, no browser.

```bash
python3 scripts/review.py audit path/to/comp [--json audit.json]   # a folder or one file
```

It reads `.html`, `.js`, `.ts(x)`, `.jsx` and `.css` under the folder, skipping `node_modules`, build output and `*.min.*` vendored bundles. Comments are ignored.

| Level | Rule | Why |
|---|---|---|
| FAIL | `random` — `Math.random()`, `getRandomValues()` | A seek to the same time paints different pixels |
| FAIL | `clock` — `Date.now()`, `new Date()`, `performance.now()` | Wall-clock time is not timeline time |
| FAIL | `timer` — `setTimeout`, `setInterval`, `requestAnimationFrame` | Motion outside the paused timeline or the frame |
| FAIL | `css-motion` — `@keyframes`, `animation:`, `transition:` (`none` is fine) | Not seekable; Remotion does not render it |
| WARN | `will-change` | Soft scaled glyphs; it has broken seek determinism |
| WARN | `layout-tween` — a `.to/.from/.fromTo` on width, height, top, left, margin or padding | Layout work every frame; move with x, y, scale or clip-path |
| WARN | `linear-move` — an entrance or exit (position plus opacity) on `ease: "none"` | Entrances ease out, exits ease in (`motion-design.md`). A cut-to-cut drift with no fade is not flagged |

- **Worst level wins** per file and for the run. Exit 1 on any FAIL, else 0. Clean files collapse to one PASS line, so a long report means real findings.
- **Each finding** names the rule, the file and line, what is wrong, and the fix.
- **Intended exceptions** (the one-shape morph in `templates.md` tweens width and height) get `audit-ok` and a reason on that line. Never mark a FAIL `audit-ok` to get a render out.
- **Limits:** text patterns, not a parser. It misses motion built from strings or spread across helper files it cannot follow, and it does not judge taste, timing or overshoot. HyperFrames `lint` and `check` still run; the stills and scores still decide.

*Source: the audit shape — one level per animation with the worst one winning, a concrete fix per finding, and no padding when a file is clean — after motiondivision/ai-kit (MIT, github.com/motiondivision/ai-kit @1e42494), `plugins/motion/agents/motion-reviewer.md`. Its scoring method is a paid server resource and was not used. The rules are Reelsmith's own engine rules (`hyperframes.md`, `motion-design.md`). Tests: `scripts/test_motion_audit.py`.*

## Kinetic type, before the full render
For client sizzle and hand-authored kinetic pieces, pull stills at the BRIEF frame numbers (`storyboard.md`)
**before** you trust playback. HyperFrames and OpenMotion: `$HF snapshot --at` (each with its own pinned CLI). Remotion: `npx remotion still --frame=N`.
Then look at `contact.jpg` and `phone.jpg`. `review.md` includes a 1–10 table: hook, phone, motion,
variety, brand, sound. Score it as a fresh reviewer, from the stills, not from memory of the comp.
Fix the three worst scores and re-check until each is 8 or higher. Rules and
banned defaults: `motion-design.md`. Gate: `brand-qa.md`. The table does not change `review.py` pass/fail. The 1–5 rubric below
stays for every job. Template cuts can leave the kinetic table blank.

## Sound on the cut

For a designed hit, score sound from the cue sheet. Check the sync tap, the bed-relative level, and the density (`music.md`, Measured SFX check). `review.py` still measures integrated LUFS and true peak on the encoded file. Fix the first failed row before you re-render the film. This check is separate from the visual critic below and from the SageCut ladder.

## Independent critic

When a prior report exists, the fresh reviewer marks each finding FIXED, PARTLY, or STILL PRESENT and adds one ledger row. Prompts, the stop rule, and the client checks that follow a clear score are in `brand-qa.md`. SageCut stays off. Do not require `SAGE_API_KEY`. Do not install a critic tool.

## Optional SageCut (off)

Not this gate. The measurement ladder, `gate --no-sage` (local measurements, zero API), and the hold on Sage and Opus spend are in `brand-qa.md`. SageCut 0.3 does not support camera footage. Client sizzle and live footage stay on the BRIEF stills and `review.py`. Do not require `SAGE_API_KEY`. Do not install the plugin.

## One-frame pop scan

A **pop** is a single anomalous frame — a swap, reset, or flash that the viewer sees but cannot name. Most pops are rendering errors or poorly timed cuts, not intentional hits.

**How to find them:**
Frame `i` is a pop when it differs strongly from BOTH frame `i-1` and frame `i+1` (large mean absolute pixel difference), while frames `i-1` and `i+1` are similar to each other (small difference). This naturally ignores real cuts (where the change persists) and held frames (where nothing changes).

Check flagged frames manually: a hit you meant (a bolt, a key press, a beat-synced impact) has sound on that frame and is documented on the storyboard. Keep those. Fix the rest before anyone watches the cut.

**Method (implemented in `review.py`):**
For each frame `i`, measure how much it differs from frame `i-1` and from frame `i+1`. Also measure how much frames `i-1` and `i+1` differ from each other. Flag frame `i` as a pop if both of its changes exceed a threshold while its neighbors' difference is small relative to those changes (less than 1/4 of the average pop change).

*Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525)*

## Cut list and clicks at cuts

`review.py check` writes `cuts.json` and two rows. Neither is a FAIL.

- **Cut list (INFO).** Every place the picture jumps, classified: `cut` (a new shot), `flash` (the picture comes back within four frames: a white flash or a one-frame hit), `fast` (a whip or a fast camera move inside one shot: the frame before, zoomed or shifted, nearly gives the frame after) or `transition` (a change spread over more than three frames: dissolve, wipe, flash-fade). It catches punch-ins that ffmpeg's scene score misses. Use the count as cuts per minute in a take-apart dossier (`storyboard.md`), and as a check that your film has the cuts the storyboard names and no others.
- **Clicks at cuts (WARN).** At each `cut`, a hard audio edit leaves one sample-to-sample jump far larger than the jumps in the 2 ms around it. A drum hit on the beat rises over several milliseconds and is not flagged. Fix: a ~30 ms audio fade on each side of the edit (`afade=t=in:st=0:d=0.03`, `afade=t=out:st=<dur−0.03>:d=0.03` per segment), then check again.

**Limitations:** These are heuristics, not certifications. The cut detector may misclassify dissolves as cuts, miss cuts during very dark or bright sequences, or flag intentional motion as false cuts. The click detector may miss pops in dense mixes or flag legitimate transients. Always review the output; passing these checks does not guarantee the film has no defects. Use `contact.jpg` and frame strips for final verification.

`detect_pops` stays the one-frame check. The cut list answers a different question: where the shots change, and whether that change is a cut at all.

## Reading time per text block

Plan with rule 8 in `motion-design.md`. Check the built comp per block of on-screen text: time it from the first frame the whole block is inside the frame, and count only that first unbroken stretch. It passes at (characters ÷ 15) + 1.5 s, and never under 1.5 s; for Chinese, Japanese or Korean, count 4.5 characters per second. A block that never fully enters the frame never passes. New words under the same block restart the clock. A typewriter line is timed as the full line. Text nobody is meant to read in full (signage in a fly-through, fine print on the end card) is marked as a pass-by and not timed; anything the film needs read is never marked. Burned-in captions follow their own timing (`captions.md`).

*Source: the reading-time rule after lemomo-ai/lemo-opuscar (MIT, Copyright (c) 2026 Lemomo (LemoLab), github.com/lemomo-ai/lemo-opuscar @00a7f9e), `core/render/readcheck.mjs`. Our words; no code copied. Its docs (CC BY-NC 4.0) were not used.*

## Self-eval at every cut

Before anyone sees a cut made from footage, pull a strip of frames ±1.5 s around each `cut` in `cuts.json` (`ffmpeg -ss <t−1.5> -t 3 … tile`), plus the first 2 s, the last 2 s, and two or three mid-points. Look for: a jump or flash at the cut, a caption hidden under an overlay or cut mid-word, an overlay showing the wrong frames, and grade drift between neighbours. Read consecutive frames wherever something enters, leaves, or changes; a sheet sampled once a second misses 1–3-frame timing.

Fix, re-render, re-check. Stop after three self-eval passes. Whatever still fails goes to the user as a named list, not into a fourth loop.

*Sources: cut classification after heygen-com/hyperframes (Apache-2.0, github.com/heygen-com/hyperframes @d317abc), `packages/cli/src/measure/cuts.ts`, re-implemented in Python. Cut-boundary self-eval, the 30 ms fade, and the three-pass cap after browser-use/video-use (MIT, Copyright (c) 2026 Browser Use, github.com/browser-use/video-use @43cfc56), `SKILL.md`. See `THIRD_PARTY_NOTICES.md`.*

## Edit log (memory across sessions)

Every film folder keeps `EDIT_LOG.md`. At the start of a session, read it and say the last session in one sentence before you ask whether to carry on. At the end, append one section:

```markdown
## Session N · YYYY-MM-DD
**Strategy:** one paragraph: the approach this session.
**Decisions:** takes, cuts, grade, music, type, and why. Include what the user approved or turned down, in their words.
**Reasoning:** one line for each decision that is not obvious.
**Locked:** what must not change without asking (approved script, picture lock, LUFS target, disclosure text).
**Outstanding:** what is deferred, and what is waiting on whom.
```

Never re-transcribe or re-voice a source the log says is cached and unchanged. A decision the user turned down stays turned down in later sessions unless they reopen it. The log holds no keys, prices, or private paths that would not belong in the film folder.

*Source: the `project.md` memory pattern in browser-use/video-use (MIT, Copyright (c) 2026 Browser Use, github.com/browser-use/video-use @43cfc56), `SKILL.md`, adapted: we add **Locked** and the turned-down rule.*

## Approve
Send the user `preview.mp4` or the sheets plus `review.md`. Only when they say yes:
    review.py approve out/_review --by "user in chat"
    review.py status out/_review      # exit 0 only when approved
`export.py run` and `youtube_prep.py` refuse to run without an approved review. `--unreviewed` exists for internal
tests only.

## Iterate cheaply
VO is cached by text hash, so visual edits never re-voice. Fix -> `--draft` render -> `review.py check` again.
Re-approve after any change to the final cut.
