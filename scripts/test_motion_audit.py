"""Tests for the static motion audit in review.py (`review.py audit`).

Run: python3 -m pytest scripts/test_motion_audit.py -v

Pure text fixtures; nothing is rendered.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import review

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent


def rules(text):
    return [(f["level"], f["rule"], f["line"]) for f in review.audit_text(text, "t.html")]


class LineRules(unittest.TestCase):
    def test_clean_timeline_passes(self):
        src = """
        const tl = gsap.timeline({ paused: true });
        tl.fromTo(".h", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }, 0.2);
        window.__timelines["main"] = tl;
        """
        self.assertEqual(rules(src), [])

    def test_random_clock_and_timers_fail(self):
        src = "let a = Math.random();\nlet b = Date.now();\nsetTimeout(go, 100);\nrequestAnimationFrame(tick);\n"
        got = rules(src)
        self.assertIn(("FAIL", "random", 1), got)
        self.assertIn(("FAIL", "clock", 2), got)
        self.assertIn(("FAIL", "timer", 3), got)
        self.assertIn(("FAIL", "timer", 4), got)

    def test_css_motion_fails_but_none_is_fine(self):
        src = ".a { transition: transform .3s; }\n.b { transition: none; }\n@keyframes spin { to { rotate: 1turn } }\n.c { animation-name: spin; }\n"
        got = rules(src)
        self.assertIn(("FAIL", "css-motion", 1), got)
        self.assertNotIn(("FAIL", "css-motion", 2), got)
        self.assertIn(("FAIL", "css-motion", 3), got)
        self.assertIn(("FAIL", "css-motion", 4), got)

    def test_hyphenated_property_is_not_css_motion(self):
        # transition-duration alone, or a word like "data-transition", is not a running animation
        self.assertEqual(rules('<div data-transition: x></div>\n'), [])

    def test_will_change_warns(self):
        self.assertEqual(rules(".h { will-change: transform; }\n"), [("WARN", "will-change", 1)])

    def test_comments_are_ignored_and_lines_kept(self):
        src = "/* no Math.random here\n   and no setTimeout */\n// Date.now() is banned\n<!-- requestAnimationFrame -->\nconst u = 'https://x.test/a';\nlet r = Math.random();\n"
        self.assertEqual(rules(src), [("FAIL", "random", 6)])

    def test_audit_ok_skips_a_line(self):
        self.assertEqual(rules("let r = Math.random(); // audit-ok: seeded upstream\n"), [])


class TweenRules(unittest.TestCase):
    def test_layout_tween_warns_across_lines(self):
        src = 'tl.to(".card", {\n  width: 640,\n  duration: 0.4,\n  ease: "power2.inOut"\n}, 1.0);\n'
        self.assertEqual(rules(src), [("WARN", "layout-tween", 1)])

    def test_transform_tween_is_clean(self):
        self.assertEqual(rules('tl.to(".card", { x: 120, scale: 1.02, ease: "power2.out" }, 1);\n'), [])

    def test_linear_entrance_warns(self):
        src = 'tl.from(".h", { y: 60, opacity: 0, ease: "none", duration: 0.5 }, 0);\n'
        self.assertEqual(rules(src), [("WARN", "linear-move", 1)])

    def test_linear_drift_without_fade_is_fine(self):
        src = 'tl.fromTo(".bg", { scale: 1.16, xPercent: -3 }, { scale: 1.02, xPercent: 3, ease: "none", duration: 4 }, 0);\n'
        self.assertEqual(rules(src), [])

    def test_linear_rotation_is_fine(self):
        self.assertEqual(rules('tl.to(".dial", { rotation: 360, opacity: 1, ease: "none" }, 0);\n'), [])

    def test_array_from_is_not_a_tween(self):
        self.assertEqual(rules("const xs = Array.from(nodes);\n"), [])


class TreeAndCli(unittest.TestCase):
    def test_worst_level_wins_and_vendored_files_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "index.html").write_text('<script>tl.to(".a", { left: 10 }, 0);</script>\n')
            (d / "fx.js").write_text("const n = Math.random();\n")
            (d / "assets").mkdir()
            (d / "assets" / "gsap.min.js").write_text("setTimeout(()=>{},0);Math.random();\n")
            (d / "node_modules").mkdir()
            (d / "node_modules" / "x.js").write_text("Math.random();\n")
            (d / "ok.css").write_text(".a { transform: scale(1); }\n")
            rep = review.audit(d)
            self.assertEqual(rep["level"], "FAIL")
            by = {f["file"]: f["level"] for f in rep["files"]}
            self.assertEqual(by, {"fx.js": "FAIL", "index.html": "WARN", "ok.css": "PASS"})

    def test_cli_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "index.html").write_text('<script>tl.to(".a", { x: 10 }, 0);</script>\n')
            out = d / "report.json"
            r = subprocess.run([sys.executable, str(HERE / "review.py"), "audit", str(d), "--json", str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(json.loads(out.read_text())["level"], "PASS")
            (d / "bad.js").write_text("setInterval(step, 16);\n")
            r = subprocess.run([sys.executable, str(HERE / "review.py"), "audit", str(d)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("timer line 1", r.stdout)

    def test_shipped_examples_and_templates_pass(self):
        for sub in ("hyperframes-example", "lottie-example", "templates"):
            rep = review.audit(REPO / sub)
            self.assertNotEqual(rep["level"], "FAIL", f"{sub}: {rep}")
            self.assertTrue(all(f["level"] == "PASS" for f in rep["files"]), f"{sub}: {rep}")


if __name__ == "__main__":
    unittest.main()
