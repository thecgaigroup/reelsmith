# HyperFrames example: 12.5-second sizzle

On `hyperframes@0.8.197`: lint 0 errors, check passed. Nested-structure and dense-track warnings are still warnings, as on 0.8.188. Five scenes on a 120 BPM beat grid, music bed with fades, local GSAP (no CDN), template variables `brand`, `cta`, `accent`.

    HF="npx --yes hyperframes@0.8.197"   # Node 22.12+
    $HF lint && $HF check && $HF snapshot --at 1,2.6,5.5,7.5,11
    $HF render -o out/sizzle-16x9.mp4 --quality delivery
    $HF render -o out/custom.mp4 --variables '{"brand":"Acme","cta":"Ship it."}'

`build_sizzle.py <project> <W> <H> landscape|portrait` regenerates `index.html` for another aspect (init a sibling project with `--resolution portrait`, copy `assets/`, run it with 1080 1920 portrait). If `assets/vo/` holds `scene-01.mp3`, `scene-02.mp3` and a `manifest.json` from the skill's voiceover script, scenes 1–2 stretch to fit the VO on whole beats and get word-timed captions.

The music bed is synthetic (generated with ffmpeg), free to use.
