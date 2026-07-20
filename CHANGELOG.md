# Changelog

## [0.19.5] — 2026-07-20

### Added
- Content-based language detection: when a subtitle file is opened and the
  filename has no language suffix, the app now inspects the text content
  to determine the language (script detection for Cyrillic, Arabic, CJK;
  diacritic markers for Latin-script languages). The detected language is
  shown in the file-open dialog.

### Changed
- Language auto-detection from the filename now takes priority over the
  last-used language from Settings. Dropping a file named `movie.en.srt`
  correctly shows English regardless of previous sessions.
- The check-for-updates feature uses the GitHub Releases API directly,
  removing the need for externally hosted update manifests.

## [0.19.0] — 2026-07-09

First release of the modernized fork.

### Added
- Multi-engine speech recognition — **PocketSphinx** (classic), **Vosk**
  (fast, recommended) and **Whisper** (opt-in, multilingual). Selectable
  in Settings and via `--engine`.
- A single Whisper multilingual model covers essentially all languages for
  audio-based sync.
- WebVTT (`.vtt`) subtitle support (input and output).
- Experimental dark theme (Light / Dark / System).
- Start-view preference (Basic or Batch) on launch.
- Windows taskbar progress indicator.
- Batch context menu: "Use as reference for all rows".
- Windows installer and a single-file portable executable.
- App translations for German, Croatian, Polish, Swedish, Norwegian,
  Italian (English fallback for untranslated strings; `.po` files ready for
  human translation).

### Changed
- Runs on Python 3.11+, FFmpeg 5.1–7.x, C++17, wxPython 4.2.
- Build system: `distutils` → `setuptools` + `pyproject.toml`.
- Updated Python dependencies.
- Vosk models are loaded once and shared across parallel jobs; richer
  engines automatically use a lower effort budget for faster sync.

### Fixed
- Output preserves the original subtitle file's formatting, positioning
  and styles (the timing correction is applied to the original).
- Batch/CLI output encoding respects the configured output encoding
  and the source encoding instead of always writing UTF-8.
- Batch mode keeps processing until correlation is achieved, matching
  the single-file behaviour.
- Headless mode on Windows no longer opens a stray console window.
- CLI now prints a goodness-of-fit summary on success and an explanation
  when synchronization fails.
- Output paths containing brackets or braces no longer fail as an
  invalid pattern.
- Czech accepts its correct ISO 639-3 code; two-letter language codes
  are accepted everywhere.
- Fixed wxPython 4.2 / Python 3 type errors in sliders, progress bars,
  timers, locale initialisation and the Settings window.
- Benign FFmpeg warnings for image-based (PGS) subtitle tracks are
  filtered from the log.

### Known limitations
- A delay that drifts through a video is only partially corrected by the
  single linear model.
- Full native dark mode requires wxWidgets 3.3 (not yet available).
- macOS builds and image-based (PGS) subtitle extraction are not provided.

### Baseline
- Based on upstream sc0ty/subsync, archived October 2024.
