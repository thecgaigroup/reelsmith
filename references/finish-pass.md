# Offline finish pass

Run this optional step on a local, flattened video with even dimensions and at least 1.0 s of picture. It requires NumPy, ffprobe, and FFmpeg with libx264 and AAC encoding.

```sh
REELSMITH_FINISH_PASS=1 python3 scripts/finish_pass.py run input.mp4 --out finished.mp4 --scenes scenes.csv
python3 scripts/finish_pass.py check finished.mp4 --reference input.mp4
```

The run flag defaults to off. Set it to `1`, `true`, `on`, or `yes` (case-insensitive) to enable it. Disabled runs print a message and write nothing. The `check` command works independently of the flag.

The enabled pass supports constant-frame-rate (CFR) video. If programme audio is present, its start must be within one video frame of the picture start in either direction. The pass checks the declared rates, each frame's presentation timestamp, and the stream starts before creating any output or temporary directories. It exits with a nonzero status on unsupported input and prints `finish pass supports CFR, aligned A/V only` followed by the reason.

A PySceneDetect CSV is optional. Use cut times in seconds relative to the picture start. An empty CSV or a blank first row stops the run with an error. Without a CSV, FFmpeg supplies cut candidates. The planner uses CFR frame indices to time motion cues. The mixer normalizes the accepted stream starts to zero and ducks effects under programme audio. It writes one AAC track containing the full mix, or one cue-only AAC track when the source has no audio. The picture duration bounds the mix, with silence after a short programme track and up to 25 ms of tolerance when measuring the encoded audio duration. A lead-in before the first frame starts at the first frame. Cues starting at or after the picture end appear in `cues_skipped`. A cue that begins before the end appears in `cues_rendered` even when the picture end trims its tail.

The five synthesized sounds are CC0-1.0. The [license notes](../assets/sfx/LICENSES.md) list their synthesis parameters and SHA-256 hashes. A sound with a different license or hash stops the run.

The default 9:16 layout keeps its title region sharp and adds restrained, color-preserving bloom to bright title detail. It also keeps the full-width top 11.5% and bottom 20% strips sharp. The blur softens the remaining central picture area, with feathered transitions at the region edges. For other aspect ratios, the picture effects are skipped unless you supply `--layout title.json`. In a custom layout, `regions.title` specifies the title and the optional `regions.keep_sharp` lists additional sharp rectangles. Each rectangle uses left, top, right, and bottom fractions of the frame. The title bloom takes precedence where regions overlap. See the [bundled layout](finish-pass-layouts/signal-9x16.json).

The pass encodes the picture once at CRF 17 and stream-copies it into the final MP4. It adjusts gain and limiter ceiling using encoded AAC measurements and requires −14 ± 0.5 LUFS integrated and ≤ −1 dBTP on the mix track. A mix without loudness blocks above the −70 LUFS gate fails before mastering. The report at `finished.mp4.finish/report.json` records planned, rendered and skipped cues, rendered totals, sound hashes, filters, loudness, mastering attempts and stream timing. `check` verifies the cue partition and rendered totals, confirms there is exactly one audio track, remeasures the mix, compares picture and stream timing to the source, and verifies the MP4 size and SHA-256 against the report.
