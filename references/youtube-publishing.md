# YouTube publish-prep (never uploads)

    youtube_prep.py out/howto-16x9.mp4 --job out/job.json --review out/_review --out out/youtube \
        --title "Ship a launch plan in 3 steps" --summary "…" --tags launch,planning,tutorial \
        --thumb-at 3.2 [--thumb-text "3 steps"] --brand brand.json --srt out/howto.srt --vtt out/howto.vtt \
        --privacy private --made-for-kids no --category 28

Writes `metadata.json`, `description.txt` (summary + chapters + credits + links), `thumbnail.jpg` (1280x720,
under 2 MB, 2-4 big words, brand font), `captions.srt/.vtt`, `upload-checklist.md` and `manifest.json` (sha256 of
every file, so the uploaded file is provably the reviewed one).

Gates (exit 1 on FAIL): review approved; H.264/yuv420p/AAC; 16:9 for regular uploads (9:16 up to 3 min counts as
a Short); title <= 100 characters; description <= 5000; tags <= 500 characters in total; chapters valid (first at
0:00, at least 3, each at least 10 s; short ones are merged into the neighbor) or omitted with a note.

## Manual upload (the user does this in YouTube Studio)
1. Upload the exact file in `manifest.json`, starting as **Private**.
2. Paste the title and description; add tags; choose the category.
3. Upload `thumbnail.jpg` (custom thumbnails need a verified channel).
4. Subtitles -> upload `captions.srt` (better than auto-captions).
5. **Altered or synthetic content:** answer "Yes" if realistic AI voice, faces or scenes could be mistaken for real.
   A clearly synthetic TTS narrator over motion graphics usually doesn't require it, but say "AI voice" in the
   description anyway.
6. Audience: made for kids yes/no (a legal requirement, COPPA).
7. Check chapters appear, then Unlisted -> share for a final look -> Public or Scheduled.

Automated upload (YouTube Data API, OAuth) is deliberately out of scope: it needs the channel owner's
consent and credentials, and a mistaken public post can't be taken back.
