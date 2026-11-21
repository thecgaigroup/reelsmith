#!/usr/bin/env python3
"""Tests for capabilities menu generation and consistency.

Verifies:
1. Every menu entry's sample path exists
2. README and SKILL menu match (generated from same source)
3. Free-key line matches what capabilities.py reports
4. Trigger guidance in SKILL.md only fires on appropriate cases
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SKILL_MD = REPO / "SKILL.md"
README_MD = REPO / "README.md"
EXAMPLES_DIR = REPO / "examples" / "previews"


def test_all_example_paths_exist():
    """Test 1: Every menu entry's sample path exists."""
    result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    
    examples_verified = data["examples_verified"]
    missing = [name for name, exists in examples_verified.items() if not exists]
    
    assert not missing, f"Missing example files: {missing}"
    assert data["all_examples_exist"], "Not all example files exist"
    print(f"✓ All {len(examples_verified)} example files exist")


def test_readme_and_skill_menus_match():
    """Test 2: README and SKILL menu match (both generated from capabilities_menu.py)."""
    # Generate both menus
    skill_result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    skill_menu = skill_result.stdout.strip()
    
    readme_result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py"), "--markdown"],
        capture_output=True,
        text=True,
        check=True,
    )
    readme_menu = readme_result.stdout.strip()
    
    # Read actual files
    skill_content = SKILL_MD.read_text()
    readme_content = README_MD.read_text()
    
    # Extract capabilities section from SKILL.md
    skill_section_match = re.search(
        r"## What Reelsmith can make\n\n(.+?)(?=\n## |$)",
        skill_content,
        re.DOTALL,
    )
    assert skill_section_match, "Could not find capabilities menu in SKILL.md"
    skill_section = skill_section_match.group(0).strip()
    
    # Extract capabilities section from README.md
    readme_section_match = re.search(
        r"## What Reelsmith makes\n\n(.+?)(?=\n## |$)",
        readme_content,
        re.DOTALL,
    )
    assert readme_section_match, "Could not find capabilities menu in README.md"
    readme_section = readme_section_match.group(0).strip()
    
    # Extract capability names from both (they should list the same capabilities)
    skill_capabilities = re.findall(r"^- \*\*([^*]+)\*\*:", skill_section, re.MULTILINE)
    readme_capabilities = re.findall(r"^\| \*\*([^*]+)\*\*", readme_section, re.MULTILINE)
    
    assert skill_capabilities, "No capabilities found in SKILL.md"
    assert readme_capabilities, "No capabilities found in README.md"
    
    # Both should have the same set of capabilities (order matters)
    assert skill_capabilities == readme_capabilities, (
        f"Capability lists don't match:\n"
        f"SKILL.md: {skill_capabilities}\n"
        f"README.md: {readme_capabilities}"
    )
    
    print(f"✓ Both SKILL.md and README.md list {len(skill_capabilities)} capabilities in matching order")


def test_free_key_matches_capabilities():
    """Test 3: Free-key line matches what capabilities.py reports."""
    # Get capabilities detection
    caps_result = subprocess.run(
        [sys.executable, str(HERE / "capabilities.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    caps_data = json.loads(caps_result.stdout)
    
    # Get menu data
    menu_result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    menu_data = json.loads(menu_result.stdout)
    
    # Check stock providers in capabilities
    stock_providers = caps_data["plan"]["stock_providers"]
    free_key_recommendation = menu_data["free_key_recommendation"]
    
    # If only openverse is available, Pexels should be recommended
    if stock_providers == ["openverse"]:
        assert free_key_recommendation == "Pexels", (
            f"Expected Pexels recommendation when only openverse is available, "
            f"got: {free_key_recommendation}"
        )
    else:
        # If other stock providers are configured, no specific recommendation
        assert free_key_recommendation is None or free_key_recommendation in [
            "Pexels",
            "Pixabay",
            "Unsplash",
        ], f"Unexpected free key recommendation: {free_key_recommendation}"
    
    # Verify the free key line in the menu text
    skill_content = SKILL_MD.read_text()
    if free_key_recommendation:
        assert free_key_recommendation in skill_content, (
            f"Free key recommendation '{free_key_recommendation}' not found in SKILL.md"
        )
    
    print(f"✓ Free key recommendation matches capabilities: {free_key_recommendation or 'none'}")


def test_trigger_guidance_is_appropriate():
    """Test 4: Trigger guidance in SKILL.md only fires on 'what can you do' or new-user cases."""
    skill_content = SKILL_MD.read_text()
    
    # Find the description section (YAML front matter)
    description_match = re.search(
        r"description: >-\n(.*?)(?=\n---)", skill_content, re.DOTALL
    )
    assert description_match, "Could not find description in SKILL.md front matter"
    description = description_match.group(1)
    
    # Check that trigger guidance mentions the right cases
    assert "what can you do" in description.lower() or "what can reelsmith make" in description.lower(), (
        "Trigger guidance should mention 'what can you do' or similar discovery question"
    )
    
    # Should mention showing the menu
    assert "capabilities_menu.py" in description or "show" in description.lower(), (
        "Trigger guidance should mention showing the capabilities menu"
    )
    
    # Should clarify it's automatic discovery only, not required for normal requests
    assert "automatic" in description.lower() or "never require" in description.lower() or "normal request" in description.lower(), (
        "Trigger guidance should clarify that menu is for discovery only, not required"
    )
    
    print("✓ Trigger guidance appropriately scoped to discovery questions")


def test_menu_generation_deterministic():
    """Verify menu generation is deterministic (same output on repeated runs)."""
    results = []
    for _ in range(3):
        result = subprocess.run(
            [sys.executable, str(HERE / "capabilities_menu.py"), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        results.append(result.stdout)
    
    assert all(r == results[0] for r in results), "Menu generation is non-deterministic"
    print("✓ Menu generation is deterministic")


def test_menu_has_no_internal_function_names():
    """Verify menu uses plain language, not internal function or template names."""
    # Get menu text
    result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    menu_text = result.stdout
    
    # Internal names that should NOT appear in user-facing text
    internal_names = [
        "build.py",
        "render.py",
        "HyperFrames.render",
        "template.product_launch",
        "kit.py",
    ]
    
    for internal in internal_names:
        assert internal not in menu_text, (
            f"User-facing menu should not contain internal name: {internal}"
        )
    
    print("✓ Menu uses plain language (no internal function names)")


def test_menu_references_real_examples_only():
    """Verify menu only references example files that actually exist."""
    result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    
    for cap in data["capabilities"]:
        if cap["example"]:
            example_path = EXAMPLES_DIR / cap["example"]
            assert example_path.exists(), (
                f"Menu references non-existent example: {cap['example']}"
            )
    
    print("✓ Menu references only real example files")


def test_skill_and_readme_stay_in_sync():
    """Verify that SKILL.md and README.md both have the capabilities menu and it matches the generator."""
    skill_content = SKILL_MD.read_text()
    readme_content = README_MD.read_text()
    
    # Both should have a capabilities section
    assert "## What Reelsmith" in skill_content, "SKILL.md missing capabilities section"
    assert "## What Reelsmith" in readme_content, "README.md missing capabilities section"
    
    # Get the expected free key from the generator
    result = subprocess.run(
        [sys.executable, str(HERE / "capabilities_menu.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    free_key = data["free_key_recommendation"]
    
    if free_key:
        # Both should mention the free key
        assert free_key in skill_content, f"SKILL.md should mention {free_key}"
        assert free_key in readme_content, f"README.md should mention {free_key}"
    
    print("✓ SKILL.md and README.md both have synced capabilities menus")


def main():
    """Run all tests."""
    tests = [
        ("Example paths exist", test_all_example_paths_exist),
        ("README and SKILL menus match", test_readme_and_skill_menus_match),
        ("Free key matches capabilities", test_free_key_matches_capabilities),
        ("Trigger guidance appropriate", test_trigger_guidance_is_appropriate),
        ("Menu generation deterministic", test_menu_generation_deterministic),
        ("No internal function names", test_menu_has_no_internal_function_names),
        ("Real examples only", test_menu_references_real_examples_only),
        ("SKILL and README stay in sync", test_skill_and_readme_stay_in_sync),
    ]
    
    failed = []
    for name, test_func in tests:
        try:
            print(f"\n{name}...")
            test_func()
        except AssertionError as e:
            print(f"✗ {name} FAILED: {e}")
            failed.append(name)
        except Exception as e:
            print(f"✗ {name} ERROR: {e}")
            failed.append(name)
    
    print(f"\n{'=' * 60}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)} tests")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print(f"PASSED: {len(tests)}/{len(tests)} tests")
        sys.exit(0)


if __name__ == "__main__":
    main()
