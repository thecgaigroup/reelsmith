# Helpers (tested; install on first use)

- **Manim** (diagrams, math): venv `pip install manim` (apt `libcairo2-dev libpango1.0-dev pkg-config`; `MathTex` also
  needs `texlive-latex-extra dvisvgm`). `manim -t --format mov -qm scene.py Scene` gives a qtrle alpha clip. Composite
  at time T: `[1:v]setpts=PTS-STARTPTS+T/TB[m];[0:v][m]overlay=…:eof_action=pass`. Example: `manim-example/`.
- **Lottie:** HyperFrames: local `assets/lottie.min.js`, `lottie.loadAnimation({…, autoplay:false, path:"assets/x.json"})`,
  pushed to `window.__hfLottie` (the runtime seeks it). Remotion: `@remotion/lottie`. Example: `lottie-example/`.
- **auto-editor** (cut silences from user footage): venv `pip install auto-editor`; `auto-editor in.mp4 -o cut.mp4 --no-open`.
- **Transcribe:** `$HF transcribe a.mp3 -e parakeet --json` (word times) or `--to srt`. WhisperX: venv
  `pip install whisperx` (~7.5 GB; `--device cpu --compute_type int8`).
- **ffmpeg recipes:**
  - Concat mixed clips: `concat=n=N:v=1:a=1`.
  - Duck: `[mus][vo]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300`, then `amix=normalize=0`.
  - Loudness: two-pass `loudnorm=I=-14:TP=-1.5:LRA=11` (or `export.py loudnorm`).
  - GIF: `fps=15,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer`.
  - Seamless loop repeat: `reelsmith.py loop VIDEO --times N -o out.mp4` (stream copy).
- **Beat grid / music:** `beats.py grid track.mp3 -o beatgrid.json` (librosa -> `hyperframes beats` -> fixed BPM);
  `beats.py snap beatgrid.json --durations 3,2.5,4 --unit bar`; `beats.py fit track.mp3 --seconds 22 -o bed.mp3`
  (trims to a bar line, fades out); `beats.py synth -o bed.mp3 --bpm 120 --seconds 30 --mood bright` (free fallback).
  SFX cues use that same grid (`music.md`), including launch sync taps and the role bank. Do not add a separate sound package.

## Spoken / raw takes (post)
Use this when the job is cutting talking-head, interview, or other raw spoken selects. Client sizzles stay
storyboard-first (`storyboard.md`); this does not replace that board.

Pattern only — do **not** install [browser-use/video-use](https://github.com/browser-use/video-use) or add it as a dependency.

1. **Transcript first.** Transcribe with the tools above (`$HF transcribe` or WhisperX). Read words and times. Do not dump every frame into the prompt.
2. **EDL, then confirm.** Write a short list: source, in, out, why (keep / drop filler / drop a false start). Show it. Do not cut until the user says yes.
3. **Cut.** `auto-editor` for silence, or ffmpeg trims from the approved list. Fade audio about 30 ms across each cut so it does not pop. Burn captions with `captions.py`.
4. **Filmstrip self-eval.** `review.py check` and look at `contact.jpg` plus a frame on each cut before anyone sees the cut. Hunt jumps, pops, captions under UI, and dead air. Fix and re-check.
