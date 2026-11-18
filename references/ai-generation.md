# AI generation (optional, paid: quotes first)

Free options come first: user media, stock (stock-media.md), motion graphics, Kokoro/espeak voice, synth or CC music.
Only offer AI generation when it adds something these can't. Capability detection decides whether it is even
available (`FAL_KEY`/Fal connector, `HIGGSFIELD_API_KEY`/Higgsfield connector).

## Stills-first approval gate (spend-safe, fail closed)

For any paid-generation path (AI b-roll, keyframes, image-to-video), generate cheap stills or keyframes first,
collect explicit human approval, and only render approved items to video. **No paid API call may proceed without
an explicit approval record.** Missing or empty approval means stop with a visible message, never a silent skip.

### Workflow
1. **Generate stills:** cheap image model (`nano_banana_pro`, FLUX, SDXL) for every concept. Stills are ~10-15x
   cheaper than video. Write each still to `assets/stills/<id>.jpg` with metadata (`stills.json`: id, prompt, model, cost).
2. **Show costs:** display the board (`stills.json` + thumbnails) with per-item video cost estimates. Total spend is
   visible before approval.
3. **Require approval:** collect explicit approval in `approvals.json` (format: `{"approved": [id1, id2, ...]}`) or
   equivalent. A human writes or confirms this file. No default approval; an empty list is valid (nothing rendered).
4. **Render only approved:** read `approvals.json` and render video only for items in the `approved` list. If the
   file is missing or unreadable, **stop with an error** (never silently skip). If `approved` is empty, log "no items
   approved, skipping render" and exit 0 (a valid outcome).
5. **Report spend:** log every paid call (model, item id, cost) and write a receipt (`spend.json`). Never spend on
   an item not in the approval record.

### Fail-closed rules
- **No approval file or parse error → STOP.** Log the error visibly and exit non-zero. Do not guess, do not skip.
- **Approved list empty → no render, no spend.** Log it and exit 0 (a valid decision).
- **Approved item missing still → STOP.** Log which item is approved but has no still, exit non-zero.
- **Never call a paid API without checking approval first.** Read and validate `approvals.json` before any video call.

### Offline helpers (optional)
- `scripts/validate_approvals.py <stills.json> <approvals.json>`: check that every approved id exists in stills,
  every id is a string, no duplicates. Exit 0 if valid, 1 with reasons otherwise.
- `storyboard.py` integration: stills go in `thumbs/`, approval status in shot metadata (`approved: true/false`).

**Source:** approach adapted from coleam00/ai-content-factory (MIT), the explore-approve-render flow. See THIRD_PARTY_NOTICES.md.

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
