# Script writing

Write the script before any visuals, voice or spend. Always offer **2–3 options** (different hooks or
angles) in the plan, then lint the chosen one.

## Speaking rates (words per second)
| Read | wps | wpm |
|---|---|---|
| Calm, explainer, accessibility | 2.2 | 130 |
| Default narration | 2.5 | 150 |
| Ads, social, energetic | 2.8 | 170 |
| Fast promo (ceiling) | 3.0 | 180 |
Word budget = seconds x wps x 0.9 (keep 10% for breaths). 15 s ≈ 34 words, 30 s ≈ 68, 60 s ≈ 135.
On-screen text without VO: 3–5 words per beat, at least 1.2 s on screen, plus 0.3 s for each extra word.
BBC guidance puts reading speed at 160–180 wpm; Netflix allows up to 20 characters per second.

## Structures
- **Sizzle or promo (music-led):** Hook (0–3 s) -> 3 proof beats -> payoff -> logo + CTA. 4–8 scenes of 2–5 words.
- **Five-beat arc (narrated, 30–120 s):** Hook (~15% of words) -> Tension or problem (~25%) -> Revelation, the
  product or idea (~35%) -> Proof, a number, quote or demo (~15%) -> Resolve + CTA (~10%).
- **Story presets:** *executive brief* (state the conclusion first, 3 supporting points, ask);
  *product showcase* (problem, 3 features, stat, CTA); *impact story* (person, struggle, change, result, invitation).
- **How-to:** promise the outcome in 5 s -> numbered steps (one action each, imperative verb) -> recap -> next step.
- **Testimonial:** the quote carries it; attribution card; at most 1–2 quotes per 20 s.

## Hooks (first 3 seconds; pick one, then make it specific)
- Bold claim: "Your weekly report shouldn't take three days."
- Number: "73% of teams plan in docs, not meetings." (real, sourced numbers only)
- Question with stakes: "What if launch day was boring?"
- Before/after: "From 40 tabs to one screen."
- Callout: "If you run a five-person team, watch this."
- Pattern break: start mid-action, a striking visual or a one-word slam.
Avoid: "Hi, welcome…", "In this video…", "Have you ever wondered…", logo-first openings, throat-clearing.

## CTAs (last scene; one action, one verb)
"Start free today." · "Book a demo at site.com." · "Save the date: Nov 9." · "Follow for part 2." · "Link in bio."
Show the CTA on screen as well as saying it, and hold it at least 2 s. A URL should be short and readable.

## Writing for voice
- At most 18 words per sentence (aim for 12). Use contractions. Front-load the point. Use active voice.
- Write numbers the way you'd say them for TTS ("four times", "twenty twenty-six") and keep digits on screen.
  Spell out acronyms or add them to `pronunciations` in brand.json or the content file (applied to TTS only).
- Punctuation is pacing: a period ≈ 400 ms, a dash ≈ 200 ms, a comma ≈ 100 ms. No ellipses.
- Group in threes at most. Cut buzzwords ("revolutionary", "seamless", "leverage", "cutting-edge").
- Never invent statistics, quotes or customers. Mark sample data in templates as illustrative.

## Template: present this in the plan
```
Option A — <angle>     Option B — <angle>     (Option C — <angle>)
| # | sec | on-screen (≤5 words) | VO (≤ sec x wps words) | visual / transition |
| 1 | 3.0 | Reports take days.   | Your weekly report shouldn't take three days. | kinetic slam |
...
CTA: <verb + destination>   Music: <track, license>   Voice: <free Kokoro voice | none | paid (quote)>
```

## Lint
    script_lint.py script.json --wps 2.5 --preset tiktok      # or plain text lines: 3 | on-screen | voiceover
It checks that the VO fits each scene, on-screen text length per aspect (16:9: 42 characters, 9:16: 26,
1:1: 32), a hook within 3 s, weak openers, a CTA verb in the last scene, sentence length and the
platform's maximum length. `reelsmith.py render` lints content automatically (warnings only).
