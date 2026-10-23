# Lottie example (HyperFrames)

A hand-made 2-second Lottie (`assets/pulse.json`, a looping ring and square) played frame-accurately in a 4-second HyperFrames composition. Tested with `hyperframes@0.8.188`: lint 0 errors, 4 s render in about 6 s.

    HF="npx --yes hyperframes@0.8.188"
    $HF lint && $HF snapshot --at 0,1,2,3 && $HF render -o out/lottie.mp4

How it works: load `assets/lottie.min.js` (lottie-web 5.12.2, MIT, license included), call `lottie.loadAnimation({..., autoplay: false})` and push the animation to `window.__hfLottie`. The HyperFrames runtime seeks it on every frame. For Remotion, see `LottieDemo` in the starter kit (`@remotion/lottie`).
