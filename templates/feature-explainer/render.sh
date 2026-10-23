#!/usr/bin/env bash
# Render the Remotion feature-explainer in 16:9, 9:16 and 1:1 with free local narration.
#   templates/feature-explainer/render.sh [OUT_DIR] [--draft] [--brand path/to/brand.json]
# Unpacks remotion-starter-kit.tgz into ./remotion (once), bundles the brand, generates VO
# (Kokoro or espeak; paid voices only if TTS_PROVIDER names one and its key is set),
# renders, masters loudness to -14 LUFS and writes SRT/VTT captions.
set -euo pipefail
PKG="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$PWD/out/feature-explainer}"; shift || true
DRAFT=0; BRAND="$PKG/brand/sample-brand.json"
while [ $# -gt 0 ]; do case "$1" in --draft) DRAFT=1;; --brand) BRAND="$2"; shift;; esac; shift; done
KIT="${REELSMITH_REMOTION_DIR:-$PWD/remotion}"
if [ ! -d "$KIT/src" ]; then mkdir -p "$KIT" && tar xzf "$PKG/remotion-starter-kit.tgz" -C "$KIT"; fi
cd "$KIT"
[ -d node_modules ] || npm i --no-audit --no-fund
python3 "$PKG/scripts/brand.py" bundle "$BRAND" --out public
npx --yes tsx scripts/generate-voiceover.ts src/plans/featureExplainer.ts
mkdir -p "$OUT"
Q=(); [ "$DRAFT" = 1 ] && Q=(--scale=0.5 --crf=28)
for A in 16x9 9x16 1x1; do
  npx remotion render "FeatureExplainer-$A" "out/raw-$A.mp4" "${Q[@]}"
  python3 "$PKG/scripts/export.py" loudnorm "out/raw-$A.mp4" "$OUT/feature-explainer-$A.mp4"
done
npx --yes tsx scripts/export-captions.ts src/plans/featureExplainer.ts > "$OUT/words.json"
python3 "$PKG/scripts/captions.py" build --words "$OUT/words.json" -o "$OUT/feature-explainer" --aspect 16:9
echo "done -> $OUT (next: scripts/review.py check on each file before sharing or exporting)"
