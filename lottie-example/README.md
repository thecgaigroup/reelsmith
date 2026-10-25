# Lottie example (HyperFrames)

A hand-made 2-second Lottie (`assets/pulse.json`, a looping ring and square) played frame-accurately in a 4-second HyperFrames composition. On `hyperframes@0.8.197`: lint 0 errors, check passed, snapshot at 0, 1, 2 and 3 s.

    HF="npx --yes hyperframes@0.8.197"
    $HF lint && $HF snapshot --at 0,1,2,3 && $HF render -o out/lottie.mp4

How it works: load `assets/lottie.min.js` (lottie-web 5.13.0, MIT, license included), call `lottie.loadAnimation({..., autoplay: false})` and push the animation to `window.__hfLottie`. The HyperFrames runtime seeks it on every frame. For Remotion, see `LottieDemo` in the starter kit (`@remotion/lottie`).
