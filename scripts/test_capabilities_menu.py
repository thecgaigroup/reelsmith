#!/usr/bin/env python3
"""Tests for capabilities_menu.py.

Verifies menu structure, output formats, and documentation generation.
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MENU = HERE / "capabilities_menu.py"

def run_menu(*args):
    """Run capabilities_menu.py and return (exit_code, stdout)."""
    r = subprocess.run([sys.executable, str(MENU)] + list(args), 
                      capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout

def test_menu_exists():
    """capabilities_menu.py file exists."""
    assert MENU.exists(), f"{MENU} does not exist"

def test_menu_runs():
    """capabilities_menu.py runs without crashing."""
    code, out = run_menu()
    assert code == 0, f"Expected exit code 0, got {code}"
    assert len(out) > 0, "Expected output from capabilities_menu.py"

def test_menu_has_required_entries():
    """Menu includes required capability entries."""
    code, out = run_menu()
    assert "capabilities" in out.lower() and "keys" in out.lower(), \
        "Expected 'List capabilities and keys' entry"
    assert "dependencies" in out.lower() or "doctor" in out.lower(), \
        "Expected 'Check dependencies' entry"
    assert "update" in out.lower() and "reelsmith" in out.lower(), \
        "Expected 'Update Reelsmith' entry"

def test_markdown_output():
    """Menu can output markdown format."""
    code, out = run_menu("--markdown")
    assert code == 0, f"Expected exit code 0, got {code}"
    assert "-" in out and "**" in out, "Expected markdown list format"
    assert "`python3" in out, "Expected code backticks in markdown"

def test_menu_structure():
    """Menu entries have proper structure."""
    # Import and check the MENU structure directly
    sys.path.insert(0, str(HERE))
    try:
        import capabilities_menu
        menu = capabilities_menu.MENU
        assert isinstance(menu, list), "MENU should be a list"
        assert len(menu) >= 3, "Menu should have at least 3 entries"
        
        for entry in menu:
            assert "label" in entry, f"Entry missing 'label': {entry}"
            # action can be None for info-only entries
            if "action" in entry and entry["action"] is not None:
                assert isinstance(entry["action"], str), \
                    f"Action should be string or None: {entry}"
    finally:
        sys.path.pop(0)

def test_no_preview_handled():
    """Menu handles missing preview GIFs cleanly."""
    # The 'Update Reelsmith' entry has no action, which is intentional
    code, out = run_menu()
    assert code == 0, "Menu should handle entries without preview/action"
    # Should not crash or show errors
    assert "error" not in out.lower() and "traceback" not in out.lower()

def test_markdown_consistency():
    """Markdown output is consistent with plain output."""
    code_plain, out_plain = run_menu()
    code_md, out_md = run_menu("--markdown")
    
    assert code_plain == 0 and code_md == 0, "Both outputs should succeed"
    
    # Both should mention the same key terms
    for term in ["capabilities", "doctor", "update"]:
        assert term in out_plain.lower(), f"Plain output missing '{term}'"
        assert term in out_md.lower(), f"Markdown output missing '{term}'"

if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    for t in tests:
        try:
            print(f"{t}...", end=" ", flush=True)
            globals()[t]()
            print("ok")
        except Exception as e:
            print(f"FAIL\n  {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"\n{len(tests)} tests passed")
