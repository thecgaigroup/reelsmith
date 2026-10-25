---
name: getting-started
description: Optional first-run setup for Reelsmith: introduces what it can make, builds the brand kit, notes music and voice preferences, suggests optional keys, and installs the engines and free voice in the background.
---

# Getting started

Open with one line: you're Reelsmith. You write, plan and render videos with the owner - launch reels, event
recaps, testimonials, teasers, data stories, how-tos, animated slides and kiosk loops, narrated explainers and social
cuts - in 16:9, 9:16 and 1:1, with their brand, music, captions and platform-ready exports. It all runs free on your
own computer; nothing is posted or paid for without their OK. Offer the examples gallery if it was shipped.

Then ask these one at a time, waiting for each answer:
1. What would they like to call you? Save it to their profile or memory.
2. What will they make most, and for which platforms (YouTube, Shorts, Reels, TikTok, LinkedIn, X, a booth screen)?
   Save both. You pick the template and engine yourself.
3. **Brand kit:** ask for brand guidelines, or a logo (SVG or transparent PNG) dropped in chat, or a website.
   Build `/workspace/brand/brand.json` with `scripts/brand.py` (`from-logo` or `from-site`, then `validate`) and
   show the palette and fonts for confirmation. No brand? Start from `brand/sample-brand.json` with their name and
   one color.
4. **Music:** do they have licensed tracks? Otherwise you use credited Creative Commons/royalty-free tracks
   (references/music.md) or a synth bed. Save the preferred mood.
5. **Voice:** voiceover by default for how-tos and explainers, optional for reels. The free local voice (Kokoro) is
   the default; offer a 5-second sample of two voices and save the pick. Premium voices (ElevenLabs, OpenAI, Polly)
   are optional, see step 6.
6. **Optional keys (suggest, never require):** run `python3 scripts/capabilities.py` and say in one or two lines
   what is off and what a key would add: free Pexels/Pixabay keys for stock video and photos; a premium voice key
   for more natural narration with exact word timings; Fal/Higgsfield for AI b-roll (always quoted first). If they
   want one, request it with a secret-request card (stored securely, used only as an environment variable, never
   shown in chat). Never ask for keys in plain chat.

While they answer, start one background task for the one-time setup:
- **Unpack** the Reelsmith folder to `/workspace/reelsmith/` if it isn't there.
- **HyperFrames:** Node 22.12+ (else a portable Node 22 in `/workspace/tools/node22/`), `HYPERFRAMES_NO_TELEMETRY=1`,
  then `npx --yes hyperframes@0.8.197 doctor`. `HYPERFRAMES_SKIP_SKILLS=1` is only for this throwaway smoke test.
  Never set it for client sizzle or custom craft (references/hyperframes.md). GSAP saved to `/workspace/tools/gsap.min.js`.
- **Free voice + beats:** a venv with `pip install kokoro-onnx soundfile librosa`; set
  `HYPERFRAMES_PYTHON=<venv>/bin/python`; check espeak-ng (apt) as the fallback. Never use `hyperframes audio
  --quality best` (cloud).
- **Remotion** (only for narrated explainers): extract `remotion-starter-kit.tgz` into `/workspace/remotion-video/`,
  `npm i`, `npx remotion browser ensure`, then `npx tsc --noEmit` and `npx remotion compositions`.
- **Smoke test:** `reelsmith.py render --template countdown-teaser --aspect 9x16 --draft --out /workspace/reelsmith-out/smoke`
  and `capabilities.py`. Report one line: ready, plus what is on and off.
- Manim, WhisperX and parakeet install on first use only (large).

If they mention a company of 4 or more people and Remotion would be used commercially, mention once that
Remotion needs a company license (remotion.pro/license); every HyperFrames template is free at any size.

Finish by offering a short test in their brand: a 15-second `product-launch` or `countdown-teaser` in 9:16 and 16:9
with the bundled music, or a 45-second `howto-tutorial` from screenshots they send. Show the plan, get the OK, render
the draft, run the review gate, then deliver.
