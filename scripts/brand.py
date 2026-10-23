#!/usr/bin/env python3
"""Brand kit helper. One brand.json drives HyperFrames, Remotion and ffmpeg.

  brand.py validate brand.json                 # schema-lite + files + WCAG contrast
  brand.py bundle   brand.json --out DIR       # copy logos + fonts into DIR/brand/, write
                                               #   brand.resolved.json, brand.css, hf-variables.json
  brand.py css      brand.json                 # print CSS custom properties
  brand.py hf-vars  brand.json                 # print JSON for `hyperframes render --variables`
  brand.py from-logo logo.(svg|png|jpg) --name "Acme" -o brand.json
  brand.py from-site https://example.com -o brand.json   # one polite page fetch, no crawling
"""
import argparse, colorsys, json, re, shutil, subprocess, sys, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

UA = "reelsmith-brand/5 (+single page fetch for brand colors)"
HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
DEFAULTS = {
    "logo": {"min_height_pct": 6, "watermark": False},
    "colors": {"secondary": None, "accent": None, "muted": None, "surface": None},
    "fonts": {"body": None},
    "voice": {"tone": ["clear", "friendly"], "avoid": [], "person": "we", "cta": "Learn more", "wps": 2.5, "tts_voice": "af_heart"},
    "lower_third": {"style": "bar", "bg": "surface", "fg": "fg", "accent": "primary", "radius": 12, "position": "left"},
    "safe_margins": {"title_pct": 10, "action_pct": 5},
    "motion": {"energy": "medium", "ease": "power3.out", "corner_radius": 24},
    "music": {},
}

# ---------- color math (WCAG 2.x) ----------
def norm_hex(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()

def rgb(h):
    h = norm_hex(h)[1:]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def to_hex(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))

def luminance(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def mix(a, b, t):
    ra, rb = rgb(a), rgb(b)
    return to_hex(*[ra[i] + (rb[i] - ra[i]) * t for i in range(3)])

def sat(h):
    r, g, b = [v / 255 for v in rgb(h)]
    return colorsys.rgb_to_hls(r, g, b)[2]

# ---------- load / fill defaults ----------
def load(path):
    p = Path(path)
    b = json.loads(p.read_text())
    for k, v in DEFAULTS.items():
        if isinstance(v, dict):
            b.setdefault(k, {})
            for kk, vv in v.items():
                if b[k].get(kk) is None and vv is not None:
                    b[k][kk] = vv
    c = b["colors"]
    for k in list(c):
        if c[k]:
            c[k] = norm_hex(c[k])
    c.setdefault("secondary", None); c.setdefault("accent", None)
    c["secondary"] = c.get("secondary") or mix(c["primary"], c["fg"], 0.35)
    c["accent"] = c.get("accent") or c["secondary"]
    c["muted"] = c.get("muted") or mix(c["fg"], c["bg"], 0.4)
    c["surface"] = c.get("surface") or mix(c["bg"], c["fg"], 0.08)
    b["fonts"]["body"] = b["fonts"].get("body") or dict(b["fonts"]["heading"], weight=500)
    b["_dir"] = str(p.resolve().parent)
    return b

def token(b, v):
    return b["colors"].get(v, v) if v else v

# ---------- validate ----------
def validate(path):
    errs, warns = [], []
    try:
        raw = json.loads(Path(path).read_text())
    except Exception as e:
        print(f"FAIL: cannot parse {path}: {e}"); return 1
    for k in ("name", "colors", "fonts"):
        if k not in raw:
            errs.append(f"missing required '{k}'")
    if errs:
        print("\n".join("FAIL: " + e for e in errs)); return 1
    for k in ("bg", "fg", "primary"):
        if k not in raw["colors"]:
            errs.append(f"colors.{k} is required")
    for k, v in raw["colors"].items():
        if v and not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            errs.append(f"colors.{k}={v} is not #RRGGBB")
    if "heading" not in raw["fonts"]:
        errs.append("fonts.heading is required")
    if errs:
        print("\n".join("FAIL: " + e for e in errs)); return 1
    b = load(path)
    d = Path(b["_dir"])
    for k in ("primary", "mark", "on_dark", "on_light"):
        f = b.get("logo", {}).get(k)
        if f and not (d / f).exists():
            errs.append(f"logo.{k} file not found: {f}")
    if not b.get("logo", {}).get("primary"):
        warns.append("no logo.primary; end cards will use the name as a wordmark")
    c = b["colors"]
    checks = [("fg on bg (body text)", c["fg"], c["bg"], 4.5),
              ("fg on surface (lower thirds/cards)", c["fg"], c["surface"], 4.5),
              ("primary on bg (large text/shapes)", c["primary"], c["bg"], 3.0),
              ("accent on bg (large text)", c["accent"], c["bg"], 3.0)]
    lt = b["lower_third"]
    checks.append(("lower-third fg on its bg", token(b, lt["fg"]), token(b, lt["bg"]), 4.5))
    for name, a, bb, need in checks:
        r = contrast(a, bb)
        line = f"{name}: {r:.2f}:1 (WCAG needs {need}:1)"
        (warns if r < need else []).append(line)
        print(("ok    " if r >= need else "WARN  ") + line)
    for k in ("heading", "body"):
        f = b["fonts"][k]
        if f.get("file") and not (d / f["file"]).exists():
            errs.append(f"fonts.{k}.file not found: {f['file']}")
    for e in errs: print("FAIL: " + e)
    for w in warns:
        if "WCAG" not in w: print("WARN  " + w)
    print("RESULT:", "FAIL" if errs else ("PASS with warnings" if warns else "PASS"))
    return 1 if errs else 0

# ---------- fonts ----------
def fc_file(family, weight=700):
    if not shutil.which("fc-match"):
        return None
    r = subprocess.run(["fc-match", "-f", "%{family}|%{file}", f"{family}:weight={weight}"], capture_output=True, text=True)
    fam, _, f = r.stdout.partition("|")
    return f if f and family.lower() in fam.lower() else None

def google_font(family, weight, dest: Path):
    url = "https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(family) + f":wght@{weight}&display=swap"
    # An old UA makes Google Fonts return TTF, which ffmpeg/libass can also use.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/4.0"})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    m = re.search(r"url\((https://[^)]+)\)", css)
    if not m:
        return None
    ext = Path(urllib.parse.urlparse(m.group(1)).path).suffix or ".ttf"
    out = dest / f"{family.replace(' ', '')}-{weight}{ext}"
    out.write_bytes(urllib.request.urlopen(urllib.request.Request(m.group(1), headers={"User-Agent": UA}), timeout=60).read())
    return out

def resolve_font(b, key, dest: Path):
    f = b["fonts"][key]
    d = Path(b["_dir"])
    src = None
    if f.get("file") and (d / f["file"]).exists():
        src = d / f["file"]
    elif f.get("source", "google") != "system":
        local = fc_file(f["family"], f.get("weight", 700))
        if local:
            src = Path(local)
        else:
            try:
                return google_font(f["family"], f.get("weight", 700), dest)
            except Exception as e:
                print(f"note: could not fetch Google font {f['family']} ({e}); using system fallback", file=sys.stderr)
    if src:
        out = dest / src.name
        if not out.exists():
            shutil.copy(src, out)
        return out
    return None

# ---------- outputs ----------
def css_text(b, font_urls=None):
    c = b["colors"]
    lines = []
    for key, url in (font_urls or {}).items():
        f = b["fonts"][key]
        lines.append(f"@font-face{{font-family:'{f['family']}';src:url('{url}');font-weight:100 900;font-display:block}}")
    hf, bf = b["fonts"]["heading"], b["fonts"]["body"]
    v = [f"--{k}:{val}" for k, val in c.items() if val]
    v += [f"--font-heading:'{hf['family']}',system-ui,sans-serif", f"--font-body:'{bf['family']}',system-ui,sans-serif",
          f"--weight-heading:{hf.get('weight', 700)}", f"--weight-body:{bf.get('weight', 500)}",
          f"--tracking-heading:{hf.get('letter_spacing', '-0.02em')}", f"--radius:{b['motion'].get('corner_radius', 24)}px",
          f"--title-safe:{b['safe_margins']['title_pct']}%", f"--action-safe:{b['safe_margins']['action_pct']}%"]
    lines.append(":root{" + ";".join(v) + "}")
    return "\n".join(lines) + "\n"

def hf_vars(b):
    c = b["colors"]
    out = {"brand_name": b["name"], "tagline": b.get("tagline", ""), "url": b.get("url", ""),
           "cta": b["voice"].get("cta", "Learn more")}
    out.update({f"color_{k}": v for k, v in c.items() if v})
    out["font_heading"] = b["fonts"]["heading"]["family"]
    out["font_body"] = b["fonts"]["body"]["family"]
    return out

def bundle(path, out):
    b = load(path)
    d = Path(b["_dir"])
    dest = Path(out) / "brand"
    (dest / "fonts").mkdir(parents=True, exist_ok=True)
    res = {k: v for k, v in b.items() if k != "_dir"}
    res["logo"] = dict(b.get("logo", {}))
    for k in ("primary", "mark", "on_dark", "on_light"):
        f = b.get("logo", {}).get(k)
        if f and (d / f).exists():
            shutil.copy(d / f, dest / Path(f).name)
            res["logo"][k] = f"brand/{Path(f).name}"
    font_urls = {}
    for key in ("heading", "body"):
        p = resolve_font(b, key, dest / "fonts")
        if p:
            res["fonts"][key] = dict(b["fonts"][key], file=f"brand/fonts/{p.name}")
            font_urls[key] = f"fonts/{p.name}"
    (dest / "brand.css").write_text(css_text(b, font_urls))
    (dest / "brand.resolved.json").write_text(json.dumps(res, indent=2))
    (dest / "hf-variables.json").write_text(json.dumps(hf_vars(b), indent=2))
    print(f"bundled brand '{b['name']}' -> {dest} (fonts: {', '.join(font_urls.values()) or 'system'})")
    return res

# ---------- derive a brand ----------
def palette_from_logo(path: Path):
    if path.suffix.lower() == ".svg":
        txt = path.read_text(errors="ignore")
        cols = [norm_hex(m.group(0)) for m in HEX.finditer(txt)]
        return [c for c, _ in Counter(cols).most_common()]
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    im.thumbnail((256, 256))
    data = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
    px = [tuple(p[:3]) for p in data if p[3] > 200]
    if not px:
        return []
    q = Image.new("RGB", (len(px), 1)); q.putdata(px)
    q = q.quantize(colors=8)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    return [to_hex(*pal[i * 3:i * 3 + 3]) for _, i in counts]

def brand_from_palette(name, cols, dark=True):
    vivid = sorted([c for c in cols if sat(c) > 0.25 and 0.08 < luminance(c) < 0.8], key=lambda c: -sat(c)) or ["#4F46E5"]
    primary = vivid[0]
    secondary = vivid[1] if len(vivid) > 1 else mix(primary, "#FFFFFF", 0.35)
    bg = mix(primary, "#05070D", 0.9) if dark else mix(primary, "#FFFFFF", 0.95)
    fg = "#F8FAFC" if dark else "#0F172A"
    # Make sure primary reads on bg for large text.
    t = 0.0
    while contrast(primary, bg) < 3.0 and t < 0.6:
        t += 0.1
        primary = mix(primary, fg, 0.1)
    return {"name": name, "colors": {"bg": bg, "fg": fg, "primary": primary, "secondary": secondary,
                                    "accent": vivid[2] if len(vivid) > 2 else secondary},
            "fonts": {"heading": {"family": "Inter", "weight": 800, "source": "google"},
                      "body": {"family": "Inter", "weight": 500, "source": "google"}}}

def from_logo(logo, name, out, dark=True):
    lp = Path(logo)
    b = brand_from_palette(name or lp.stem.title(), palette_from_logo(lp), dark)
    outp = Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    dst = outp.parent / lp.name
    if dst.resolve() != lp.resolve():
        shutil.copy(lp, dst)
    b["logo"] = {"primary": lp.name}
    outp.write_text(json.dumps(b, indent=2))
    print(f"wrote {out}; review colors and fonts, then run: brand.py validate {out}")

def fetch(url, limit=2_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(limit).decode("utf-8", "ignore")

def from_site(url, out, dark=None):
    html = fetch(url)
    def meta(prop):
        m = re.search(r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]*content=["\']([^"\']+)', html, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']' + re.escape(prop), html, re.I)
        return m.group(1).strip() if m else None
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    name = meta("og:site_name") or (title.group(1).split("|")[0].split(" - ")[0].strip() if title else urllib.parse.urlparse(url).netloc)
    tagline = meta("description") or meta("og:description") or ""
    css = html
    for href in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html, re.I)[:3]:
        try:
            css += fetch(urllib.parse.urljoin(url, href), 600_000)
        except Exception:
            pass
    cols = [norm_hex(m.group(0)) for m in HEX.finditer(css)]
    theme = meta("theme-color")
    common = [c for c, _ in Counter(cols).most_common(40) if c not in ("#FFFFFF", "#000000")]
    if theme and HEX.fullmatch(theme.strip()):
        common.insert(0, norm_hex(theme))
    fams = re.findall(r"fonts\.googleapis\.com/css2?\?family=([^&\"':]+)", html)
    fams = [urllib.parse.unquote_plus(f).split(":")[0] for f in fams]
    if not fams:
        ff = Counter(m.strip().strip("'\"") for m in re.findall(r"font-family:\s*([^;,}]+)", css))
        fams = [f for f, _ in ff.most_common(5) if f.lower() not in ("inherit", "sans-serif", "serif", "monospace", "system-ui", "var(--font-sans)")]
    logo_url = None
    for pat in (r'<img[^>]+(?:class|alt|src)=["\'][^"\']*logo[^"\']*["\'][^>]*>', r'<link[^>]+rel=["\'](?:apple-touch-icon|icon)["\'][^>]*>'):
        m = re.search(pat, html, re.I)
        if m:
            s = re.search(r'(?:src|href)=["\']([^"\']+)', m.group(0))
            if s:
                logo_url = urllib.parse.urljoin(url, s.group(1)); break
    logo_url = logo_url or meta("og:image")
    outp = Path(out); outp.parent.mkdir(parents=True, exist_ok=True)
    logo_file = None
    if logo_url and not logo_url.startswith("data:"):
        try:
            ext = Path(urllib.parse.urlparse(logo_url).path).suffix or ".png"
            data = urllib.request.urlopen(urllib.request.Request(logo_url, headers={"User-Agent": UA}), timeout=30).read()
            logo_file = outp.parent / f"logo{ext}"
            logo_file.write_bytes(data)
            common = palette_from_logo(logo_file) + common
        except Exception as e:
            print(f"note: logo download failed ({e})", file=sys.stderr)
    if dark is None:
        bgs = [c for c in common[:10] if sat(c) < 0.15]
        dark = not bgs or luminance(bgs[0]) < 0.4
    b = brand_from_palette(name, common, dark)
    b["tagline"] = tagline[:60]
    b["url"] = urllib.parse.urlparse(url).netloc
    if fams:
        b["fonts"]["heading"]["family"] = fams[0]
        b["fonts"]["body"]["family"] = fams[1] if len(fams) > 1 else fams[0]
    if logo_file:
        b["logo"] = {"primary": logo_file.name}
    b["_source"] = {"url": url, "note": "Auto-derived. Confirm colors, fonts and logo rights with the brand owner."}
    outp.write_text(json.dumps(b, indent=2))
    print(f"wrote {out} (name={name!r}, primary={b['colors']['primary']}, fonts={fams[:2] or 'default'}, logo={'yes' if logo_file else 'no'})")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("validate", "css", "hf-vars"):
        sp.add_parser(c).add_argument("brand")
    p = sp.add_parser("bundle"); p.add_argument("brand"); p.add_argument("--out", required=True)
    p = sp.add_parser("from-logo"); p.add_argument("logo"); p.add_argument("--name"); p.add_argument("-o", "--out", required=True); p.add_argument("--light", action="store_true")
    p = sp.add_parser("from-site"); p.add_argument("url"); p.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    if a.cmd == "validate": sys.exit(validate(a.brand))
    if a.cmd == "css": print(css_text(load(a.brand)), end="")
    if a.cmd == "hf-vars": print(json.dumps(hf_vars(load(a.brand))))
    if a.cmd == "bundle": bundle(a.brand, a.out)
    if a.cmd == "from-logo": from_logo(a.logo, a.name, a.out, dark=not a.light)
    if a.cmd == "from-site": from_site(a.url, a.out)

if __name__ == "__main__":
    main()
