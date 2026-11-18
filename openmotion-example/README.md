# OpenMotion example: 6.5-second kinetic title card

A HyperFrames-format project laid out for OpenMotion's Studio lint: the root `index.html` only mounts `compositions/title.html`, and that sub-composition registers its own paused timeline. The motion is transforms and opacity only. The reveal is `mask-reveal-up` with a word stagger, and an ambient grid drift runs to the last frame. There is no audio and no default look. Brand tokens come from `brand/brand.css`, with fallbacks so the card still renders unbranded.

    export OPENMOTION_TELEMETRY=0 DO_NOT_TRACK=1 HYPERFRAMES_NO_TELEMETRY=1
    OM=${REELSMITH_OPENMOTION_DIR:-/workspace/tools/openmotion}; HF="$OM/node_modules/.bin/hyperframes"   # install: references/openmotion.md
    python3 ../scripts/brand.py bundle ../brand/sample-brand.json --out .     # or your brand.json
    python3 ../scripts/openmotion_preflight.py .
    node $OM/scripts/lint-project.mjs $OM .
    $HF render . -o out/title-16x9.mp4 --format mp4 --quality draft --json
    node --experimental-strip-types $OM/scripts/verify-export.ts out/title-16x9.mp4 '{"width":1920,"height":1080,"fps":30,"duration":6.5,"audio":"silent"}'
    python3 ../scripts/review.py check out/title-16x9.mp4 --out out/_review --preset youtube --expect-seconds 6.5

Tested 2026-11-18 on OpenMotion @9e2f877 (HyperFrames 0.9.7): Studio lint 0 errors, render about 12 s at delivery quality, verify-export passed, and review.py auto PASS (it warns that there is no audio). The same project also renders on `hyperframes@0.8.197`. `brand/`, `out/` and `.hyperframes/` are generated and gitignored. `assets/gsap.min.js` is the same file as in `hyperframes-example/`.
