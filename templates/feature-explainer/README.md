# feature-explainer (Remotion)

Narrated 24 s explainer: hook -> three numbered feature cards -> stat -> logo + CTA. Uses the
Remotion starter kit (`remotion-starter-kit.tgz`, recovered from git history; it is not in the current tree), the shared `brand.json`, free local narration and
an on-screen "AI-generated voice" label.

    templates/feature-explainer/render.sh out/fe --draft      # half-res review render
    templates/feature-explainer/render.sh out/fe              # final, after review

Edit copy in `remotion/src/plans/featureExplainer.ts` (each scene has `text`, `sub` and `vo`).
Keep feature titles to about 4 words and subs to about 8. Scene length grows to fit the narration,
snapped to whole beats. The stat in the sample is marked "(sample figure)": replace it with a real,
sourced number or keep the label.
