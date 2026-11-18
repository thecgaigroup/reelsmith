# Third-Party Notices

This file lists third-party code and techniques adapted into Reelsmith.

## creator-generalist

Portions of this software are adapted from [creator-generalist](https://github.com/codepawl/creator-generalist) by CodePawl.

**Source commit:** d3ab529a1270217f70666f0566af3110a9e4f74d (read 2026-11-14)

**Files adapted:**
- `references/paid-to-free-tools.md` — paid-plugin-to-free-tool mapping (from `plugins/2d-generalist/skills/edit-video/references/paid-to-free.md`)
- `references/explainer-format-signal-shorts.md` — Signal Shorts explainer format (from `plugins/2d-generalist/skills/2d-generalist/` skill and references)
- `scripts/validate_music_license.py` — music license validator (from `plugins/design-sound/skills/design-sound/references/music.md` pattern)
- `scripts/compare_look.py` and `scripts/test_compare_look.py` — deterministic render QA check (from `plugins/2d-generalist/skills/2d-generalist/scripts/`)

**License (MIT):**

```
MIT License

Copyright (c) 2026 CodePawl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## HyperFrames

Techniques adapted from [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen.

**Source commit:** d317abcdbad97cef34866ba6698e376ec2c60ad9 (read 2026-11-17)

**What was adapted (no files copied):**
- `scripts/review.py` `detect_cuts` — cut / flash / fast-move classification re-implemented in Python from the approach in `packages/cli/src/measure/cuts.ts` (64×36 grey signatures, change versus the local typical change, picture-returns test, zoom-and-shift search). Thresholds re-chosen and tested here. Changes: rewritten in Python/numpy; soft-cut and tone-histogram tests left out; a "transition" class added.
- `references/motion-design.md` (Measure a reference move), `references/storyboard.md` (Measured), `references/review-and-qa.md` (Self-eval at every cut) — practices from `skills/reverse-any-video/` restated in our words.

**License:** Apache License 2.0. HyperFrames ships no NOTICE file. The `reverse-any-video` skill itself (HyperFrames Pro, HeyGen sign-in, credits, usage beacon) is not used or installed.

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS
```

## video-use

Portions adapted from [video-use](https://github.com/browser-use/video-use) by Browser Use.

**Source commit:** 43cfc566833548093455c9d4a46bd69913b7e552 (read 2026-11-17)

**What was adapted (no files copied):**
- `scripts/review.py` `cut_clicks` and `references/review-and-qa.md` (Self-eval at every cut, Edit log) — the cut-boundary audio-pop check, the 30 ms fade rule, the three-pass self-eval cap, and the `project.md` session memory, restated and re-implemented.
- `references/helpers.md` (Filler and pause cuts) and `references/captions.md` (Captions on a cut film) — cut padding, silence thresholds, output-timeline subtitle offsets, subtitles-last, font assertion.

**License (MIT):**

```
MIT License

Copyright (c) 2026 Browser Use

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Claude Animated Shorts

Numbers adapted from [claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) by Mr omi. (Note: relationship to @dextune not independently verified; treating as a related matching public repository.)

**Source commit:** e3b817b6afc6cd413466d43f11ba31209e034bbf (read 2026-11-17)

**What was adapted (no files copied):**
- `references/motion-design.md` (Story-short camera) and `references/storyboard.md` (one-topic look reports) — measured camera, depth-of-field and render-scale numbers and the look-match practice, restated in our words. No code, reference frames or contact sheets were taken; those frames are another channel's work and are not redistributed.

**License (MIT):**

```
MIT License

Copyright (c) 2026 Mr omi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## OpenMotion

Techniques adapted from [OpenMotion](https://github.com/nexu-io/openmotion) by OpenDesign (nexu-io) and contributors.

**Source commit:** 664be5086141b09fe08b2638e43a8728c3a615b7 (read 2026-11-17)

**What was adapted (no files copied):**
- `references/motion-design.md` (Look file) — the keep / swap / capacity split, observed-inferred-deviation labels, evidence status levels, and the swap test, from `docs/motion-md.md` and `library/skills/openmotion-design-remix/references/*/MOTION_DESIGN.md`, restated in our words.
- `references/templates.md` (Launch story shapes, Direction cards) — the product-proof, detail-led and reference-rhythm outlines and the selection card, from `skills/openmotion-template-to-video/references/recipes.md`, restated in our words.
- `references/storyboard.md` (Check line, spectacle as four moments) — from `skills/openmotion-director/references/action-script.md`, restated in our words.
- `references/brand-qa.md` (Type complaint triage) — from `skills/openmotion-production/references/typography.md`, restated in our words.

**Changes:** rewritten in English for Reelsmith's lanes; brand stays in `brand.json`; added the series variety rule and house overrides (no default look, `poster-grid` never a series default). Not used: the Studio, MCP server, model gateway, motion catalog, brand design systems, bundled templates, fonts, media, and vendored libraries.

**License:** Apache License 2.0. OpenMotion ships no top-level NOTICE file. The full license text is reproduced once in this file under HyperFrames, above, and applies here unchanged. Catalog reference footage, brands, screenshots and fonts keep their original rights and were not used.
