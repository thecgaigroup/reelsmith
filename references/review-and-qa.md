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

## Kinetic type, before the full render
For client sizzle and hand-authored kinetic pieces, pull stills at the BRIEF frame numbers (`storyboard.md`)
**before** you trust playback. HyperFrames: `$HF snapshot --at`. Remotion: `npx remotion still --frame=N`.
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

## Approve
Send the user `preview.mp4` or the sheets plus `review.md`. Only when they say yes:
    review.py approve out/_review --by "user in chat"
    review.py status out/_review      # exit 0 only when approved
`export.py run` and `youtube_prep.py` refuse to run without an approved review. `--unreviewed` exists for internal
tests only.

## Iterate cheaply
VO is cached by text hash, so visual edits never re-voice. Fix -> `--draft` render -> `review.py check` again.
Re-approve after any change to the final cut.
