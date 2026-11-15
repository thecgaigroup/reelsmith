# Changelog

All notable changes to Reelsmith will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.2] - 2026-11-15

### Added
- Take-apart dossier in `references/storyboard.md`: structured reference breakdown capturing what makes exceptional films work (seen, measured, take sections covering spine, world, formal idea, hand-overs, weak spots, keeps/breaks). Take shape and pace only, never the reference's subject, words, pictures, or music. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- Five kinds of boundaries in `references/transitions.md`: every cut must be becomes / carried / matched / door / change of ground. "Next" is not a reason. Includes pointer from storyboard.md. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- Measure a reference move in `references/motion-design.md`: frame-by-frame measurement method to fit a move's speed curve as cubic-bezier. The rebuild must match the curve, not just the look. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- One-frame pop scan in `references/review-and-qa.md` and `scripts/review.py`: detect frames whose change is far larger than neighbors' (swap, reset, flash). Implemented with behavioral test in `scripts/test_pop_detection.py`. Source: James Dimachkie/video-decompiler (MIT, github.com/JimGHTB12/video-decompiler @57a7525).
- ROADMAP.md entry documenting video-decompiler fold and what was skipped (video-decompiler/raea as engine: FSL license and competes with Remotion/HyperFrames; woodxbt listicle: index already covered or parked; Hairline: web widget).

## [5.1.1] - 2026-11-14

### Added
- Archive rights gate in `references/stock-media.md`: clear guidance on allowed sources (Wikimedia Commons, Library of Congress, NARA) and rights (US public domain 1930 or earlier, federal works, CC0/BY/BY-SA); refused licenses (NC, ND, post-1930 press photos). Source: Moh4696/cinematic-skill (MIT, exploraX).
- Evidence vs illustration rule in `references/brand-qa.md`: code-drawn documents must be labelled as recreations; AI stills are illustration only, never evidence or real person stand-ins. Source: Moh4696/cinematic-skill (MIT, exploraX).
- Voice-first timing in `references/voiceover.md`: cut scratch voice first, then time picture to words; keep time-stretch within 0.90–1.15x; hits land on spoken words. Source: Moh4696/cinematic-skill (MIT, exploraX).
- Documentary preset in `references/scriptwriting.md`: cold open, bridge, forward-only chronology, sections as takes, turn, close. Includes fact_notes guidance with sources. Source: Moh4696/cinematic-skill (MIT, exploraX).
- One phrase, one way in `references/kinetic-type.md`: a phrase is either typed on screen or shown as document, never both; typed labels at least 3% of frame height. Source: Moh4696/cinematic-skill (MIT, exploraX).

## [5.1.0] - 2026-10-27
- Initial craft documentation surface with harness, motion grammar, kinetic type recipes, and sound cues.
