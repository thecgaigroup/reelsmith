# Music: sources, licenses, beat grid

## Order of preference
1. The user's own or licensed track. Ask for the license if it's unclear.
2. A verified royalty-free track from the sources below. Log it in `credits.json`.
3. `beats.py synth` bed (generated with ffmpeg, no rights issues) as the fallback.
4. Fal music generation: quote only (`get_pricing` -> `estimate_cost`), and only after explicit approval.

Test track (in the package): `assets/music/militaire-electronic-32s.mp3`, "Militaire Electronic" by
Kevin MacLeod, CC BY 3.0 (Wikimedia Commons via Openverse). Its beat grid and `CREDITS.txt` sit next to it.
Credit is required in the end card or description.

## Sources (licenses verified 2026-10-23)
| Source | License | Attribution | API | Watch out |
|---|---|---|---|---|
| Incompetech (Kevin MacLeod) | CC BY 4.0 (paid no-credit option) | Required: "Title Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0" | No | Use the exact credit text |
| Pixabay Music | Pixabay Content License | Not required (credit appreciated) | No music API | No standalone resale. Some tracks get Content ID claims; keep the download page URL |
| YouTube Audio Library | Standard: YouTube use only; some tracks CC BY | CC BY tracks need credit in the description | No | Not for other platforms unless CC BY |
| Free Music Archive | Per-track CC | Per track | No | ND = no sync to video; NC = no ads or promos |
| ccMixter | Per-track CC, many NC | Per track | No | Sampling licenses can't be used in ads |
| Openverse audio / Wikimedia Commons | Per-item CC0, CC BY or CC BY-SA | Per item (the API returns the attribution text) | Yes (`api.openverse.org`, anonymous, rate-limited) | Verify the license on the landing page; BY-SA makes the video BY-SA |
| Mixkit | Free license (commercial OK); "Restricted" items are personal only | No | No (bots are forbidden) | Download by hand only |

Never rip music from videos or streaming services. Commercial ads need a commercial license (no NC).
Background: creativecommons.org/legalmusicforvideos.

## Beat grid
    beats.py grid track.mp3 -o track.beatgrid.json     # librosa -> hyperframes beats -> fixed --bpm
    beats.py snap track.beatgrid.json --durations 3,2.5,4 --unit bar
    beats.py fit track.mp3 --seconds 22 -o fitted.mp3 --grid track.beatgrid.json   # ends on a bar line, fades out
    beats.py synth -o bed.mp3 --bpm 120 --seconds 30 --mood bright|dark|calm
`beatgrid.json` holds `{engine, bpm, beats[], downbeats[], bars[], sections[], duration}` in seconds.
`reelsmith.py render --music track.mp3` builds or reuses the grid, starts at the first downbeat and snaps
scene cuts to it (templates choose `beat`, `half` or `bar` units).

## Mixing
- Music sits about -18 to -20 LU under the narration. Duck to about 35% under VO with
  `sidechaincompress` (the pipeline does this), using 8-frame ramps.
- Fade in 0.5 s and out 1.5 s; end on a downbeat.
- Master with two-pass loudnorm to -14 LUFS integrated and -1.5 dBTP for social (see loudness-accessibility.md).

## Sound on the beat

Picture and sound share one clock. Write the cue sheet on the storyboard (`storyboard.md`), in the same times as the shots. Do not keep a second timeline in a side file the comp does not read.

```js
const b = (n) => n * (60 / bpm); // beat n, in seconds. A half-beat is b(n + 0.5).
```

HyperFrames tweens and `<audio data-start>` use `b(n)`. Remotion uses `Math.round(b(n) * fps)`. When a track exists, `beats.py grid` is the table (`beats`, `downbeats`, `bars`). A cue is a grid time plus the role's sync tap (`offset_ms` below). It is not a number typed from memory.

| On screen | Sound | Gain |
|---|---|---|
| Word or line lands | Short whoosh, then a soft blip | 0.12–0.20 |
| Chip, badge, cursor click | Click or pop. Pitch rises across a run | 0.15–0.25 |
| Build into the spectacle | One riser, ending on the hit | ~0.20 |
| Spectacle or logo slam | One impact | 0.25–0.35 |
| End mark | Chime, in the bed's key | ~0.15 |
| Drift, grain, idle | Silence | — |

Accent. Continuous motion stays quiet. One impact and one riser per film. On a launch reel that riser is the reverse swell in the role bank. Hero hits sit at 0.25–0.35, support at 0.08–0.20, and the bed ducks under speech and under the impact. Pan follows on-screen x, from −1 to +1. Tonal hits stay in one key. Those linear gains are the narrated mix, once the bed is already ducked. A music-led launch uses the bed-relative levels below instead of copying one gain onto every stem.

### Sync taps

`b(n)` is the picture event: the cut, the cursor press, the word landing. The wav does not all start on that instant. Write `offset_ms` on the cue so the sync point meets the frame you mean. A tap uses its attack. A whoosh, a swell, and an impact use their peak.

These taps are medians measured on music-led launch references. They are the house default. Move one when the storyboard says the feel is early or late.

| Role | Sync point | offset_ms |
|---|---|---|
| Tap, tick | attack leads the cut | −60 |
| Knock | attack leads the cut | −40 |
| Click (cursor press) | attack leads the press frame | −11 |
| Pop-in thump | peak just after the land | +30 |
| Whoosh into a seam | peak just after the cut | +37 |
| Reverse swell into the spectacle | peak just after the cut | +42 |
| Impact, logo slam | peak on the frame | 0 |

Place the file so that point sits at `b(n) + offset_ms / 1000`. HyperFrames: `data-start` is the start of the file, earlier than the sync point by whatever attack or peak lives inside the take. Remotion: `from` is `Math.round((b(n) + offset_ms / 1000) * fps)` minus the frames before that sync point. A run of the same role stays apart: ticks about 66 ms, keys about 87 ms, pops about 114 ms. Tighter than that, the row becomes a buzz.

### Bed-relative levels

On a music-led launch, measure the music's median level in the second before the cue. Set the effect so its loudest ~50 ms sits about 3–10 dB over that median (`bed_db`). UI ticks, clicks, and pops sit at the low end, or under the accent. The one impact sits at the top. The bed steps down before that impact. It does not duck under every tick.

Narration still uses the linear gains in the table above, with the bed ducked under speech (`Mixing`). Master the sum to about −14 LUFS (`loudness-accessibility.md`). Sparse hits still need a sustained bed (Hits without a new package).

### Launch role bank

Name roles on the cue sheet. One row per designed sound. The bed stays the licensed track or `beats.py synth`. Shapes stay the stdlib and ffmpeg sketches below. This list is the recipe. It is not a sample library.

| Role | Lands on | Feel |
|---|---|---|
| whoosh | the primary seam | short; peak just after the cut |
| tap / click | chip, badge, cursor press | short; attack leads the frame |
| knock | a physical UI beat, when the storyboard names one | mid; attack leads the frame |
| reverse swell | the build into the spectacle | one per film; peak just after the cut |
| impact | spectacle or logo slam | one per film; peak on the frame; bed steps down first |
| chime | end mark | in the bed's key |
| drift, grain, idle | holds | silence |

A launch kit is that list filled in: role, `b(n)`, `offset_ms`, `bed_db`. One clean impact on the lockup. Leave a 252-sound bank upstream.

### Measured SFX check

Read the mix the way you read stills. Three passes, all on the house clock.

1. **Timeline.** The cue sheet is the transcript: time, role, `offset_ms`, `bed_db`, picture event. A transient with no row is a hardcoded time or a stale file.
2. **Sheet.** Seek the picture to `b(n)` and Read that frame (`brand-qa.md`). The sync point belongs to that frame. `review.py check` reports integrated LUFS and true peak on the encoded file.
3. **Critique.** Timestamp the first failure and fix that row before you re-render the film. Sync: the attack or peak is within a frame of `b(n) + offset_ms`. Level: the accent is 3–10 dB over the prior-second bed, and UI detail stays under the impact. Density: one impact, one riser or reverse swell, runs keep their gap, idle stays quiet.

The sound score in `brand-qa.md` uses this check. It does not install a listener. It is separate from the SageCut frame ladder.

### Hits without a new package

The bed stays the licensed track or `beats.py synth`. When the brief wants hits, synthesize them with Python stdlib or ffmpeg. Do not add an npm audio library, and do not vendor a sound-design skill.

Shape, not a dependency: a kick is a sine that drops in pitch with a short decay; a hat is a short burst of high noise; an impact is a low sine plus noise, decay under about 200 ms; a whoosh is band-limited noise swept upward. An impact's peak lands on `b(n)`. A tap's attack leads that frame, and a whoosh or swell peaks just after it (Sync taps).

Master to about −14 LUFS integrated. Leave headroom so the encoded AAC file stays at or under −1 dBTP (`loudness-accessibility.md`). A bed of tiny hits and silence will not reach −14 without crushing. Lengthen the bed. Do not slam a limiter to fake the number.

HyperFrames: one `<audio id="…">` per stem, with `data-start`, `data-duration`, and `data-track-index`. Do not call `play()`. From 0.8.197 the renderer sums multiple audio clips. Remotion: a `<Sequence from={frame}>` per cue, then `export.py loudnorm` on the final, because Remotion does not normalize.

Check: every transient's sync point sits on `b(n) + offset_ms` (Sync taps). A hit with no cue row is a hardcoded time or a stale file. Seek the picture to that `b(n)` and read the frame (`brand-qa.md`). This repo does not ship an `sfx` package. The pattern is this section.

## Scout notes

- [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion) — cue sheet on the picture's timeline, gain hierarchy, −14 LUFS, stdlib generators. Not installed.
- [Sunwood-ai-labs/hyperframes-motion-reel-skill](https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill) — `b(n)` beat grid, code-generated kick and impact on that same grid. Not installed. HyperFrames skills stay the HeyGen ones, and they stay on.
- [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) (MIT) — launch-preset ideas only: `offset_ms` taps, `bed_db`, a role kit, and critique / sheet / timeline as measurements. [LexnLin, earshot v0.4](https://x.com/LexnLin/status/2113393065427620076). The sound bank, the skills, and the MCP are not installed. CPU listening stays local if anyone runs it later; this repo does not (`ROADMAP.md`).
