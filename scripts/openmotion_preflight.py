#!/usr/bin/env python3
"""Static preflight for an OpenMotion-ready HyperFrames project. Stdlib only, no Node, no render.

    openmotion_preflight.py PROJECT_DIR [--json]

Catches, before Node or Chrome start, the structural rules OpenMotion's Studio lint
(`scripts/lint-project.mjs`, host "studio") fails that plain HyperFrames lint only warns on:

  - root timeline clips with nested children must be mounted sub-compositions
    (`data-composition-src` -> a <template> file whose root has the same data-composition-id);
  - every composition registers a paused timeline as window.__timelines['<id>'];
  - mounted durations match the sub-composition's data-duration;
  - GSAP tweens animate transforms and opacity only (no letterSpacing, width, top, fontSize...);
  - no wall clock or randomness (Math.random, Date.now, setTimeout, setInterval, .play()).

This is a fast pre-check, not a replacement: run the real OpenMotion lint and render after it
(references/openmotion.md). Exit 0 = clean, 1 = findings, 2 = cannot read the project.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

LAYOUT_PROPS = ("letterSpacing", "wordSpacing", "lineHeight", "fontSize", "width", "height", "top", "left",
                "right", "bottom", "margin", "marginTop", "marginLeft", "padding", "paddingTop", "paddingLeft")
BANNED_CALLS = (r"Math\.random\s*\(", r"Date\.now\s*\(", r"\bsetTimeout\s*\(", r"\bsetInterval\s*\(", r"\.play\s*\(")


class _Tree(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.nodes, self.scripts, self._in_script = [], [], [], False

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "parent": self.stack[-1] if self.stack else None, "children": 0}
        if node["parent"] is not None:
            self.nodes[node["parent"]]["children"] += 1
        self.nodes.append(node)
        if tag == "script":
            self._in_script = True
            self.scripts.append("")
        if tag not in self.VOID:
            self.stack.append(len(self.nodes) - 1)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.nodes[self.stack[i]]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_script and self.scripts:
            self.scripts[-1] += data


def _parse(text):
    t = _Tree()
    t.feed(text)
    return t


def _comp_root(tree):
    for i, n in enumerate(tree.nodes):
        if "data-composition-id" in n["attrs"] and "data-composition-src" not in n["attrs"]:
            return i, n
    return None, None


def _script_findings(where, scripts, comp_id):
    out = []
    code = "\n".join(scripts)
    if comp_id and not re.search(r"__timelines\s*(\[\s*['\"]" + re.escape(comp_id) + r"['\"]\s*\]|\." + re.escape(comp_id) + r"\b)", code):
        out.append(f"{where}: composition '{comp_id}' does not register window.__timelines['{comp_id}']")
    if comp_id and "paused" not in code:
        out.append(f"{where}: timeline for '{comp_id}' is not created with paused: true")
    for pat in BANNED_CALLS:
        if re.search(pat, code):
            out.append(f"{where}: wall clock or randomness ({pat.split(chr(92))[0] or pat}) drives the render; seek the paused timeline instead")
    for m in re.finditer(r"\.(?:to|from|fromTo|set)\s*\(([^;]*?)\)\s*[,;]?", code, re.S):
        for prop in LAYOUT_PROPS:
            if re.search(r"[{,]\s*['\"]?" + prop + r"['\"]?\s*:", m.group(1)):
                out.append(f"{where}: GSAP tween animates layout property '{prop}'; animate x/y/scale/opacity instead")
    return out


def check(project):
    project = Path(project)
    findings = []
    index = project / "index.html"
    if not index.is_file():
        raise FileNotFoundError(f"{index} not found")
    for cfg in ("hyperframes.json", "meta.json"):
        p = project / cfg
        if not p.is_file():
            findings.append(f"{cfg}: missing (HyperFrames project config)")
        else:
            try:
                json.loads(p.read_text())
            except ValueError as exc:
                findings.append(f"{cfg}: invalid JSON ({exc})")
    tree = _parse(index.read_text(encoding="utf-8"))
    ri, root = _comp_root(tree)
    if root is None:
        return findings + ["index.html: no root element with data-composition-id"]
    for attr in ("data-width", "data-height", "data-duration"):
        if attr not in root["attrs"]:
            findings.append(f"index.html: root composition is missing {attr}")
    findings += _script_findings("index.html", tree.scripts, root["attrs"]["data-composition-id"])
    for n in tree.nodes:
        if n["parent"] != ri or "clip" not in n["attrs"].get("class", "").split():
            continue
        label = n["attrs"].get("id") or n["tag"]
        src = n["attrs"].get("data-composition-src")
        if not src:
            if n["children"] and n["tag"] not in ("audio", "video"):
                findings.append(f"index.html: clip <{n['tag']} id=\"{label}\"> has nested children; move it to a sub-composition (data-composition-src)")
            continue
        sub_path = project / src
        if not sub_path.is_file():
            findings.append(f"index.html: clip '{label}' mounts missing file {src}")
            continue
        text = sub_path.read_text(encoding="utf-8")
        if not text.lstrip().startswith("<template"):
            findings.append(f"{src}: sub-composition must be wrapped in <template>")
        sub = _parse(text)
        _, sroot = _comp_root(sub)
        mount_id = n["attrs"].get("data-composition-id")
        if sroot is None:
            findings.append(f"{src}: no element with data-composition-id")
            continue
        sid = sroot["attrs"]["data-composition-id"]
        if mount_id and mount_id != sid:
            findings.append(f"{src}: data-composition-id '{sid}' does not match the mount '{mount_id}'")
        try:
            if abs(float(n["attrs"].get("data-duration", "nan")) - float(sroot["attrs"].get("data-duration", "nan"))) > 1e-3:
                findings.append(f"{src}: data-duration differs from the mount in index.html")
        except ValueError:
            findings.append(f"{src}: data-duration is not a number")
        findings += _script_findings(src, sub.scripts, sid)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        findings = check(a.project)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read project: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"ok": not findings, "findings": findings}, indent=2))
    else:
        for f in findings:
            print("FAIL", f)
        print("RESULT:", "PASS" if not findings else f"{len(findings)} finding(s)")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
