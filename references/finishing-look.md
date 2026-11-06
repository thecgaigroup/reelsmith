---
description: Load when grading or adding grain to a finished cut, especially one assembled from generated clips. One constant pass over the whole joined picture, after the stitch and before review.py and export.
---

# Finishing look

One look for the film, applied once. This is the grade-and-grain pass for footage cuts (generated clips, real selects). Engine effects on a Remotion or HyperFrames piece stay in `transitions.md` (Polish). This adds no package: it is one ffmpeg filter chain.

## Where it goes
1. Clips are reviewed and approved **raw** (`review-and-qa.md`). Never grade a clip that is sent for approval.
2. Assemble the cut (`transitions.md`, `helpers.md`).
3. Run the look **once on the joined picture**. Every shot gets the identical pass, so the cuts match. Audio is stream-copied.
4. Then `review.py check`, the stitch checks, and export. Run the last-frame identity check on the graded cut too.

No per-shot grade. A shot that does not match is fixed in generation, not in the finish.

## Never
Smooth faces or retouch skin (no bilateral, denoise or beauty blur by default). Sharpen anything: sharpening is what makes generated skin read as plastic. Raise saturation, or touch reds and yellows (skin, wood). Vary the filter per shot. Change geometry (no crop, reframe or stabilise). Add or alter audio.

## Pin the colour matrix
Many generators deliver untagged files. Untagged, ffmpeg converted YUV to RGB as BT.601 and back as BT.709, which darkened skin by about 4%. Start the chain with `setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709` and tag the output `-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv`.

## Example: a warm archival look, and why each number
Tested on 1080p24 generated clips. Face luma stayed within 1.5% of source, skin saturation within +1%, the frame overall about 8–11% less saturated; size, fps and frame count unchanged.

```
[in]setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,format=gbrp,
curves=master='0/0.035 0.2/0.2 0.5/0.5 0.8/0.82 1/0.965',
colorbalance=rh=0.028:gh=0.006:bh=-0.028:bs=0.012:pl=1,
colorchannelmixer=rr=0.952756:rg=0.042912:rb=0.004332:gr=0.012756:gg=0.982912:gb=0.004332:br=0.012756:bg=0.042912:bb=0.944332,
huesaturation=saturation=-0.2:colors=g+c+m,split[base][hl];
[hl]curves=master='0/0 0.72/0 1/0.9',gblur=sigma=24,colorchannelmixer=rr=1:gg=0.6:bb=0.35[glow];
[base][glow]blend=all_mode=screen:all_opacity=0.16,vignette=angle=0.25,unsharp=5:5:-0.35:5:5:0,format=yuv420p,noise=c0s=7:c0f=t[out]
```

| Setting | Why |
|---|---|
| `curves 0/0.035` | Lifts blacks ~9/255: kills the inky generated black, reads as print stock |
| `0.2/0.2 0.5/0.5` | Mids pinned, so skin keeps its exposure |
| `0.8/0.82`, `1/0.965` | A little snap in the upper half; highlights rolled off ~9/255 to remove specular sheen on skin |
| `colorbalance rh/bh ±0.028`, `gh 0.006`, `bs 0.012`, `pl=1` | Warm highlights so every location shares one colour of light; a touch of green stops warm skin turning pink; slightly cool shadows; lightness preserved |
| `colorchannelmixer` (Rec.709 desaturate 0.94) | 6% global desaturation, which cancels the saturation the warm shift adds to skin |
| `huesaturation -0.2 g+c+m` | Mutes over-rich greens, teals and magentas; reds and yellows untouched |
| Halation: threshold 0.72, `sigma 24`, tint g0.6 b0.35, screen 0.16 | Only the top ~28% of tones glow (lamps, windows, not faces); wide like film base, red-orange like real halation, felt not seen; screen never darkens |
| `vignette angle 0.25` | ~4% frame luma; 0.42 cost 12% |
| `unsharp … -0.35` | A hair of negative unsharp takes the digital edge off hair and fabric without blurring a face |
| `noise c0s=7 c0f=t`, last | Mono temporal grain, visible at 100% and on a phone, gone at thumbnail. Last, so it is not blurred or vignetted. 5 is quieter, 9 more filmic |

A comparison look is the same chain without halation, vignette and softening. Let the creator choose on a phone, with a split-screen clip.

## Measure before you fix
- **Flicker:** measure frame-to-frame luma first (`signalstats`, YDIF mean and peak). Clean generated clips barely pulse (mean 0.03); `deflicker` *added* pumping to them (0.21 mean, 0.98 peak). Deflicker only a clip that measurably flickers, and re-measure.
- **Denoise:** default none; it smooths pores. Only on a visibly noisy clip, after the creator sees it, and always before grain (`hqdn3d=2:1.5:3:3` is fast; `nlmeans` is about 13 s per second of 1080p).
- **Grain does not compress.** With grain, crf 16 was ~96 Mbps, crf 20 ~54 Mbps (the graded master), crf 22 ~28 Mbps (the upload copy). Platform re-encodes thin fine grain; if it vanishes after upload, a coarser grain is the next test.

## Upscaling
A 720p source: lanczos to 1080 before the grade, plus about 2 points more grain (grain restores apparent detail; sharpening brings back the digital edge). A learned video upscaler is a paid route: quote it (`ai-generation.md`) and run a one-clip canary judged on faces, flicker and text before any batch.

Cost: CPU only, about 50 s of wall time per minute of 1080p24 on a 14-core laptop.
