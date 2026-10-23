# AI generation (optional, paid: quotes first)

Free options come first: user media, stock (stock-media.md), motion graphics, Kokoro/espeak voice, synth or CC music.
Only offer AI generation when it adds something these can't. Capability detection decides whether it is even
available (`FAL_KEY`/Fal connector, `HIGGSFIELD_API_KEY`/Higgsfield connector).

## Flow (every time)
1. **Propose:** shots, model, seconds, aspect, why it's needed.
2. **Quote:** Fal: `get_pricing`, then `estimate_cost` with `unit_quantity` {quantity, unit from get_pricing} (a bare
   `duration` returns unknown). Higgsfield: show the balance and the model's credit cost from its docs.
3. **Approval** for that specific spend, from the user, in chat. A decline is final; fall back to free.
4. **Draft** cheap and short (e.g. LTX or Wan class models), then a **final** (Kling or Seedance class), only if needed.
5. **Prep:** reframe or upscale for other aspects; place in `assets/broll/` and composite muted under type,
   captions and logo.
6. **Disclose** AI footage, voice and the model in the delivery and the platform's AI label.

| Need | Typical choice | Notes |
|---|---|---|
| B-roll clip | Fal video (Kling, Seedance, LTX, Wan) or Higgsfield | 5-10 s per shot; describe camera move + subject + light |
| Still / background | Fal image models | Then animate with Ken Burns for free |
| Music | Fal music models | Quote only; prefer CC / royalty-free tracks (music.md) |
| Talking avatar | Fal lip-sync / Higgsfield | **Consent of the person** + a photo the user owns |
| Premium voice | ElevenLabs / OpenAI / Polly | `--vo elevenlabs --allow-paid`; free Kokoro by default |

## Never
Generate without an approved quote; imitate real people, voices or brands without rights; clone a voice without
consent; present AI footage as real events; or put keys in files, logs or job.json.
