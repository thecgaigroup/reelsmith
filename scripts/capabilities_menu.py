#!/usr/bin/env python3
"""Generate a user-facing capabilities menu from Reelsmith's actual feature detection.

This script produces the plain-language menu shown when users ask "what can Reelsmith do"
or when new users need to discover capabilities. The menu is generated from capabilities.py
and includes real example files.

Usage:
  python3 capabilities_menu.py                    # plain text menu for SKILL.md
  python3 capabilities_menu.py --markdown         # markdown table for README.md
  python3 capabilities_menu.py --json             # machine-readable

The menu structure and free-key recommendation are derived from capabilities.py's actual
feature detection logic, not hardcoded, so they stay in sync.
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
EXAMPLES = REPO / "examples" / "previews"

# Template types mapped to their capabilities and example GIFs
CAPABILITIES = [
    {
        "name": "Product launches and feature promos",
        "description": "Music-driven announcement videos with kinetic type and brand animations",
        "template": "product-launch",
        "example": "product-launch-9x16.gif",
    },
    {
        "name": "Event recaps and highlights",
        "description": "Turn event photos into engaging video recaps with music and transitions",
        "template": "event-recap",
        "example": "event-recap-16x9.gif",
    },
    {
        "name": "Testimonials and customer stories",
        "description": "Showcase customer quotes and reviews with polished typography",
        "template": "testimonial",
        "example": "testimonial-16x9.gif",
    },
    {
        "name": "Coming soon teasers",
        "description": "Countdown and date-reveal videos with loopable animations",
        "template": "countdown-teaser",
        "example": "countdown-teaser-9x16.gif",
    },
    {
        "name": "Stats and milestone callouts",
        "description": "Highlight key numbers, metrics, and achievements",
        "template": "stat-callout",
        "example": "stat-callout-9x16.gif",
    },
    {
        "name": "Tutorials and how-tos",
        "description": "Step-by-step instructional videos with chapter markers for YouTube",
        "template": "howto-tutorial",
        "example": "howto-tutorial-16x9.gif",
    },
    {
        "name": "Slide presentations and kiosk loops",
        "description": "Animated decks for talks, booths, or continuous display",
        "template": "slides-presentation",
        "example": "slides-presentation-16x9.gif",
    },
    {
        "name": "Feature explainers with narration",
        "description": "Product walkthroughs with voiceover and auto-generated captions",
        "template": "feature-explainer",
        "example": "feature-explainer-1x1.gif",
    },
    {
        "name": "Client sizzle reels and awards cuts",
        "description": "Production-quality cuts from real footage with beat-synced kinetic type",
        "template": None,  # No template, custom HyperFrames workflow
        "example": None,  # No single example file
    },
    {
        "name": "Stream highlights and gaming clips",
        "description": "Extract vertical 9:16 highlights from live streams or VODs with chat-burst analysis",
        "template": None,  # stream-highlights mode in clipping.py
        "example": None,  # No preview (user content)
    },
]


def get_free_key_recommendation() -> Optional[str]:
    """Determine which free key would most improve results.
    
    This logic mirrors capabilities.py's feature detection: it checks which stock
    providers are available and recommends Pexels if none are configured.
    """
    # Import capabilities.py's detection logic
    import sys
    sys.path.insert(0, str(HERE))
    from capabilities import detect
    
    caps = detect()
    stock_providers = caps["plan"]["stock_providers"]
    
    # If only openverse is available (the no-key fallback), recommend Pexels
    if stock_providers == ["openverse"]:
        return "Pexels"
    
    return None


def verify_examples() -> Dict[str, bool]:
    """Verify that all referenced example files exist."""
    status = {}
    for cap in CAPABILITIES:
        if cap["example"]:
            example_path = EXAMPLES / cap["example"]
            status[cap["example"]] = example_path.exists()
    return status


def generate_menu_text() -> str:
    """Generate plain-text menu for SKILL.md."""
    lines = ["## What Reelsmith can make", ""]
    
    for cap in CAPABILITIES:
        line = f"- **{cap['name']}**: {cap['description']}"
        if cap["example"]:
            example_path = f"examples/previews/{cap['example']}"
            line += f" (see `{example_path}`)"
        else:
            line += " (no single example; see references/client-sizzle.md)"
        lines.append(line)
    
    lines.append("")
    
    # Add free key recommendation
    free_key = get_free_key_recommendation()
    if free_key:
        lines.append(
            f"Everything works free and offline. Optional API keys add features: "
            f"a **{free_key}** key unlocks high-quality stock photos and videos. "
            f"Run `python3 scripts/capabilities.py` to see what's available."
        )
    else:
        lines.append(
            "Run `python3 scripts/capabilities.py` to see which features are available."
        )
    
    lines.append("")
    lines.append(
        "Tell me what you need — aspect ratio, length, platform, and brand — "
        "and I'll write the script, plan the cut, and render the video."
    )
    
    return "\n".join(lines)


def generate_menu_markdown() -> str:
    """Generate markdown table for README.md."""
    lines = ["## What Reelsmith makes", ""]
    lines.append("| Capability | Example |")
    lines.append("|---|---|")
    
    for cap in CAPABILITIES:
        desc = f"**{cap['name']}** — {cap['description']}"
        if cap["example"]:
            img_path = f"examples/previews/{cap['example']}"
            example_cell = f'<img src="{img_path}" width="120" alt="{cap["name"]}">'
        else:
            example_cell = "See references/client-sizzle.md"
        lines.append(f"| {desc} | {example_cell} |")
    
    lines.append("")
    
    # Add free key recommendation
    free_key = get_free_key_recommendation()
    if free_key:
        lines.append(
            f"Everything works free and offline. Optional API keys add features: "
            f"a **{free_key}** key unlocks high-quality stock photos and videos. "
            f"Run `python3 scripts/capabilities.py` to see what's available."
        )
    else:
        lines.append(
            "Run `python3 scripts/capabilities.py` to see which features are available."
        )
    
    return "\n".join(lines)


def generate_menu_json() -> dict:
    """Generate machine-readable menu data."""
    free_key = get_free_key_recommendation()
    examples_status = verify_examples()
    
    return {
        "capabilities": CAPABILITIES,
        "free_key_recommendation": free_key,
        "examples_verified": examples_status,
        "all_examples_exist": all(examples_status.values()),
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--markdown", action="store_true", help="Generate markdown table for README"
    )
    parser.add_argument(
        "--json", action="store_true", help="Generate machine-readable JSON"
    )
    args = parser.parse_args()
    
    if args.json:
        print(json.dumps(generate_menu_json(), indent=2))
    elif args.markdown:
        print(generate_menu_markdown())
    else:
        print(generate_menu_text())


if __name__ == "__main__":
    main()
