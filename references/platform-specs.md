# Platform specs, safe zones and export

Checked 2026-10-23 against each platform's own documentation. Platforms change these often: re-check
the source before a high-stakes delivery and update `scripts/presets.json` (`checked` field).

## Presets (`scripts/presets.json`, used by `export.py`, `review.py`, `script_lint.py`)
| Preset | Size | Max length | Safe zone (top/bottom/left/right) | Notes |
|---|---|---|---|---|
| youtube | 1920x1080 | 12 h (15 min unverified) | 5/10/5/5% | H.264 High, closed GOP of half the frame rate, 8 Mbps at 1080p30 |
| shorts | 1080x1920 | 3 min | 8/35/6/10% | Square or vertical; over 1 min with a Content ID claim gets blocked |
| reels | 1080x1920 | 15 min (API) | 14/35/6/6% | Meta: keep the top 14%, bottom 35% and 6% sides clear of text and logos |
| ig-feed | 1080x1350 (4:5) | 15 min | 5/8/5/5% | Feed images 1.91:1 to 4:5 |
| ig-stories | 1080x1920 | 60 s per card | 14/35/6/6% | Same safe zone as Reels |
| tiktok | 1080x1920 | 3 min (some accounts 10) | 12.5/34.5/11.1/11.1% plus the right rail | Right-side buttons from about 44% of the height down |
| linkedin / linkedin-square | 1920x1080 / 1080x1080 | 15 min | 6/10/5/5% | 3 s minimum; 75 KB to 5 GB |
| x / x-vertical / x-square | 1280x720 / 720x1280 / 720x720 | 20 min (Premium 2 h+) | 5–8/12–20/5/5% | 1080p for subscribers; at least 5 Mbps video, AAC-LC 128k |
| master | source size | none | 5% | Archive copy at CRF 16 with 320k audio, -16 LUFS |

Safe-zone guide PNGs are in `guides/` (`safe-reels.png` and the others). Generate one with
`export.py overlay --preset reels -o reels-safe.png`; `review.py check --preset reels` draws it over frames (`safe.jpg`).
The template engine's own vertical safe area (13% top, 32% bottom, 8% left, 11% right) stays inside the
Reels, Shorts and TikTok zones.

## Export
    review.py check final.mp4 --out review/ --preset reels --job out/job.json    # show user, then:
    review.py approve review/ --by "user in chat"
    export.py run final.mp4 --preset reels,tiktok,shorts --out deliver/ --review review/ [--fit pad-blur|crop|pad] [--srt c.srt]
    export.py loudnorm in.mp4 out.mp4 --lufs -14      # master the mix only (Remotion renders need this)

`run` fits the frame (a native render beats `pad-blur`), uses H.264 High and AAC-LC 48 kHz, a closed GOP,
two-pass loudnorm to the preset target, faststart and stripped metadata. It checks the length and size
limits, writes a thumbnail or cover, and copies caption sidecars. It refuses to run without an
approved review.

## Sources
- YouTube upload encoding: support.google.com/youtube/answer/1722171. Limits: answer/71673. Thumbnails: answer/72431. Shorts: answer/15424877, answer/10059070. Chapters: answer/9884579.
- Instagram Reels and Graph API media: developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media. Instagram Help 1038071743007909 and 1631821640426723. Meta Ads Guide (Reels/Stories safe zones).
- TikTok Content Posting API media transfer guide: developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide (updated 2026-08-04). Safe zones: TikTok Ads Manager overlay templates. The fixed numbers above are a common reading of those templates, not an official spec.
- LinkedIn video specs: linkedin.com/help/linkedin/answer/a7174587.
- X media best practices: docs.x.com/x-api/media/quickstart/best-practices.
