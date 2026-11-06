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

## Generated clips: every clip, on arrival

Before a generated clip is used anywhere, a fresh reviewer (not the agent that prompted it) checks the **raw** file. Never send a graded or finished clip for approval: reviewers judge identity and action on the model's output.

1. **Hash and probe.** Recompute sha256 and compare it with the generation receipt. `ffprobe`: resolution, aspect (a 1344x768 file is not 16:9), fps, codec, duration against the plan, and a full decode (`ffmpeg -v error -i clip.mp4 -f null -`).
2. **Audible track.** An audio stream is present only if one was expected. A stream can exist and still be silent: check it with `volumedetect` (mean near −90 dB is no audio).
3. **Five frames:** 0, 25, 50, 75 and 100% of the clip. Look at faces, hands, fingers and feet. Reject a warp; do not average it away.
4. **Identity at the last frame,** compared with the approved keyframe or sheet, not with the first frame. Drift compounds over a clip (eye colour, freckles, style).
5. **Mouths on silent shots.** Only the singer's mouth moves. Tile face crops at about 1.5 fps and confirm closed mouths on every non-singing character.
6. **Separate verdicts,** not one: technical, identity, required action, mouths, hands and contact, camera, continuity (no invented text or props), skin and style, motion. One failure fails the clip for that purpose. Unverified is a verdict, not a pass.

Write the verdict to a `review.json` keyed by the clip's sha256. A new file, a re-encode, or a trim is a new hash and needs a new verdict.

## Review before the stitch

Assembly starts only from reviewed, selected clips: one take per shot, each pick's sha256 matching its file, and the creator's words recorded (a rejected take needs a recorded override).

- **The song master is the only audio.** Every clip's own audio is discarded. Graphics engines render silent or as alpha, and the master is muxed last.
- **The cut plan runs on the song clock:** shot, source, source in/out, record in/out, transition. It covers 0 to the master's length with no gap and no overlap.
- **Every non-cut join has a one-line story reason** (`transitions.md`, Generated clips).
- **Coverage gaps are still-holds of the shot's approved opening frame, flagged.** Name the output an animatic until every shot has a clip. A clip shorter than its slot is reported as a shortfall, not silently looped.

## After every assembly

Run `review.py check` on every assembly, graded or not, then these stitch checks on the graded cut:
- A frame either side of every cut: no same-size cut on the same face. `ffmpeg -i cut.mp4 -vf scdet=t=8 -an -f null -` lists cut times; compare them with the cut plan (a missing cut hides a soft blend).
- Identity at each cut: the outgoing last frame and the incoming first frame against the approved keyframes.
- Flicker across joins: frame-to-frame luma (`signalstats` YDIF). Measure before reaching for `deflicker` (`finishing-look.md`).
- `blackdetect=d=0.04:pix_th=0.12` reports only the planned fades.
- Audio: one stream, starting at 0, the master's length, matching the master. Pops only matter where audio was spliced (a teaser, a cutdown); those get 30 ms fades (`helpers.md`). A continuous master needs none.

## Loudness on a music delivery

A mastered song is not a reel. Measure and report its loudness; do not normalize it to −14 LUFS by default. The master stays as supplied unless the creator says otherwise. `review.py` will show a loudness WARN against the preset target; report it, do not fix it. `export.py run` and `export.py loudnorm` normalize every output, so on a music delivery use them only for a separate platform-loudness copy the creator asked for. The master delivery is the finished picture with the untouched master muxed in (`helpers.md`). If the creator asks for normalization, use two-pass `loudnorm` with `linear=true`. If pass 2 reports `normalization_type: dynamic`, it compressed the song: stop and say so.

## Approve
Send the user `preview.mp4` or the sheets plus `review.md`. Only when they say yes:
    review.py approve out/_review --by "user in chat"
    review.py status out/_review      # exit 0 only when approved
`export.py run` and `youtube_prep.py` refuse to run without an approved review. `--unreviewed` exists for internal
tests only.

## Iterate cheaply
VO is cached by text hash, so visual edits never re-voice. Fix -> `--draft` render -> `review.py check` again.
Re-approve after any change to the final cut.
