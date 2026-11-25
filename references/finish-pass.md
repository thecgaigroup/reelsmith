# Finish a baked master

The finish pass runs locally with Python 3.10+, NumPy, OpenCV for layouts with baked lettering, and FFmpeg/ffprobe with libx264 and AAC. It is off by default. Set `REELSMITH_FINISH_PASS` to `1`, `true`, `on`, or `yes` (case-insensitive) to enable it.

```sh
REELSMITH_FINISH_PASS=1 python3 scripts/finish_pass.py run master.mp4 --out finished.mp4
python3 scripts/finish_pass.py check finished.mp4 --reference master.mp4

REELSMITH_FINISH_PASS=1 python3 scripts/export.py run master.mp4 \
  --preset reels,tiktok --out delivery --review review-dir --thumb-at 0
```

Direct runs write `finished.mp4.finish/report.json` with gate measurements, the cover frame and time, anchor rectangles, cue counts, verified sound hashes, and the MP4's SHA-256 and byte size. The run stages both files, renames the MP4 first, then renames the report and verifies the pair. If a process stops between the renames, `check` fails for a missing or mismatched report. To verify an older render whose report lacks the MP4 identity, rerun the finish pass.

Export runs finish the approved input once in a temporary directory, then apply the requested platform video presets and copy the finished AAC audio. Export measures frame 0 of every encoded preset against the original master's opening. A failed luma gate returns a nonzero status and discards the staged delivery. Use a direct run to retain the finish report or supply a custom layout. `--thumb-at 0` makes the platform thumbnail use the opening frame.

## Picture

The default [Signal 9:16 layout](finish-pass-layouts/signal-9x16.json) describes baked regions as fractional `[left, top, right, bottom]` coordinates. Check the positions against your master or supply a matching JSON file with `--layout`. The finish pass moves the badge and pill to the safe top corners and fits the caption band below or clear of the title. For the pill and captions, each frame uses a feathered mask around the bright lettering and its dark backing. Nearby glyphs are grouped by baseline, and short captions qualify when their glyphs fit the text-height range and sit near the center of the band. A pill outline is retained when it surrounds a detected line of text. The pass uses the same per-frame mask to limit the fill of each vacated text region. The safe rectangle comes from the intersection of the Reels and TikTok presets. TikTok right-rail intersections are reported as advisories. Other aspect ratios need an explicit layout for title and anchor effects.

A feathered depth-of-field mask lets the title stay sharp. Bright and saturated title pixels create a two-radius glow in their original colours. On a flattened render, the mask estimates the text backing from its contrast and shape, and the fill approximates the hidden picture.

The cover is selected from the first three seconds using luminance, title detail, and stability over nearby frames. It replaces frame 0, including when a platform preset reduces the frame rate. Use `--cover-hold SECONDS` to extend the replacement, rounded up to whole frames. The rendered timeline keeps the same frame count, dimensions, frame rate, and video duration. The production path is intended for constant-frame-rate masters.

## Audio and verification

Supply a PySceneDetect CSV with `--scenes` for repeatable editorial cuts, or use the default FFmpeg `scdet` detection. Motion onsets and cuts determine cue timing and effect choice. Exact fallback cues can vary with the detector and FFmpeg scaling version. All five [SFX assets](../assets/sfx/LICENSES.md) are self-synthesized and dedicated under CC0-1.0. The mix only uses assets whose license and SHA-256 match the manifest. NumPy is used for local analysis and mixing support. FFmpeg is invoked as an external program with LGPL filters and the existing libx264 encoder.

SFX duck under the existing voice and music. The programme is summed with the ducked effects and the combined mix receives static gain and true-peak limiting. The encoded MP4 is measured using FFmpeg ebur128. A failed peak check triggers another encoded candidate from the premix with more headroom. The video stream is reused for those attempts.

Both commands require existing local input files and restrict FFmpeg and ffprobe to local file and pipe protocols. The checker runs independently of the flag. After verifying the report against the MP4, it decodes both videos to check frame-0 luma mean ≥16, standard deviation ≥12 and mean ≥95% of the source opening. It re-plans safe placement from the source size and layout and checks the cover for the source caption's bright strokes independently of the compositor mask. It checks the MP4 contains 48 kHz AAC at −14 ±0.5 LUFS integrated and ≤−1 dBTP, and compares the video timeline with the reference. The finish pass sets the earliest stream start to zero, preserves the original lead or lag, and checks the relative starts within one source frame. If the original custom layout moved, pass its current path with `--layout`.
