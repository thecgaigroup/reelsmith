# Voiceover

Default: **free and local.** `--vo auto` uses Kokoro (natural, offline) if installed, else espeak-ng, else no VO.
Paid voices only with `--vo elevenlabs|openai --allow-paid` and the key present; otherwise a quote prints and the free
path runs. `REELSMITH_IGNORE_KEYS=1` forces free.

## Writing for the ear
Pace: about 2.5 words per second (calm 2.2, energetic 2.8-3.0); script_lint checks the fit. Short sentences,
contractions, one idea per line, numbers as spoken ("twenty-four seven"). Brand `voice.pronunciations` fixes
names (`{"SaaS": "sass"}`).

## Providers
| Provider | Cost | Word timings | Notes |
|---|---|---|---|
| Kokoro (`af_heart`, `am_michael`, …) | free, local | via transcription | `HYPERFRAMES_PYTHON=<venv>/bin/python $HF tts "…" -o vo.wav` (`--list`) |
| espeak-ng | free | estimated | robotic; drafts and fallback |
| ElevenLabs | paid | exact (`/with-timestamps`) | `eleven_multilingual_v2`; `previous_text`/`next_text` for continuity; list voices `GET /v2/voices` |
| OpenAI `gpt-4o-mini-tts` | paid | none (transcribe) | |
| Amazon Polly neural | paid beyond free tier | `word` speech marks | |
Show the `--dry-run` character count before any paid voice. Each scene is voiced separately and cached by text hash.

## Timings for captions
Paid providers with timestamps give exact word times. Otherwise: `$HF transcribe vo.wav -e parakeet --json`
(local; `$HF models install parakeet` once, 640 MB), or WhisperX for multi-speaker footage.

## Ethics
Say the voice is AI. Never clone or imitate a real person's voice without written consent.
