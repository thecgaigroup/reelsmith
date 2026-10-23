# Capabilities and optional keys

Reelsmith runs fully free and local with no keys. Each optional service turns on only when its key or tool
is detected. Run this first in every job:

    python3 scripts/capabilities.py            # on/off table + what this job will use + suggested keys
    python3 scripts/capabilities.py --json     # other scripts read this
    python3 scripts/capabilities.py --no-keys  # force the free path (same as REELSMITH_IGNORE_KEYS=1)
    python3 scripts/capabilities.py --simulate PEXELS_API_KEY,FAL_KEY   # testing: pretend keys exist (dry-run only)
    python3 scripts/capabilities.py --mcp fal,higgsfield                # the agent has these connectors

It checks only whether an env var is non-empty. It never prints, logs, hashes or measures a key.

| Feature | Env var(s) | Off -> fallback | Cost |
|---|---|---|---|
| Stock video + photos | `PEXELS_API_KEY`, `PIXABAY_API_KEY` | Openverse CC images, user media, typographic scenes | Free keys |
| Stock photos | `UNSPLASH_ACCESS_KEY` (optional) | Pexels/Pixabay, Openverse | Free key |
| Premium VO + word timings | `ELEVENLABS_API_KEY` + `TTS_VOICE_ID` | Kokoro (local) -> espeak-ng | Paid; quote first |
| VO / cloud transcription | `OPENAI_API_KEY` | Kokoro/espeak; local parakeet transcription | Paid; quote first |
| VO | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` (Polly) | Kokoro/espeak | Paid beyond free tier |
| AI b-roll, images, music | `FAL_KEY` or the Fal connector | stock, user media, motion graphics | Paid; quote only |
| AI video, avatars | `HIGGSFIELD_API_KEY` or the Higgsfield connector | stock, user media, motion graphics | Paid credits; quote only |
| Local tools | ffmpeg (+libass, loudnorm), node 22, espeak-ng, Kokoro, librosa, Pillow | detected; installed on first use | Free |

## Suggesting keys (never require them)
After the capability check, say once what a key would add, for example: "A free Pexels key would add stock
video. Want to add one?" Keys go in through the platform's secret prompt as env vars, never pasted in chat.
Never echo them, write them to files or put them in job.json or logs.

## Paid-use guardrails
- A paid voice runs only when it is named (`--vo elevenlabs` or `TTS_PROVIDER=elevenlabs`) AND `--allow-paid`
  is given AND the key exists. Otherwise Reelsmith prints a quote and runs the free path.
- `REELSMITH_IGNORE_KEYS=1` forces everything free, even when keys are set. Use it for tests and drafts.
- Fal/Higgsfield: quote, get approval for that specific spend, then generate. A decline is final.
- `--dry-run` everywhere prints the plan (keys redacted) and calls nothing.
