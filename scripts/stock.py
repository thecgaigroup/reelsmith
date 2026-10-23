#!/usr/bin/env python3
"""Free stock footage/photos through official APIs only. Never scrapes.

  stock.py search "city night" --type video --aspect 9:16 [--provider auto|pexels|pixabay|unsplash|openverse] [-n 5]
  stock.py get    "city night" --type video --aspect 16:9 --out assets/ [--credits credits.json] [-n 2] [--min-height 1080]
  ... add --dry-run to print the request plan (key redacted) without calling anything.

Keys (optional, env only, never printed): PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY.
Providers without a key are skipped. Openverse (CC images, no key) is the free fallback for photos.
Every download is appended to credits.json with creator, license and source URL.
Mixkit and Coverr have no public API: download by hand from their sites, then log with `stock.py credit`.
"""
import argparse, hashlib, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capabilities import has_key  # noqa: E402

UA = "reelsmith-stock/5"
CACHE = Path(os.environ.get("REELSMITH_CACHE", Path.home() / ".cache" / "reelsmith" / "stock"))
TTL = 24 * 3600  # Pixabay asks for 24 h caching; harmless for the others.
ORIENT = {"16:9": "landscape", "9:16": "portrait", "1:1": "square", "4:5": "portrait"}

def key(name):
    return os.environ.get(name, "")

def redact(url):
    return urllib.parse.urlunparse(urllib.parse.urlparse(url)._replace(query="&".join(
        p if not p.lower().startswith(("key=", "client_id=")) else p.split("=")[0] + "=***"
        for p in urllib.parse.urlparse(url).query.split("&"))))

def get_json(url, headers=None, dry=False):
    if dry:
        print(f"  DRY-RUN GET {redact(url)}" + (f"  headers: {', '.join(headers)} (values hidden)" if headers else ""))
        return None
    h = hashlib.sha1(redact(url).encode()).hexdigest()
    cf = CACHE / f"{h}.json"
    if cf.exists() and time.time() - cf.stat().st_mtime < TTL:
        return json.loads(cf.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            CACHE.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(5 * (attempt + 1)); continue
            raise SystemExit(f"{redact(url)} -> HTTP {e.code} (rate limit or bad key; key not shown)")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt < 2:
                time.sleep(3); continue
            raise SystemExit(f"{redact(url)} -> {e.__class__.__name__} (network/rate limit)")

def fit_score(w, h, aspect, min_h):
    want = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0, "4:5": 0.8}[aspect]
    return abs(w / h - want) * 10 + (0 if min(w, h) >= min_h else 5)

# ---------- providers: each returns normalized items ----------
def pexels(q, kind, aspect, n, min_h, dry):
    base = "https://api.pexels.com/videos/search" if kind == "video" else "https://api.pexels.com/v1/search"
    url = f"{base}?query={urllib.parse.quote(q)}&orientation={ORIENT[aspect]}&per_page={n}&size=medium"
    js = get_json(url, {"Authorization": key("PEXELS_API_KEY")}, dry)
    if not js:
        return []
    out = []
    for it in js.get("videos" if kind == "video" else "photos", []):
        if kind == "video":
            files = [f for f in it["video_files"] if f.get("file_type") == "video/mp4" and f.get("height")]
            files.sort(key=lambda f: (fit_score(f["width"], f["height"], aspect, min_h), -f["height"] if f["height"] <= 2160 else 9e9))
            if not files:
                continue
            f = files[0]
            out.append({"provider": "pexels", "id": it["id"], "url": f["link"], "w": f["width"], "h": f["height"], "dur": it.get("duration"),
                        "creator": it["user"]["name"], "creator_url": it["user"]["url"], "page": it["url"],
                        "license": "Pexels License", "license_url": "https://www.pexels.com/license/",
                        "attribution": f"Video by {it['user']['name']} on Pexels"})
        else:
            out.append({"provider": "pexels", "id": it["id"], "url": it["src"]["original"], "w": it["width"], "h": it["height"],
                        "creator": it["photographer"], "creator_url": it["photographer_url"], "page": it["url"],
                        "license": "Pexels License", "license_url": "https://www.pexels.com/license/",
                        "attribution": f"Photo by {it['photographer']} on Pexels"})
    return out

def pixabay(q, kind, aspect, n, min_h, dry):
    o = {"landscape": "horizontal", "portrait": "vertical", "square": "all"}[ORIENT[aspect]]
    base = "https://pixabay.com/api/videos/" if kind == "video" else "https://pixabay.com/api/"
    url = f"{base}?key={key('PIXABAY_API_KEY') or 'MISSING'}&q={urllib.parse.quote(q)}&per_page={max(3, n)}&safesearch=true"
    url += "" if kind == "video" else f"&orientation={o}&image_type=photo"
    js = get_json(url, None, dry)
    if not js:
        return []
    out = []
    for it in js.get("hits", [])[:n]:
        if kind == "video":
            vs = [dict(v, name=k) for k, v in it["videos"].items() if v.get("url")]
            vs.sort(key=lambda v: fit_score(v["width"], v["height"], aspect, min_h) + (0 if v["height"] <= 2160 else 3))
            v = vs[0]
            out.append({"provider": "pixabay", "id": it["id"], "url": v["url"], "w": v["width"], "h": v["height"], "dur": it.get("duration"),
                        "creator": it["user"], "creator_url": f"https://pixabay.com/users/{it['user']}-{it['user_id']}/", "page": it["pageURL"],
                        "license": "Pixabay Content License", "license_url": "https://pixabay.com/service/license-summary/",
                        "attribution": f"Video by {it['user']} via Pixabay"})
        else:
            out.append({"provider": "pixabay", "id": it["id"], "url": it.get("largeImageURL") or it["webformatURL"], "w": it["imageWidth"], "h": it["imageHeight"],
                        "creator": it["user"], "creator_url": f"https://pixabay.com/users/{it['user']}-{it['user_id']}/", "page": it["pageURL"],
                        "license": "Pixabay Content License", "license_url": "https://pixabay.com/service/license-summary/",
                        "attribution": f"Image by {it['user']} via Pixabay"})
    return out

def unsplash(q, kind, aspect, n, min_h, dry):
    if kind == "video":
        return []
    o = ORIENT[aspect] if ORIENT[aspect] != "square" else "squarish"
    url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(q)}&orientation={o}&per_page={n}"
    js = get_json(url, {"Authorization": "Client-ID " + key("UNSPLASH_ACCESS_KEY"), "Accept-Version": "v1"}, dry)
    if not js:
        return []
    utm = "?utm_source=reelsmith&utm_medium=referral"
    return [{"provider": "unsplash", "id": it["id"], "url": it["urls"]["full"], "w": it["width"], "h": it["height"],
             "creator": it["user"]["name"], "creator_url": it["user"]["links"]["html"] + utm, "page": it["links"]["html"] + utm,
             "download_location": it["links"]["download_location"],
             "license": "Unsplash License", "license_url": "https://unsplash.com/license",
             "attribution": f"Photo by {it['user']['name']} on Unsplash"} for it in js.get("results", [])]

def openverse(q, kind, aspect, n, min_h, dry):
    if kind == "video":
        return []
    ar = {"landscape": "wide", "portrait": "tall", "square": "square"}[ORIENT[aspect]]
    # Commercial-use, modifiable licenses only (CC0, PDM, BY, BY-SA). Each item still needs its own license check.
    lic = os.environ.get("REELSMITH_OPENVERSE_LICENSE")  # e.g. "cc0,pdm" for no-attribution assets
    filt = f"license={lic}" if lic else "license_type=commercial,modification"
    url = (f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(q)}&{filt}"
           f"&aspect_ratio={ar}&size=large&page_size={n}&mature=false")
    js = get_json(url, None, dry)
    if not js:
        return []
    out = []
    for it in js.get("results", []):
        out.append({"provider": "openverse", "id": it["id"], "url": it["url"], "w": it.get("width") or 0, "h": it.get("height") or 0,
                    "creator": it.get("creator") or "unknown", "creator_url": it.get("creator_url"), "page": it.get("foreign_landing_url"),
                    "license": f"CC {it['license'].upper()} {it.get('license_version') or ''}".strip(), "license_url": it.get("license_url"),
                    "attribution": it.get("attribution") or f"{it.get('title')} by {it.get('creator')}", "source": it.get("source")})
    return out

PROVIDERS = {"pexels": ("PEXELS_API_KEY", pexels), "pixabay": ("PIXABAY_API_KEY", pixabay),
             "unsplash": ("UNSPLASH_ACCESS_KEY", unsplash), "openverse": (None, openverse)}

def chosen(provider, kind, dry):
    names = list(PROVIDERS) if provider == "auto" else [provider]
    out = []
    for nm in names:
        env, _ = PROVIDERS[nm]
        if kind == "video" and nm in ("unsplash", "openverse"):
            continue
        if env and not has_key(env):
            print(f"  skip {nm}: {env} not set (optional; see capabilities.py for signup)")
            continue
        if env and not dry and not os.environ.get(env):
            print(f"  skip {nm}: {env} is only simulated; use --dry-run")
            continue
        out.append(nm)
    return out

def search(q, kind, aspect, provider, n, min_h, dry):
    items = []
    for nm in chosen(provider, kind, dry):
        print(f"  {nm}: searching '{q}' ({kind}, {aspect})")
        try:
            items += PROVIDERS[nm][1](q, kind, aspect, n, min_h, dry)
        except SystemExit as e:
            print(f"  {nm}: {e}")
        if items and provider == "auto" and not dry:
            break  # first provider with results wins; keeps request counts low
    if not items and not dry:
        print("  no stock results. Fallback: user media, Openverse photos, or a typographic/motion-graphics scene.")
    return items

def credit(credits, item, local):
    cp = Path(credits)
    data = json.loads(cp.read_text()) if cp.exists() else []
    rec = {k: item.get(k) for k in ("provider", "id", "creator", "creator_url", "page", "license", "license_url", "attribution", "source")}
    rec["file"] = str(local)
    rec["downloaded"] = time.strftime("%Y-%m-%d")
    data = [d for d in data if d.get("file") != rec["file"]] + [rec]
    cp.write_text(json.dumps(data, indent=2))

def download(item, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    ext = Path(urllib.parse.urlparse(item["url"]).path).suffix.lower() or (".mp4" if item.get("dur") else ".jpg")
    if ext not in (".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    dest = outdir / f"{item['provider']}-{item['id']}{ext}"
    req = urllib.request.Request(item["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    if item["provider"] == "unsplash" and item.get("download_location"):
        # Required by Unsplash API guidelines: register the download.
        get_json(item["download_location"], {"Authorization": "Client-ID " + key("UNSPLASH_ACCESS_KEY")})
    return dest

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("search", "get"):
        p = sp.add_parser(c)
        p.add_argument("query"); p.add_argument("--type", default="video", choices=["video", "photo"])
        p.add_argument("--aspect", default="16:9", choices=list(ORIENT)); p.add_argument("--provider", default="auto", choices=["auto", *PROVIDERS])
        p.add_argument("-n", type=int, default=3); p.add_argument("--min-height", type=int, default=1080); p.add_argument("--dry-run", action="store_true")
        p.add_argument("--license", default=None, help="Openverse only: e.g. cc0,pdm (default: any commercial+modifiable CC)")
        if c == "get":
            p.add_argument("--out", required=True); p.add_argument("--credits", default=None)
    p = sp.add_parser("credit", help="log a hand-downloaded file (Mixkit, Coverr, your own)")
    p.add_argument("file"); p.add_argument("--credits", required=True); p.add_argument("--provider", required=True)
    p.add_argument("--creator", default=""); p.add_argument("--page", default=""); p.add_argument("--license", required=True); p.add_argument("--license-url", default="")
    p.add_argument("--attribution", default="")
    a = ap.parse_args()
    if a.cmd == "credit":
        credit(a.credits, {"provider": a.provider, "id": Path(a.file).stem, "creator": a.creator, "page": a.page,
                           "license": a.license, "license_url": a.license_url, "attribution": a.attribution}, a.file)
        print(f"logged {a.file} in {a.credits}"); return
    if a.license:
        os.environ["REELSMITH_OPENVERSE_LICENSE"] = a.license
    items = search(a.query, a.type, a.aspect, a.provider, a.n + 2 if a.cmd == "get" else a.n, a.min_height, a.dry_run)
    if a.cmd == "search" or a.dry_run:
        for it in items:
            print(f"  [{it['provider']}] {it['w']}x{it['h']} {it.get('dur') or ''} {it['attribution']} | {it['license']} | {it['page']}")
        if a.dry_run:
            print("  DRY-RUN: nothing downloaded, no credits written.")
        return
    outdir = Path(a.out)
    credits = a.credits or str(outdir / "credits.json")
    saved = 0
    for it in items:
        if saved >= a.n:
            break
        try:
            dest = download(it, outdir)
        except Exception as e:
            print(f"  skip {it['provider']}-{it['id']}: download failed ({e.__class__.__name__})")
            continue
        saved += 1
        credit(credits, it, dest)
        print(f"  saved {dest} ({it['w']}x{it['h']}) <- {it['attribution']} [{it['license']}]")
    print(f"credits -> {credits}")

if __name__ == "__main__":
    main()
