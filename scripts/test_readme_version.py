#!/usr/bin/env python3
"""Test that README version references match VERSION file.

Validates:
1. README H1 title does not contain a version number, OR if it does, matches VERSION
2. Any explicit 'Reelsmith vX.Y.Z' or 'current version' mentions in README match VERSION
3. Historical mentions in CHANGELOG and devlog are excluded from checks
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
README = REPO / "README.md"
VERSION_FILE = REPO / "VERSION"


def get_version() -> str:
    """Read the canonical version from VERSION file."""
    return VERSION_FILE.read_text().strip()


def check_readme_h1(readme_text: str, version: str) -> list[str]:
    """Check that README H1 doesn't have a stale version."""
    errors = []
    
    # Extract first H1
    h1_match = re.search(r'^# (.+)$', readme_text, re.MULTILINE)
    if not h1_match:
        errors.append("README has no H1 title")
        return errors
    
    h1_text = h1_match.group(1).strip()
    
    # Check if H1 contains a version
    version_pattern = r'v?\d+\.\d+\.\d+'
    version_in_h1 = re.search(version_pattern, h1_text)
    
    if version_in_h1:
        found_version = version_in_h1.group(0)
        # Normalize both versions (strip 'v' prefix if present)
        found_clean = found_version.lstrip('v')
        version_clean = version.lstrip('v')
        
        if found_clean != version_clean:
            errors.append(
                f"README H1 version '{found_version}' does not match VERSION '{version}'. "
                f"H1: '{h1_text}'"
            )
    
    return errors


def check_version_mentions(readme_text: str, version: str) -> list[str]:
    """Check explicit version mentions in README body."""
    errors = []
    
    # Pattern for explicit Reelsmith version mentions
    # Matches: "Reelsmith v5.4.0", "Reelsmith 5.4.0", "version 5.4.0", etc.
    patterns = [
        r'Reelsmith\s+v?(\d+\.\d+\.\d+)',
        r'version\s+v?(\d+\.\d+\.\d+)',
        r'current\s+version[:\s]+v?(\d+\.\d+\.\d+)',
    ]
    
    for line_num, line in enumerate(readme_text.split('\n'), 1):
        # Skip changelog-style lines (headers with dates, version brackets)
        if re.match(r'^##\s+\[?\d+\.\d+\.\d+\]?', line):
            continue
        if 'CHANGELOG' in line or 'devlog' in line:
            continue
            
        for pattern in patterns:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                found_version = match.group(1)
                version_clean = version.lstrip('v')
                
                if found_version != version_clean:
                    errors.append(
                        f"Line {line_num}: version mention '{found_version}' does not match "
                        f"VERSION '{version}'\n  Line: {line.strip()}"
                    )
    
    return errors


def test_readme_version_consistency():
    """Test that README versions are consistent with VERSION file."""
    version = get_version()
    readme_text = README.read_text()
    
    errors = []
    errors.extend(check_readme_h1(readme_text, version))
    errors.extend(check_version_mentions(readme_text, version))
    
    if errors:
        error_msg = "\n".join([
            "README version mismatches found:",
            *errors,
            f"\nVERSION file contains: {version}"
        ])
        raise AssertionError(error_msg)


def test_version_file_exists():
    """Test that VERSION file exists and is readable."""
    assert VERSION_FILE.exists(), f"VERSION file not found at {VERSION_FILE}"
    version = VERSION_FILE.read_text().strip()
    assert re.match(r'^\d+\.\d+\.\d+$', version), \
        f"VERSION file format invalid: '{version}' (expected X.Y.Z)"


def test_readme_exists():
    """Test that README.md exists."""
    assert README.exists(), f"README.md not found at {README}"


if __name__ == "__main__":
    import sys
    
    try:
        test_version_file_exists()
        test_readme_exists()
        test_readme_version_consistency()
        print("✓ All README version checks passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
