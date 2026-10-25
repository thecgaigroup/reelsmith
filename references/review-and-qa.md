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
For client sizzle and hand-authored kinetic pieces, look at `contact.jpg` and `phone.jpg` (or HyperFrames
snapshots at each beat) **before** a delivery render. `review.md` includes a 1–10 table: hook, phone, motion,
variety, brand, sound. Fill it. Fix the three worst scores and re-check until each is 8 or higher. Rules and
banned defaults: `motion-design.md`. The table does not change `review.py` pass/fail. The 1–5 rubric below
stays for every job. Template cuts can leave the kinetic table blank.

## Approve
Send the user `preview.mp4` or the sheets plus `review.md`. Only when they say yes:
    review.py approve out/_review --by "user in chat"
    review.py status out/_review      # exit 0 only when approved
`export.py run` and `youtube_prep.py` refuse to run without an approved review. `--unreviewed` exists for internal
tests only.

## Iterate cheaply
VO is cached by text hash, so visual edits never re-voice. Fix -> `--draft` render -> `review.py check` again.
Re-approve after any change to the final cut.
