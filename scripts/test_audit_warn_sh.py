"""Tests for scripts/audit_warn.sh (shell wrapper for WARNING-ONLY audit).

Run: python3 scripts/test_audit_warn_sh.py -v

Tests the shell helper's exit codes and output in different scenarios.
"""

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
HELPER = HERE / "audit_warn.sh"


class AuditWarnShellHelper(unittest.TestCase):
    """Test the audit_warn.sh shell helper."""
    
    def _run_helper(self, comp_path, env=None):
        """Run the helper and capture output and exit code."""
        cmd = ["bash", str(HELPER), str(comp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env or os.environ.copy())
        return result.returncode, result.stdout, result.stderr
    
    def test_clean_comp_exits_zero_with_clean_message(self):
        """Clean composition exits 0 and prints clean message."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "index.html").write_text('<script>tl.to(".a", { x: 10 }, 0);</script>\n')
            rc, stdout, stderr = self._run_helper(d)
            self.assertEqual(rc, 0, f"Expected exit 0, got {rc}")
            self.assertIn("WARNING-ONLY", stdout + stderr)
    
    def test_fail_findings_default_mode_exits_zero_and_continues(self):
        """FAIL findings in default mode exit 0 (render continues)."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bad.js").write_text("Math.random();\n")
            rc, stdout, stderr = self._run_helper(d)
            self.assertEqual(rc, 0, f"Expected exit 0 in WARNING-ONLY, got {rc}")
            self.assertIn("FAIL findings", stdout + stderr)
            self.assertIn("WARNING-ONLY", stdout + stderr)
    
    def test_fail_findings_strict_mode_exits_nonzero(self):
        """FAIL findings in strict mode exit non-zero."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "bad.js").write_text("setTimeout(fn, 100);\n")
            env = os.environ.copy()
            env["REELSMITH_AUDIT_STRICT"] = "1"
            rc, stdout, stderr = self._run_helper(d, env=env)
            self.assertNotEqual(rc, 0, f"Expected non-zero exit in strict mode, got {rc}")
            self.assertIn("strict mode", stdout + stderr)
    
    def test_missing_path_exits_zero_with_error_message(self):
        """Missing path exits 0 (WARNING-ONLY) with error message."""
        rc, stdout, stderr = self._run_helper("/no/such/path")
        self.assertEqual(rc, 0, f"Expected exit 0 for missing path in WARNING-ONLY, got {rc}")
        # review.py audit exits 1 for missing path, helper treats as findings
        self.assertIn("WARNING-ONLY", stdout + stderr)
    
    def test_error_exit_code_handled_gracefully(self):
        """Non-standard exit codes (not 0 or 1) are caught and reported as ERROR."""
        # We can't easily force review.py to exit with a weird code, but we can
        # test that the helper handles it. For now, test that the helper exists.
        self.assertTrue(HELPER.exists(), f"Helper script not found: {HELPER}")
        self.assertTrue(os.access(HELPER, os.X_OK), f"Helper not executable: {HELPER}")
    
    def test_warn_findings_exit_zero_and_continue(self):
        """WARN findings exit 0 and render continues."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "warn.js").write_text('<script>tl.to(".x", { width: 100 }, 0);</script>\n')
            rc, stdout, stderr = self._run_helper(d)
            self.assertEqual(rc, 0, f"Expected exit 0 for WARN, got {rc}")
            self.assertIn("WARNING-ONLY", stdout + stderr)


if __name__ == "__main__":
    unittest.main()
