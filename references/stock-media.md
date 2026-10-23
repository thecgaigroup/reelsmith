# Stock footage and photos

Official APIs only. Never scrape, never spoof a Referer or browser headers, never hotlink into a render.
Keys live in env only and are never printed (`capabilities.py` shows on/off).

    stock.py search "city night" --type video --aspect 9:16 -n 5            # providers with keys, else Openverse
    stock.py get "team meeting" --type photo --aspect 16:9 --out assets/ --credits assets/credits.json
    stock.py get "ocean" --type video --dry-run                               # prints the request plan; works with no keys
    stock.py credit clip.mp4 --provider mixkit --page URL --license "Mixkit Free License" --credits assets/credits.json

| Provider | Key (env) | Get a key | Limits | Attribution |
|---|---|---|---|---|
| Pexels (video + photo) | `PEXELS_API_KEY` | pexels.com/api/new (free) | 200 requests/h, 20k/month | Credit Pexels and the creator where possible |
| Pixabay (video + photo) | `PIXABAY_API_KEY` | pixabay.com/api/docs (free account) | 100 requests/60 s; cache 24 h; download, don't hotlink | Not required; show the source when results are displayed |
| Unsplash (photo, optional) | `UNSPLASH_ACCESS_KEY` | unsplash.com/oauth/applications | Demo 50 requests/h | "Photo by X on Unsplash". `stock.py` triggers the required download endpoint |
| Openverse (CC photos, no key) | none | — | Anonymous, rate-limited | Per item; check the license |
| Coverr, Mixkit | no API | download by hand | — | Coverr: none required; Mixkit: free license |

Rules:
- Every download goes into `credits.json` with creator, license, source page and date. Copy the CC BY
  lines into the description or end card.
- Prefer clips at least as large as the target (`--min-height 1080`). Vertical: search `--aspect 9:16`
  first, then crop 16:9 with care.
- Avoid recognizable people or logos in ads unless the license covers it (Pixabay and Pexels warn about
  trademarks and model releases).
- No key, nothing found? Use the user's media, the shipped `templates/_media` (CC0) or a typographic scene.

The test images in `templates/_media/` are CC0 from Openverse; see `templates/_media/credits.json`.
