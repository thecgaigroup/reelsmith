# Loudness and accessibility

## Loudness (EBU R128 / ITU-R BS.1770)
| Target | Integrated | True peak | Use |
|---|---|---|---|
| Social + YouTube | -14 LUFS | -1.5 dBTP (presets use -1.0 to -1.5) | default for every preset |
| Master / broadcast-safe | -16 LUFS (Apple podcasts, many streaming) | -1 dBTP | `master` preset |
| EBU broadcast | -23 LUFS | -1 dBTP | TV delivery only |
Platforms turn loud uploads down but rarely turn quiet ones up, so -14 is the safe middle.
Reelsmith mixes in one pass: VO normalized, music ducked about 10-14 dB under speech (sidechain), then two-pass
`loudnorm` (measured values, `linear=true`). Remotion output needs `export.py loudnorm`. Verify:
`ffmpeg -i x.mp4 -filter_complex ebur128=peak=true -f null -` (read I and Peak in the summary).
AAC encoding adds 0.5-1.5 dB of true-peak overshoot on punchy mixes, and more at 128 kbps, so always measure the
**encoded** file. `export.py` does this for you: loudnorm, an oversampled limiter at -2.5 dBTP, AAC, a re-measure,
and a small gain trim if the peak is still above the ceiling (it costs at most about 1 LU).

## Accessibility
- **Captions** on every video with speech: sidecars (SRT/VTT) for platforms and burn-in for silent-autoplay social.
  Follow captions.md (line length, reading speed, 2 lines max, sync).
- **Contrast:** text at least 4.5:1 (large text 3:1), WCAG 1.4.3. `brand.py validate` checks the palette; put
  scrims behind text on photos.
- **Flashes:** no more than 3 flashes per second (WCAG 2.3.1); avoid full-screen luminance flips and saturated red
  flashes. `review.py check` flags violations.
- **Motion:** keep camera moves smooth (ease), avoid long fast shakes, and give each text card time to read
  (about 0.3 s per word plus 1 s).
- **Hold text** at least 1.5 s; never put essential info only in the music or only in color.
- **Describe** key visuals in the VO or the description for blind viewers (audio description light).
- **Language:** plain words, short sentences, and spell out numbers that matter.
