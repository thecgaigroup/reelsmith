# Paid-Plugin-to-Free-Tool Map

<!-- Adapted from codepawl/creator-generalist (MIT), commit d3ab529a, read 2026-11-14 -->

How to get a paid After Effects, Premiere, or plugin effect using free tools in Resolve, Remotion, Blender or FFmpeg.
Every technique here is **untested in this repository**: run once and check frames before relying on it. These are starting points, not proven recipes. For platform loudness targets and export settings, see `platform-specs.md` and `loudness-accessibility.md`.

## Quick map

| Paid tool or effect | Free replacement | Notes |
|---|---|---|
| Twixtor (slow motion) | Resolve Optical Flow retime, Render in Place | See `retime-and-speed.md` references in DaVinci docs |
| CC Time Blend | Fusion Time Blend with Loop nodes | Fusion-specific |
| Saber (glows) | Fusion Glow + Blur on Text+ or mask | Neptune-style glow alternative |
| Element 3D, Depth | Fusion 3D (Replicate 3D, Text 3D) or Blender → GLB/EXR import | Native 3D in Fusion or external Blender pipeline |
| Roughen Edges, Halftone, Turbulent Displace | Fusion nodes with equivalent job | Node-based approach |
| Lumetri, Dehancer | Resolve Color page (note: Dehancer is paid OFX) | Color grading |
| Warp-O-Matic, Tween | Displace + Create Bump Map (Studio free fallback) | Displacement mapping |
| Premiere/AE transitions | Adjustment-clip Fusion transitions | Resolve-specific |
| AE camera shake, Wiggle | Fusion Camera Shake, Shake modifier, Anim Curves | Expression alternatives |
| AE Posterize Time | Frame hold in Resolve Retime or Remotion frame quantization | Choppy frame rate effect |

## Platform export targets (per-platform loudness and aspect)

These are the current targets as of 2026-10-23. **Always re-check the platform's own documentation** before a high-stakes delivery, as limits change frequently. Reelsmith's `scripts/presets.json` holds the current checked values.

### TikTok
- **Aspect:** 9:16 (1080x1920)
- **Length:** 3 minutes (some accounts 10 minutes)
- **Loudness target:** −14 LUFS integrated, peaks < −1 dBTP
- **Codec:** H.264, AAC 48 kHz

### Instagram Reels
- **Aspect:** 9:16 (1080x1920)
- **Length:** 15 minutes (API), typically under 90 seconds for feed performance
- **Loudness target:** −14 LUFS integrated, peaks < −1 dBTP
- **Codec:** H.264, AAC 48 kHz
- **Safe zone:** Keep top 14%, bottom 35%, and 6% on each side clear of text/logos

### YouTube Shorts
- **Aspect:** 9:16 (1080x1920) or square
- **Length:** Up to 3 minutes (over 1 minute with Content ID claim may be blocked)
- **Loudness target:** −14 LUFS integrated, peaks < −1 dBTP
- **Codec:** H.264 High profile, closed GOP
- **Safe zone:** Top 8%, bottom 35%, 6% left, 10% right

### YouTube (long-form)
- **Aspect:** 16:9 (1920x1080 or 3840x2160 for 4K)
- **Length:** Up to 12 hours (15 minutes for unverified accounts)
- **Loudness target:** −14 LUFS integrated, peaks < −1 dBTP
- **Codec:** H.264 High profile, closed GOP of half the frame rate, 8 Mbps at 1080p30
- **Safe zone:** 5% top, 10% bottom, 5% left/right

## Beat-synced captions

For Shorts and vertical video where speech drives the edit:

1. **Auto-generate captions** via the editor's built-in tool, `captions.py`, or the `watch-video` skill's speech extraction.
2. **Sync to speech:** 1–4 words on screen at a time, synced to the spoken word within 0.05–0.1 seconds.
3. **Style:** Bold sans font with outline or shadow, large enough to read on a phone. Place inside the safe zone (see above).
4. **Beat sync:** When music is present, time caption entrances to land on or just before the beat. The picture should arrive 4–8 frames before the word it illustrates.

Burned-in captions go into the master render; SRT/VTT sidecars can be uploaded separately for accessibility.

## Texture and analog treatments

These techniques come from the "analog Vox" system in creator-generalist but apply to any piece aiming for a tactile, non-digital look:

- **Roughen Edges:** Small border (2–3 px), applied to text or shapes to break digital sharpness
- **Chromatic aberration:** Light separation (0.8–1.5), not overdone (>2 looks amateur)
- **Grain overlay:** Halftone grunge at 50% grey, overlay blend mode
- **Posterize Time:** 8–12 fps for a collage/stop-motion feel (graphics only; never posterize the camera)
- **Vignette:** Subtle edge darkening

Apply these as adjustment layers over the whole comp. Keep them subtle: the goal is to add warmth and materiality, not to overpower the content.

## Loudness measurement (FFmpeg)

To check the integrated loudness of a final export:

```bash
ffmpeg -i output.mp4 -af loudnorm=print_format=summary -f null -
```

Read the "Input Integrated" (LUFS) and "Input True Peak" (dBTP) from the output. Aim for −14 LUFS integrated with true peak under −1 dBTP for streaming platforms.

To normalize:

```bash
ffmpeg -i input.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:v copy output.mp4
```

A two-pass run (measure first, then feed measured values back) is more accurate.

## Notes

- These mappings prioritize **free** and **tested** tools. When a free tool cannot match the paid one, the mapping names the limitation.
- **Reconciliation with existing Reelsmith docs:** Reelsmith's `loudness-accessibility.md` already covers −14 LUFS as the streaming standard. If any specific platform number conflicts with the table above, **keep Reelsmith's number** and note the difference here. The creator-generalist source was checked in late 2026; platforms change limits often.
- For DaVinci Resolve-specific steps (Fusion nodes, Color page, etc.), consult Resolve's own documentation or the creator-generalist `edit-video` references (not vendored here).
- **No paid API calls, no network requests in tests, no secrets.** This reference is read-only guidance.

---

**Source:** Adapted from [codepawl/creator-generalist](https://github.com/codepawl/creator-generalist) (MIT), commit d3ab529a1270217f70666f0566af3110a9e4f74d, read 2026-11-14. See `THIRD_PARTY_NOTICES.md` for full license.
