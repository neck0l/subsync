# Changelog

All notable changes to this fork of SubSync are documented here.
This fork revives and modernizes the archived upstream project (sc0ty/subsync),
continuing the 0.17 line.

## [0.19.4] — 2026-07-13

### Fixed
- Language switching now works properly — Croatian, German, Polish, Swedish,
  Norwegian, Italian + English (243 strings each, 100% machine-translated).
- Subtitle language auto-detected from filename on open (e.g. `movie.en.srt`
  → English), no longer overridden by the last-used language in Settings.
- Docs: removed old `sc0ty.github.io` links, cleaned up install/architecture
  guide references.
- "Check for updates" now uses the GitHub Releases API directly
  (`/releases/latest`) instead of the old assets.json mechanism (no hosting
  infrastructure needed — just tag a release and upload the setup.exe).

## [0.19.3] — 2026-07-13

First release of the modernized fork.

### Added
- Multi-engine speech recognition — choose between **PocketSphinx** (classic),
  **Vosk** (fast, recommended) and **Whisper** (opt-in, multilingual). Selectable
  in Settings and with the `--engine` command-line option.
- Whisper uses one multilingual model, enabling audio-based sync for essentially
  any language without a per-language model.
- WebVTT (`.vtt`) subtitles are now supported for both input and output.
- Experimental dark theme (Light / Dark / System) applied across the app.
- Setting to choose the start view (Basic or Batch) on launch.
- Windows taskbar icon shows synchronization progress.
- Batch: right-click a reference → "Use as reference for all rows", so a single
  video can be applied to many subtitle rows at once.
- Windows installer (`setup.exe`) and a single-file portable executable.

### Changed
- Runs on Python 3.11+, FFmpeg 5.1–7.x, C++17 and wxPython 4.2.
- Build system migrated from the removed `distutils` to `setuptools` +
  `pyproject.toml`.
- Updated Python dependencies (pysubs2, PyYAML, requests, pybind11, wxPython,
  pycryptodome).
- Speech/Vosk models are loaded once and shared across parallel jobs; the
  richer engines automatically use a lower effort budget, making them faster.
- Downloaded assets can be verified against multiple trusted signing keys.

### Fixed
- Synchronized output now preserves the original subtitle's formatting,
  positioning and styling (the timing is applied to the original file).
- Batch and command-line output encoding now respects the configured output
  encoding and the source encoding instead of always writing UTF-8.
- Batch synchronization keeps working until it correlates rather than giving up
  early, so files that sync fine individually also sync in batch.
- Headless/command-line mode on Windows no longer opens a stray console window.
- The command line now explains why a sync failed and prints a goodness-of-fit
  summary on success.
- Output paths that contain brackets or braces no longer fail as an invalid
  pattern.
- Czech now accepts its correct ISO 639-3 code; two-letter language codes are
  accepted everywhere.
- Fixed several Python 3 / wxPython 4.2 crashes in the GUI (sliders, progress
  bars, timers, locale handling and the Settings window).
- Benign FFmpeg probing warnings for image-based subtitle tracks are no longer
  printed.

### Known limitations
- A delay that drifts through the video is only partially corrected — the linear
  model handles a constant offset perfectly but averages a changing delay.
- A fully native dark mode requires wxWidgets 3.3 (not yet available); the
  notebook tab strip stays light.
- macOS builds are not provided, and image-based (PGS) subtitles are unsupported.

### Baseline
- Based on upstream sc0ty/subsync, archived in October 2024.
