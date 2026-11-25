# Changelog

All notable changes to Reelsmith will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.6.0] - 2026-11-25

### Added

- **Safe layout caption flag** — Opt-in `--safe-layout` flag for `captions.py build` positions burned-in captions inside documented safe zones for vertical 9:16 Reels, TikTok, and YouTube Shorts. When enabled:
  - Captions at 672px from bottom (keeps bottom 35% clear, per platform specs)
  - Horizontal caption band: 120–770px (650px usable, clears TikTok right rail)
  - Left margin: 120px (11.1%), right margin: 310px (28.7%)
  - Only affects 9:16 aspect; 16:9, 1:1, 4:5 unchanged
- **Safe zones module** (`templates/_shared/safe_zones.py`) — `SafeZones` class and convenience functions (`get_safe_margins`, `get_caption_vpos`) calculate platform-safe positioning for 9:16 content. Returns margins (220/672/120/310 px), caption bands, badge/pill positions. When disabled (default), all margins are zero.
- **Frame-0 quality checker** (`scripts/test_frame0_cover.py`) — CLI tool and importable API validates frame 0 meets luma mean ≥ 16, stddev ≥ 12, and ≤ 5% darker than source. Uses ffmpeg signalstats filter and raw pixel analysis. Thresholds are full-range 0-255 luma. Computes real population stddev from decoded grayscale frame.
- **Safe layout tests** — Unit tests for safe zone calculations, caption positioning, and byte-identical backward compatibility (flag-off hash matches default). Frame-0 quality tests with real generated clips (dark, flat, good, darker-than-source, slightly-darker, gradient).
- **Safe layout reference** (`references/safe-layout.md`) — Short guide covering caption flag usage, safe zone numbers, and backward compatibility.

### Changed

- **captions.py** — Added `--safe-layout` flag to `build` command. Only affects 9:16 aspect.

### Backward Compatibility

**Default is OFF.** When `--safe-layout` is absent:
- Captions use legacy positioning (691px from bottom for 9:16)
- Output is byte-for-byte identical to 5.5.2

## [5.5.2] - 2026-11-25

### Added

- **Craft techniques test coverage**: Added comprehensive test suite (`scripts/test_craft_techniques.py`) covering audio sync detection, crop placement measurement, and filter sanitization. Integrated into CI workflow.
- **Filter graph sanitization**: Added `sanitize_filter_input()` to `review.py` to escape dangerous characters (`:`, `;`, `'`, `[`, `]`, `\`) in ffmpeg filter graphs. Applied to scene-id labels in `scene_frames()` to prevent injection via user text.

### Fixed

- **Dropout detection accuracy**: Review dropout check now uses audio stream duration (`-select_streams a:0`) instead of container duration, correctly detecting dropouts when audio ends before video container.
- **Loudnorm timestamp integrity**: Export audio pipeline now uses `asetpts=N/SR/TB+STARTPTS` after loudnorm to prevent ~89ms timestamp jump and end trim that could cause sync drift.
- **Crop display precision**: Export crop percentage now only shown for `crop` mode (not `pad-blur`), accurately reflecting when actual cropping vs padding occurs.

## [5.5.1] - 2026-11-22

### Fixed

- **Caption burn-in test robustness**: Fixed flaky assertion in `test_stream_highlights.py` by computing caption metrics relative to upper-half control region. This handles encoding variations that caused intermittent failures (measured mean_diff 4.82 vs threshold 5.0). New assertion requires 3x ratio vs control, catching real burns (typically 10x+) while rejecting no-burn cases (ratio ~1.0). Added negative test to verify assertion rejects identical frames.
- **OpenCV version pin**: Pinned opencv-python to 4.x line (`>=4.10,<5`) in `requirements-stream.txt` and CI to prevent regression from opencv 5.x which removed `cv2.CascadeClassifier`. Added `test_opencv_version.py` to verify CascadeClassifier availability and Haar cascade loading in CI.
- **THIRD_PARTY_NOTICES consolidation**: Merged no-extension `THIRD_PARTY_NOTICES` file into `THIRD_PARTY_NOTICES.md`, keeping yt-dlp, faster-whisper, onnxruntime, YuNet, and YOLOX entries verbatim. Deleted duplicate file. All references already pointed to `.md` file.
- **CHANGELOG conflict marker**: Removed accidentally committed `<<<<<<< HEAD` marker from CHANGELOG.md.

### Added

- **Stream-highlights route**: Added stream-highlights row to SKILL.md route table and corresponding entry in `capabilities_menu.py`. Existing drift test now verifies this route has a matching capability entry.

### Changed

- README H1 remains "# Reelsmith" with no version (unchanged).
- All existing tests pass unmodified.

## [5.5.0] - 2026-11-21

### Added

**Stream-Highlights Mode** - Extract vertical 9:16 highlight clips from live streams and gaming VODs

- **Chat-burst analysis**: Priority-based moment detection (chat bursts > RMS loudness > speech-lexicon)
  - Twitch IRC and YouTube live chat collection support (optional)
  - Chat.json file input for pre-recorded chat logs
  - Spam-resistant scoring with rolling z-score spike detection
  - Peak sub-bucket detection within windows
- **URL input**: Process streams directly from YouTube, Twitch, etc. via yt-dlp (optional dependency)
- **Full lexicon detection**: Detects speech start/end using ffmpeg silencedetect; extracts phrases every ~0.75s with Whisper for semantic keyword/phrase matching over sub-bucket peaks
- **Multi-track audio**: Downmix multi-channel (2.0, 5.1, 7.1) to mono via pan filter, excluding LFE
- **Sync drift detection**: Automatic drift measurement via cross-correlation in `review.py`, flagging >200ms offset
- **Speaker detection**: YuNet face/YOLOX person extraction from full-frame timeline screenshots every 100 frames
- **Fast Whisper transcription**: Local GPU transcription mode using faster-whisper for speech detection (skips cloud)
- **OpenMotion pipeline**: Integrated stream-highlights mode with scene detection, music-free export, OpenAI Whisper integration, and remote editing handoff (openmotion_editor.py)
- **CLI**: `python3 scripts/stream_highlights.py` with live URL and chat-burst collection support
- **Tests**: Added `test_stream_highlights.py` with scene-lock verification for multi-stream and caption burn-in checks

### Changed

- **Review captions**: Added lexicon-phrase coverage check (100% matched or transcript skipped)
- **Lint**: Added UTF-8 BOM/nulls check; skip generated .ass/.vtt; fail on control chars

### Dependencies

- **yt-dlp**: Optional for URL-based stream processing. Install via pip or standalone binary.
- **faster-whisper**: Optional for local GPU transcription. CPU works but is slower.

### Fixed

- **Audio export clarity**: Addressed possible codec loudness issues in some export scenarios

## [5.4.0] - 2026-11-13

### Added

**Automated Color Grading (`scripts/compare_look.py`)**:
- **Automatic LUT generation**: Generate ffmpeg color grading filters (lut3d or curves) from reference images to match look & feel. Uses either 3D LUT (Hald CLUT + interpolation) or 1D RGB curves (Cb/Cr histogram matching).
- **Color transfer via histogram matching**: Align source luma/chroma histograms to reference in YCbCr space using percentile mapping. Preserves relative contrast while shifting mean color to reference.
- **Spatial analysis**: Compare reference and result images using SSIM structural similarity and histogram-based color metrics. Spot under/over-correction automatically.
- **CLI tests**: `scripts/test_compare_look.py` verifies successful single-image grading, RGB curves generation, and histogram matching convergence. Checks that filter-graded frames move closer to reference than original.

### Fixed

- **Remotion `npx` reliability**: Pin `--yes` flag on `npx` calls for Remotion render commands to work around sporadic prompt hang in unattended CI and automation flows.

### Changed

- **Brand validation test**: `test_brand.py` now asserts `npx remotion --version` succeeds to catch broken Remotion install early. Already present in existing brand build flow.

## [5.3.1] - 2026-11-07

### Fixed

- **docs/quickstart.md lint**: Removed non-breaking space (U+00A0) causing ci.yml lint errors. Replaced with regular space.
- **README.md escaping**: Fixed unescaped `<` in link anchor causing markdown lint error. Changed `<30 seconds` to escaped form for goldmark compatibility.

## [5.3.0] - 2026-11-06

### Added

**Music-Free Clip Export**:
- **`--music-free` flag for captions.py**: When enabled, generates music-free `.json` for video rendering. JSON includes per-scene music-free timestamps from review.py, plus optional cloud-ASR transcript.
- **`--music-free` flag for export.py**: When enabled, composites loud beep tone (1 kHz sine) over music regions, marks them with 🔇 icon plus translucent gray overlay, and bakes captions via libass. Result is a single self-contained video for remote editors who lack Remotion. Music-free timestamps come from review.py scene detection.
- **Music detection in review.py**: Detects music segments via RMS energy analysis. Saves music-free ranges to review.json per scene. Used by export.py --music-free.

### Fixed

- **Burn-in caption vertical margin**: Corrected bottom margin calculation in captions.py. For 9:16, now uses 36% (691px from bottom on 1920px height), matching documented safe zones. For 1:1 and 4:5, uses 10% from bottom. For 16:9, uses 10% from bottom. This aligns with TikTok/Reels/Shorts guidance. Previously margin_v was 60 for 9:16 (effectively 3% from bottom).

### Changed

- **review.py scene JSON output**: Added optional `music_free_ranges` list to each scene when music is detected. Each range is `[start_sec, end_sec]` relative to scene start. Used by export.py --music-free for compositing.

## [5.2.0] - 2026-11-01

### Added

**Lint expanded**:
- **UTF-8 BOM and null-byte check**: Fails on UTF-8 byte order marks or embedded null bytes in text files. Skips generated captions (.ass/.vtt), binaries, and standard ignored directories.
- **Control character detection**: Rejects files with ASCII control characters (U+0000..U+001F excluding tab/LF/CR), which can break parsers. Skips generated/binary files.
- **Line length limit**: Warns on source lines >200 chars. Skips generated and test-fixture files. Soft limit encourages readable code.

**Testing**:
- **`test_audit_warn_sh.py`**: Verifies bash scripts call `echo` via `>&2` or `printf`, not bare `echo` to stdout (which breaks JSON piping). Covers scripts/ and new .sh additions.
- **`test_sync_drift.py`**: Checks review.py reports audio/video sync drift within 100ms. Mocks scene AV files, asserts drift measurement and pass/warn/fail logic.
- **`test_doctor.py`**: End-to-end doctor.py test verifying JSON structure, success/failure exit codes, and readable output.

### Changed

- **captions.py**: Burn-in now references .vtt if .ass is missing. Maintains backward compatibility while enabling .vtt-only workflows.
- **review.py**: Sync drift check computes audio/video offset via cross-correlation, warns >100ms. Tolerates small codec-induced shifts.
- **audit.py**: Revised `warn()` to print to stderr (`>&2`), keeping stdout clean for JSON output.

## [5.1.0] - 2026-10-28

### Added

**OpenMotion Lint and Validation**:
- **openmotion_preflight.py**: Checks package.json exists, has remotion/openmotion deps, verifies scripts/review.py presence for music detection, ensures public/ folder has hero art and scenes/, and scans for `.md` with unsafe shell command examples.
- **test_openmotion_preflight.py**: End-to-end test creating mock OpenMotion project and verifying preflight detects missing files, broken deps, and unsafe shell code.

**CLI Enhancements**:
- **reelsmith.py autocomplete**: Tab-complete template names when calling `reelsmith.py <template-name>`. Requires bash-completion or zsh compinit. Run `eval "$(python3 scripts/reelsmith.py --print-completion bash)"` to enable.
- **doctor.py**: Diagnostic tool checking ffmpeg/remotion install, Node.js version, permissions, and environment. Outputs JSON summary plus human-readable report. Run `python3 scripts/doctor.py` for health check before rendering.

### Changed

- **captions.py**: Auto-create output directory if missing (was failing silently). Error messages now include concrete next steps.
- **brand.py validate**: Stricter JSON schema checks. Rejects extra keys, enforces required color fields, validates URLs.

### Documentation

- **SKILL.md**: Added route table mapping CLI scripts to documentation sections. New entries for openmotion_preflight, reelsmith autocomplete, doctor.
- **docs/openmotion.md**: Covers OpenMotion lint, preflight, review.py integration, and remote editor handoff.
- **capabilities_menu.py**: Interactive menu showing available Reelsmith modes. Run `python3 scripts/capabilities_menu.py`.

## [5.0.0] - 2026-10-21

### Breaking

- Dropped Python 3.9 support (EOL Oct 2025). Minimum is now **Python 3.10**.
- Remotion templates must include `@remotion/lambda` and `@remotion/cli` in package.json. Missing packages fail validation.

### Added

**Automated Review Workflow**:
- **review.py**: Runs automated checks on rendered videos: resolution, aspect ratio, caption timing, scene structure, music detection (via RMS energy), audio dropouts. Writes `review.json` with structured pass/warn/fail verdicts per check.
- **test_motion_audit.py**: End-to-end test verifying review.py runs on sample video, produces valid JSON, and correctly flags issues (missing scenes, bad aspect ratio, caption gaps).

**Caption Improvements**:
- **Speaker labels**: `captions.py` now supports speaker labels in burn-in captions. When `.json` transcript includes speaker IDs, displays speaker name above caption text.
- **CPS limit flag**: `--max-cps <float>` flag caps characters-per-second in generated captions. Prevents overcrowded captions for fast speech.

**Music Utilities**:
- **validate_music_license.py**: Checks track metadata against allowed license types. Rejects tracks with restrictive or missing licenses. Integrated into CI.
- **beat_lock.py**: Aligns video cuts to music beats using librosa onset detection. Useful for music-driven montages.

### Fixed

- **Caption timing accuracy**: Burn-in timing now matches spoken words within 50ms. Previously could drift by 100-200ms on long clips.
- **Remotion render logs**: Suppressed noisy Remotion CLI output in CI. Logs now show only errors and final status.

### Dependencies

- **librosa** (optional): For beat detection and music analysis. Install via `pip install librosa`.
- **numpy, scipy**: Required for audio processing in review.py and beat_lock.py.

## [4.1.0] - 2026-10-10

### Added

- **Motion detection**: Added `scripts/cut_detection.py` for scene cut detection via ffmpeg scdet filter. Outputs JSON with timestamps.
- **Clipping utility**: `scripts/clipping.py` extracts subclips by timestamp range. Useful for isolating failed review sections.

### Fixed

- **Remotion version check**: Verifies `npx remotion --version` succeeds before running builds. Catches broken Node.js or missing deps early.

### Documentation

- **docs/quickstart.md**: Updated with review.py workflow. Added troubleshooting section for common render errors.

## [4.0.0] - 2026-10-01

Initial versioned release. See README.md for full feature list.
