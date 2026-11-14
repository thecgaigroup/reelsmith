"""Validate music licenses in a manifest: CC0 and CC BY (with credit) pass, everything else blocks.

Adapted from codepawl/creator-generalist (MIT), commit d3ab529a, read 2026-11-14.

This validator enforces a strict allowlist policy over a music manifest file. It does NOT download files.
Only CC0 (no credit needed) and CC BY (with a recorded credit line) are allowed. Everything else—including
NC, ND, SA when unsure, unknown licenses, and missing credit lines for CC BY—causes the validator to exit
with a non-zero code (hard fail).

Run:
  python3 scripts/validate_music_license.py manifest.json [--verbose]

Manifest format (JSON array):
  [
    {
      "file": "track.mp3",
      "title": "Track Title",
      "author": "Artist Name",
      "license": "CC BY 4.0",
      "credit": "Artist Name (source.com), CC BY 4.0",
      "source": "https://source.com/track",
      "page": "https://source.com/track-page"
    },
    ...
  ]

Exit codes:
  0 — all tracks pass
  1 — one or more tracks blocked (non-allowlisted license, missing credit for CC BY, or unknown)
  2 — manifest file cannot be read or is invalid JSON
"""

import argparse
import json
import pathlib
import sys


ALLOWED_LICENSES = {
    "CC0",
    "CC0 1.0",
    "CC BY 3.0",
    "CC BY 4.0",
}


def normalize_license(license_string):
    """Normalize a license string for comparison."""
    if not license_string:
        return None
    normalized = license_string.strip().upper()
    # Handle common variations
    normalized = normalized.replace("CC-BY", "CC BY")
    normalized = normalized.replace("CREATIVE COMMONS", "CC")
    return normalized


def validate_track(track, index):
    """Validate a single track. Returns (ok, message)."""
    file_name = track.get("file", f"track {index}")
    license_raw = track.get("license", "").strip()
    credit = track.get("credit", "").strip()
    
    if not license_raw:
        return False, f"{file_name}: license field is missing or empty"
    
    normalized = normalize_license(license_raw)
    
    # Check if it's an allowed license
    allowed = False
    is_cc_by = False
    for allowed_lic in ALLOWED_LICENSES:
        if allowed_lic in normalized:
            allowed = True
            if "CC BY" in allowed_lic and allowed_lic != "CC0":
                is_cc_by = True
            break
    
    if not allowed:
        # Check for explicitly blocked variants
        if "NC" in normalized or "ND" in normalized or "SA" in normalized:
            return False, f"{file_name}: license '{license_raw}' contains NC, ND, or SA (blocked)"
        return False, f"{file_name}: license '{license_raw}' is not in allowlist (CC0, CC BY)"
    
    # If it's CC BY, credit line is required
    if is_cc_by and not credit:
        return False, f"{file_name}: CC BY license requires a credit line (field 'credit' is missing or empty)"
    
    return True, f"{file_name}: OK ({license_raw})"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("manifest", type=pathlib.Path, help="JSON manifest file to validate")
    parser.add_argument("--verbose", action="store_true", help="Print OK tracks in addition to failures")
    args = parser.parse_args()
    
    # Read and parse manifest
    try:
        content = args.manifest.read_text(encoding="utf-8")
        tracks = json.loads(content)
        if not isinstance(tracks, list):
            print(f"Error: manifest must be a JSON array, got {type(tracks).__name__}")
            return 2
    except FileNotFoundError:
        print(f"Error: manifest file not found: {args.manifest}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in manifest: {exc}")
        return 2
    except Exception as exc:
        print(f"Error reading manifest: {exc}")
        return 2
    
    if not tracks:
        print("Warning: manifest is empty (no tracks to validate)")
        return 0
    
    # Validate each track
    failures = []
    passes = []
    for index, track in enumerate(tracks):
        ok, message = validate_track(track, index)
        if ok:
            passes.append(message)
        else:
            failures.append(message)
    
    # Report results
    if args.verbose:
        for msg in passes:
            print(msg)
    
    for msg in failures:
        print(f"BLOCKED: {msg}")
    
    print()
    print(f"{len(passes)} of {len(tracks)} tracks pass")
    if failures:
        print(f"{len(failures)} tracks BLOCKED")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
