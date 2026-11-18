"""Tests for automatic motion audit during render paths.

Run: python3 -m pytest scripts/test_auto_audit.py -v

Verifies that the audit runs automatically, findings are logged but don't block
in default mode, and strict mode does block on FAIL findings.
"""

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import review

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent


class AutoAuditFunction(unittest.TestCase):
    """Test the auto_audit function directly."""
    
    def test_clean_comp_passes(self):
        """Clean composition passes and returns 'clean' summary."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "index.html").write_text('<script>tl.to(".a", { x: 10 }, 0);</script>\n')
            summary = review.auto_audit(d, strict=False)
            self.assertIn("clean", summary.lower())
    
    def test_warn_only_mode_does_not_raise(self):
        """WARN findings are logged but don't raise in default mode."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "index.html").write_text('<script>tl.to(".a", { width: 100 }, 0);</script>\n')
            summary = review.auto_audit(d, strict=False)
            self.assertIn("warning", summary.lower())
    
    def test_fail_findings_do_not_raise_in_default_mode(self):
        """FAIL findings are logged but don't raise in default mode."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bad.js").write_text("let r = Math.random();\n")
            summary = review.auto_audit(d, strict=False)
            self.assertIn("FAIL", summary)
    
    def test_strict_mode_raises_on_fail(self):
        """Strict mode raises SystemExit on FAIL findings."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bad.js").write_text("setTimeout(fn, 100);\n")
            with self.assertRaises(SystemExit) as cm:
                review.auto_audit(d, strict=True)
            self.assertIn("strict mode", str(cm.exception))
    
    def test_strict_mode_from_env_var(self):
        """REELSMITH_AUDIT_STRICT=1 enables strict mode."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bad.js").write_text("Date.now();\n")
            old = os.environ.get("REELSMITH_AUDIT_STRICT")
            try:
                os.environ["REELSMITH_AUDIT_STRICT"] = "1"
                with self.assertRaises(SystemExit):
                    review.auto_audit(d)
            finally:
                if old is None:
                    os.environ.pop("REELSMITH_AUDIT_STRICT", None)
                else:
                    os.environ["REELSMITH_AUDIT_STRICT"] = old
    
    def test_missing_path_skips_gracefully(self):
        """Missing composition path logs SKIPPED."""
        summary = review.auto_audit("/no/such/path")
        self.assertIn("SKIPPED", summary)
        self.assertIn("not found", summary)
    
    def test_none_path_skips_gracefully(self):
        """None path is handled as a skip, not an error."""
        summary = review.auto_audit(None)
        self.assertIn("SKIPPED", summary)


class IntegrationTests(unittest.TestCase):
    """Integration tests for audit in render paths."""
    
    def test_hyperframes_example_has_no_fails(self):
        """The shipped hyperframes-example passes audit with no FAIL."""
        rep = review.audit(REPO / "hyperframes-example")
        self.assertNotEqual(rep["level"], "FAIL", 
                          f"hyperframes-example should pass: {rep}")
    
    def test_openmotion_example_has_no_fails(self):
        """The shipped openmotion-example passes audit with no FAIL."""
        rep = review.audit(REPO / "openmotion-example")
        self.assertNotEqual(rep["level"], "FAIL",
                          f"openmotion-example should pass: {rep}")
    
    def test_templates_pass_audit(self):
        """All shipped templates pass audit with no FAIL."""
        templates = REPO / "templates"
        if not templates.exists():
            self.skipTest("templates directory not found")
        
        for template_dir in templates.iterdir():
            if not template_dir.is_dir():
                continue
            if template_dir.name.startswith("_"):
                continue
            
            with self.subTest(template=template_dir.name):
                rep = review.audit(template_dir)
                self.assertNotEqual(rep["level"], "FAIL",
                                  f"{template_dir.name} should pass: {rep}")


class VisibilityTests(unittest.TestCase):
    """Test that audit output is always visible."""
    
    def test_summary_line_always_printed(self):
        """auto_audit always returns a summary line."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "ok.js").write_text("const x = 1;\n")
            summary = review.auto_audit(d)
            # Summary should be a non-empty string
            self.assertIsInstance(summary, str)
            self.assertTrue(len(summary) > 0)
            # Should mention "audit" and have a status
            self.assertIn("audit", summary.lower())
    
    def test_findings_count_in_summary(self):
        """Summary includes count of findings when present."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "warn.js").write_text('<script>tl.to(".x", { top: 10 }, 0);</script>\n')
            summary = review.auto_audit(d)
            # Should mention warnings
            self.assertTrue("warning" in summary.lower() or "WARN" in summary)


if __name__ == "__main__":
    unittest.main()
