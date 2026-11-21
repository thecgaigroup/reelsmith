#!/usr/bin/env python3
"""Reelsmith capabilities menu.

Defines the canonical capabilities menu that is shown in SKILL.md and README.
This is the single source of truth; documentation files are generated from it.

Usage:
    python3 capabilities_menu.py              # show the menu
    python3 capabilities_menu.py --markdown   # output as markdown list for docs
"""
import argparse, sys

# Canonical menu entries. Each entry must have "label" and "action".
# "preview" (GIF filename) is optional; missing preview is handled cleanly.
MENU = [
    {"label": "List capabilities and keys", "action": "python3 scripts/capabilities.py"},
    {"label": "Check dependencies", "action": "python3 scripts/doctor.py"},
    {"label": "Update Reelsmith", "action": None},  # No action = info only
]

def format_menu(*, markdown=False):
    """Format the menu for display or markdown output."""
    if markdown:
        lines = []
        for entry in MENU:
            label = entry["label"]
            action = entry.get("action")
            if action:
                lines.append(f"- **{label}**: `{action}`")
            else:
                lines.append(f"- **{label}**: See `python3 scripts/doctor.py` for update instructions")
        return "\n".join(lines)
    else:
        # Plain text format for terminal display
        lines = ["Reelsmith capabilities:"]
        for i, entry in enumerate(MENU, 1):
            label = entry["label"]
            action = entry.get("action")
            if action:
                lines.append(f"  {i}. {label}: {action}")
            else:
                lines.append(f"  {i}. {label}: see 'python3 scripts/doctor.py' for instructions")
        return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markdown", action="store_true", help="output as markdown for docs")
    args = ap.parse_args()
    print(format_menu(markdown=args.markdown))

if __name__ == "__main__":
    main()
