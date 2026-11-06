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

## Stitching generated clips (ffmpeg, tested)
Each recipe below ran on real 1080p24 generated clips with ffmpeg 8.1. Rules for when to use them: `transitions.md`
(Generated clips), `motion-design.md` (Retiming), `review-and-qa.md`. Look pass: `finishing-look.md`.

- **Check the build first.** `ffmpeg -h filter=xfade` lists the transition names this build has. `ffmpeg -filters | grep -E
  'vidstab|drawtext|subtitles'`: a stock Homebrew build can lack vidstab, `drawtext` and `subtitles` (no freetype or libass).
  Do not write a recipe around a filter the build lacks. Overlay a PNG for labels instead of `drawtext`.
- **Normalize every input the same way** (`NORM`). Generated files are often untagged; pin BT.709, and `fps` gives xfade the
  shared time base it needs:
  `setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p`.
  On output: `-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv`. Uniform tags also stop a filter
  re-init glitch at joins.
- **Frame-exact trim, hard-cut concat:** input `-ss` plus a re-encode is exact (`-c copy` cuts on keyframes):
  `ffmpeg -ss 1.0 -i a.mp4 -vf "$NORM" -frames:v 72 -an -c:v libx264 -crf 18 a1.mp4`, or
  `trim=start_frame=24:end_frame=96,setpts=PTS-STARTPTS,$NORM`. Then `-f concat -safe 0 -i list.txt -c copy cut.mp4`,
  safe only because every segment was encoded identically.
- **xfade by name:** `[0:v][1:v]xfade=transition=fade:duration=0.5:offset=2.5,format=yuv420p[v]`. For lengths d0…dn and
  fades f0…, `offset_k = (d0+…+dk) − (f0+…+fk)` and `total = Σd − Σf` (3 s + 3 s with 0.5 s gives offset 2.5, 5.5 s).
  Always add `format=yuv420p` after xfade, or x264 may pick 4:4:4. On a song master, give the outgoing shot an `s`-second
  tail handle and set the offset to the cut point, so the total does not shrink.
- **Fade through black:** `xfade=transition=fadeblack:duration=1.0:offset=…`. Head and tail of the finished picture:
  `fade=t=in:st=0:d=1` and `fade=t=out:st=<end−d>:d=<d>`, video only.
- **Audio splices (teasers, cutdowns, never the continuous master):** per piece
  `atrim=start=S:duration=D,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=D-0.03:d=0.03`, then `concat=n=N:v=0:a=1`.
  Measured at a splice: the sample step was 28x the median without the 30 ms fades, below the median with them. A blended
  audio join between separate sources: `acrossfade=d=0.5:c1=tri:c2=tri`.
- **Still-hold push-in (animatic, gaps):** `scale=3840:-2:flags=lanczos,zoompan=z='1.00+0.0400*on/95':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=96:s=1920x1080:fps=24,setsar=1,format=yuv420p`
  (`d` = output frames per image; upscale first or zoompan steps).
- **Speed ramp (non-face crops only):** `split[s0][s1];[s0]trim=0:1,setpts=PTS-STARTPTS[a];[s1]trim=1:3.5,setpts=(PTS-STARTPTS)/1.25[b];[a][b]concat=n=2:v=1:a=0,fps=24`.
- **Two-pass loudnorm, only when the creator asks** (`review-and-qa.md`, music delivery): pass 1
  `loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null -` and read `input_i`, `input_tp`, `input_lra`, `input_thresh`,
  `target_offset`; pass 2 `loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=…:linear=true:print_format=json,aresample=48000`.
  Tested: −12.46 to −14.16 LUFS, `normalization_type: linear`. `dynamic` means it compressed: stop and say so.
- **Mux the master last, no loudness processing** (AAC 256k is the only change): `ffmpeg -i picture.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart out.mp4`.
- **Encodes.** Graded master: `libx264 -preset medium -crf 20 -tune grain -pix_fmt yuv420p` (~54 Mbps with grain).
  Intermediate segments: crf 18. Upload copy: `-preset slow -crf 22 -tune grain` (~28 Mbps), AAC 48 kHz 256k, `+faststart`.
  Hardware encoders (VideoToolbox) for review proxies only.

## Spoken / raw takes (post)
Use this when the job is cutting talking-head, interview, or other raw spoken selects. Client sizzles stay
storyboard-first (`storyboard.md`); this does not replace that board.

Pattern only — do **not** install [browser-use/video-use](https://github.com/browser-use/video-use) or add it as a dependency.

1. **Transcript first.** Transcribe with the tools above (`$HF transcribe` or WhisperX). Read words and times. Do not dump every frame into the prompt.
2. **EDL, then confirm.** Write a short list: source, in, out, why (keep / drop filler / drop a false start). Show it. Do not cut until the user says yes.
3. **Cut.** `auto-editor` for silence, or ffmpeg trims from the approved list. Fade audio about 30 ms across each cut so it does not pop (only where audio is spliced; a picture cut over one continuous track needs none). Burn captions with `captions.py`.
4. **Filmstrip self-eval.** `review.py check` and look at `contact.jpg` plus a frame on each cut before anyone sees the cut. Hunt jumps, pops, captions under UI, and dead air. Fix and re-check.
