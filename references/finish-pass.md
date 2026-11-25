# Offline finish pass

Run this optional step on a local, flattened video with even dimensions. It requires NumPy, ffprobe, and FFmpeg with libx264 and AAC encoding.

```sh
REELSMITH_FINISH_PASS=1 python3 scripts/finish_pass.py run input.mp4 --out finished.mp4 --scenes scenes.csv
python3 scripts/finish_pass.py check finished.mp4 --reference input.mp4
```

The run flag defaults to off. Set it to `1`, `true`, `on`, or `yes` (case-insensitive) to enable it. The `check` command works independently of the flag.

A PySceneDetect CSV is optional. Without one, FFmpeg supplies cut candidates. The planner combines cuts and motion into a temporary `cues.json`. The mixer ducks the effects under the programme audio and applies gain and peak limiting to the combined mix. The five synthesized sounds are CC0-1.0. The [license notes](../assets/sfx/LICENSES.md) list their synthesis parameters and SHA-256 hashes. A sound with a different license or hash stops the run.

The default 9:16 layout keeps its title region sharp and adds restrained, color-preserving bloom to bright title detail. The soft blur preserves the placement and visibility of picture elements outside the title band. For other aspect ratios, the picture effects are skipped unless you supply `--layout title.json`. Use the same structure as the [bundled layout](finish-pass-layouts/signal-9x16.json), with left, top, right, and bottom expressed as fractions of the frame. Make all other picture edits in the source composition.

The pass encodes the picture once at CRF 17 and stream-copies it into the final MP4. It verifies the encoded AAC at −14 ± 0.5 LUFS integrated and ≤ −1 dBTP. The report at `finished.mp4.finish/report.json` records the cue totals, sound hashes, filters, loudness and stream timing. `check` remeasures the audio, compares dimensions, frame count, frame rate, duration and relative stream starts to the source, and verifies the MP4 size and SHA-256 against the report.
