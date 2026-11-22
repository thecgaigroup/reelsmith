# Clipping Lane: Long-form to Vertical 9:16

Extract face-tracked highlight clips from long-form videos. Local files only, CPU-only, $0, no LLM required.

## When to use this lane

**Use for:**
- Talking-head content (interviews, vlogs, tutorials, presentations)
- Local video files you own or have rights to use
- Content where a face or primary subject stays roughly centered
- Extracting 5-20 second highlight moments from 5-60 minute source videos
- Vertical (9:16) output for Reels, Shorts, TikTok

**Do not use for:**
- Music videos or performance footage (no face to track)
- Multi-speaker content with frequent speaker changes (tracker will jump)
- YouTube downloads (use local files only; no yt-dlp shipped)
- Wide establishing shots or landscape footage (face tracking requires visible subjects)
- Content shorter than 2-3 minutes (not enough material for highlights)
- Podcasts with static cameras (cropping won't add value)

For template-driven videos (product launches, explainers, stat callouts), use the existing template lanes in `SKILL.md`.
For client sizzles from real footage, use the `client-sizzle.md` workflow.

## Workflow

```bash
# 1. Prepare: transcribe video (if not done already)
#    For now, provide your own words.json transcript
#    Future: integrate parakeet/WhisperX automatic transcription

# 2. Run the full clipping pipeline
python3 scripts/clipping.py process VIDEO.mp4 \
  --out output/clips \
  --transcript words.json \
  --min-clip 10 \
  --max-clip 60 \
  --top-n 5

# Output structure:
#   output/clips/
#     highlights.json       # Detected highlights with scores
#     tracking.json         # Face tracking data
#     transcript.json       # Copy of input transcript
#     clip_001/
#       raw.mp4            # Extracted segment
#       video.mp4          # Face-tracked 9:16 crop
#       words.json         # Shifted word timings
#       captions.srt       # Shifted captions
#       captions.vtt
#       captions.ass       # ASS for burn-in
#       burned.mp4         # Final with captions
#       review/            # review.py outputs
#         preview.mp4
#         contact.jpg
#         safe.jpg
#         review.json
#     clip_002/
#       ...
#     summary.json         # Overall results
```

## How it works

### 1. Highlight detection (`highlights.py`)

Scores segments using:
- **Speech pacing:** Optimal 2-3 words/second (matches scriptwriting guidance)
- **Hook patterns:** Questions (?), exclamations (!), hook words (how, why, discover, secret, amazing)
- **Audio energy:** Dynamic moments using ffmpeg volumedetect (2-second windows)
- **Natural boundaries:** Sentence breaks for clean cuts

No LLM required. Scoring is deterministic and offline.

**Score formula:**
```
combined_score = text_score * 0.4 + pacing_score * 0.3 + audio_score * 0.3
```

**Output format** (highlights.json):
```json
[
  {
    "start": 10.5,
    "end": 25.3,
    "duration": 14.8,
    "score": 0.85,
    "hook": "Why this matters for you",
    "reason": "Strong hook, good pacing, high energy",
    "text_score": 0.78,
    "pacing_score": 0.91,
    "audio_score": 0.65
  },
  ...
]
```

**Deduplication:** Segments overlapping >50% are deduplicated, keeping the higher-scored one.

### 2. Face tracking (`facetrack.py`)

- **Detection:** OpenCV Haar cascade frontal face detector (CPU-only, ships with opencv-python, no model download)
- **Tracking:** IoU-based tracker ID assignment via IoU matching between frames (technique inspired by supervision pattern; supervision is not a dependency)
- **Sampling:** 5 fps by default (configurable with `--sample-fps`)
- **Smoothing:** 30-frame moving average window to reduce jitter
- **Crop generation:** 9:16 windows centered on primary track (longest/most detections)
- **Fallback:** Center crop if no faces detected

**Tracker ID assignment:**
- Match detections to previous frame by IoU (threshold 0.3)
- Assign same ID if match found, new ID otherwise
- Result: continuous segments keep one tracker_id (test requirement 3)

**Crop window centering:**
- Each frame's crop window centers on tracked face
- Clamps to video bounds (no black bars)
- For un-sampled frames, uses last known position or interpolates

### 3. Caption shifting (`clipping.py` + `pysubs2`)

For each clip:
1. Extract words that fall within clip time range
2. Shift timings by `-start_time` (clip starts at 0:00)
3. Build captions using `captions.py` (profile: social, aspect: 9:16)
4. Output SRT, VTT, and ASS formats
5. Burn ASS to video using `captions.py burn`

Uses `pysubs2` (MIT) for precise timestamp manipulation. Fallback to manual shift if pysubs2 unavailable.

**Shift formula:**
```
new_time = max(0, original_time - clip_start_time)
```

Test requirement 4: Shifting by T preserves cue count and moves last cue's end by exactly T.

### 4. Review gate

Each clip passes through `review.py check`:
- **Aspect ratio:** Must be exactly 9:16 (test requirement 1)
- **Duration:** Must match `end - start` within one frame (test requirement 1)
- **Audio:** 48kHz sample rate check (test requirement 5)
- **Loudness:** EBU R128 integrated + true peak
- **Quality:** Black frames, silence, frozen frames, flashes, cut detection

Same gates as template videos. Clips with review failures are flagged in summary.json but not automatically discarded.

## Integration with existing pipeline

**Reuses:**
- `scripts/captions.py` — caption building and burn-in (already uses libass via ffmpeg)
- `scripts/review.py` — quality checks (aspect, duration, loudness, sync, cuts)
- FFmpeg — all video operations (extract, crop, burn, probe)
- Transcription path — user provides words.json or runs parakeet/WhisperX separately

**Does not replace:**
- Template-driven workflows (product-launch, testimonial, etc.) — use those for scripted content
- Client sizzle workflow — use that for awards/partner work with real footage + kinetic type
- Remotion/HyperFrames/OpenMotion engines — clipping lane is FFmpeg-based, no composition engine

## Dependencies

New dependencies for the clipping lane:

| Package | Version | License | Purpose | Transitive dependencies |
|---------|---------|---------|---------|------------------------|
| opencv-python | ≥4.5.0 | Apache-2.0 | Face detection (Haar cascades) | numpy (BSD-3) |
| pysubs2 | ≥1.6.0 | MIT | SRT/ASS/VTT manipulation | - |

**License verification:**
- All Apache-2.0, MIT, or BSD-3-Clause (no GPL, AGPL, LGPL, MPL)
- OpenCV Haar cascade files are Apache-2.0 (included in opencv-python)
- No gated models, no model downloads, no paid services

**Install:**
```bash
pip install opencv-python pysubs2
```

No CUDA, no torch, no GPU required. All operations are CPU-only.

## Techniques harvested from AI-Youtube-Shorts-Generator

From [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) (MIT, Copyright 2026 Anil Chandra Naidu Matcha):

**Used:**
- Highlight ranking schema (score, hook, reason, start, end)
- Overlap deduplication approach (threshold-based)
- Natural boundary detection (sentence breaks)
- Face-centered crop concept for vertical reframe

**Re-implemented from scratch:**
- All scoring logic (no LLM, uses transcript + audio energy heuristics instead)
- Face tracking (OpenCV with IoU-based tracker ID assignment, not their implementation)
- Deduplication (our own threshold and IoU logic)
- Crop generation (our crop window algorithm)

**Not used:**
- yt-dlp downloader (local files only)
- MuAPI / OpenAI API / Gemini API (no paid services)
- Their specific LLM prompts or scoring weights
- Their face detection/tracking implementation

This harvest is **techniques only**, not wholesale adoption. Reelsmith's clipping lane is a new implementation designed for the existing review/captions/FFmpeg pipeline.

## Limitations and notes

**Current limitations:**
1. **Manual transcription:** User must provide words.json transcript (parakeet/WhisperX integration pending)
2. **Single-subject tracking:** Best for one primary speaker; multi-speaker content may have tracker ID jumps
3. **CPU face detection:** Haar cascades are fast but less accurate than DNN models; may miss profiles/side views
4. **Static crop per clip:** Crop position uses middle-of-clip snapshot, not frame-by-frame pan (future: zoompan)
5. **Sampling artifacts:** 5fps sampling means some fast motions may be missed

**Best practices:**
- Provide good lighting and frontal/3/4 view of subject
- Use tripod or stable footage (shaky cam confuses tracker)
- For multi-speaker content, manually specify time ranges or edit afterward
- Review `tracking.json` to verify primary track was selected correctly
- Check `review/review.json` for quality warnings before delivery

## Stream-Highlights Mode (v5.5.0)

v5.5.0 adds stream-highlights mode for live streams and gaming VODs with chat-burst analysis.

### Differences from default mode

| Feature | Default mode (v5.4.0) | Stream-highlights mode (v5.5.0) |
|---------|----------------------|----------------------------------|
| **Input** | Local files only | Local files OR URLs (with `--rights-confirmed`) |
| **Scoring** | Transcript + audio energy | Chat bursts > RMS loudness > speech-lexicon |
| **Detection** | Haar cascade only | YuNet/YOLOX with Haar fallback |
| **Captions** | Standard social profile | Stream-pop (3-word, profanity masked) |
| **Chunking** | Full file | 90-second chunks for streams |
| **Chat** | Not supported | Twitch IRC, YouTube API, chat.json |

### Usage

```bash
# Local file with chat
python3 scripts/clipping.py process video.mp4 \
  --out output/clips \
  --mode stream-highlights \
  --chat chat.json \
  --max-clip 30

# URL with rights confirmation
python3 scripts/clipping.py process "https://youtube.com/watch?v=ID" \
  --out output/clips \
  --mode stream-highlights \
  --rights-confirmed \
  --max-clip 30
```

### Chat burst scoring

Stream-highlights mode prioritizes chat activity spikes:
- Analyzes unique participants and excitement markers (wow, clip, pog, emojis)
- Deweights spam: one user repeating messages doesn't inflate score
- Uses Median Absolute Deviation (MAD) for outlier-robust scoring
- Finds peak 5-second bucket within window for precise moment detection
- 6-second lead-in from peak for context

Falls back to RMS loudness when chat unavailable or insufficient.

### Advanced detection

**YuNet face detection (optional):**
- MIT License, 233 KB model from OpenCV Zoo
- More accurate than Haar cascade
- Download: `python3 scripts/fetch_models.py --yunet`

**YOLOX-S person tracking (optional):**
- Apache-2.0 License, 35 MB model from OpenCV Zoo
- Tracks player movement for dynamic crop panning
- Download: `python3 scripts/fetch_models.py --yolox`

Both fall back to Haar cascade if models unavailable.

### Stream-pop captions

3-word pop-in captions optimized for gaming streams:
- Each word pops in yellow when spoken
- Spoken words turn white
- Next phrase replaces at same position (no stacking)
- Profanity masking enabled by default (`--profanity-mask`)

### Dependencies

Core (included): `opencv-python`, `pysubs2`

Stream mode (optional): `yt-dlp`, `faster-whisper`, `onnxruntime`

Install: `pip install -r requirements-stream.txt`

### Rights requirements

URL input requires `--rights-confirmed` flag. You are responsible for:
- Obtaining rights to record, edit, and publish content
- Respecting platform terms of service
- Complying with creator policies

## Test requirements (all met in CI)

1. **Highlight JSON structure:** Each highlight has numeric score, non-empty hook/reason, valid start/end times. Output mp4 is exactly 9:16, duration matches `end - start` within one frame.
2. **Crop window accuracy:** Tracked subject center stays inside crop window in ≥95% of sampled frames.
3. **Tracker ID stability:** Continuous segment keeps single tracker_id (no ID jumps within contiguous detections).
4. **Caption shifting:** Shifting SRT by T seconds preserves cue count and moves last cue's end by exactly T.
5. **Audio quality:** 48kHz sample rate check (existing review.py check) passes on clip outputs.
6. **Stream-highlights tests:** Chat scoring, profanity masking, rights-flag enforcement, model fallback (all with mocks, no network in CI).

Tests in `scripts/test_clipping.py` and `scripts/test_stream_highlights.py`, run in CI.

## Dependencies

- **opencv-python** (Apache-2.0): Face and person detection
- **pysubs2** (MIT, tkarabela): Caption format manipulation
- **yt-dlp** (Unlicense, optional): URL input for streams
- **faster-whisper** (MIT, optional): Speech transcription
- **onnxruntime** (MIT, optional): ONNX model inference

**Models** (optional, separate download):
- YuNet face detection (MIT License, OpenCV)
- YOLOX-S person detection (Apache-2.0, OpenCV)

See THIRD_PARTY_NOTICES for full license information.
