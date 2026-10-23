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
