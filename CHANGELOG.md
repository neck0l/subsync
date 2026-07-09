# Changelog

All notable changes to this fork of **SubSync** are documented here.
This fork revives the archived upstream project (sc0ty/subsync) and modernizes it.

Format: newest entries on top. Dates are local.

---

## [Unreleased] — modernize branch

### Segment D — FFmpeg 6/7 compatibility (DONE)
- **Added** `gizmo/media/ffmpeg-channel-compat.h` — a compat shim that translates
  SubSync's legacy `uint64_t` channel-layout bitmasks to/from the modern
  `AVChannelLayout` API (introduced in FFmpeg 5.1, mandatory in 7.0).
- **Migrated** `gizmo/media/stream.cpp`, `audiodec.cpp`, `resampler.cpp` off the
  removed helpers (`av_get_default_channel_layout`, `av_get_channel_name`,
  `av_get_channel_description`, `av_get_channel_layout_channel_index`,
  `swr_alloc_set_opts`, and the `channels`/`channel_layout` struct fields).
- The Python-facing `AudioFormat` API is unchanged (still `uint64_t` masks).
- **Verified:** builds + links + `import gizmo` on **both FFmpeg 5.1 and FFmpeg 7.1**
  (0 errors each). Reconnaissance confirmed `avcodec_decode_subtitle2` and
  `av_init_packet` still exist in 7.1, so no subtitle-decode rewrite was needed.
- Active runtime restored to the known-good FFmpeg 5.1 build.

### Segment E — C++17 modernization (DONE)
- **Replaced** all dynamic exception specifications `throw()` with `noexcept` in
  `gizmo/general/exception.{h,cpp}` (removed in C++17).
- **Enabled C++17**: `setup.py` now passes `/std:c++17` (MSVC) / `-std=c++17`
  (unix, with c++14/c++11 fallback), and — importantly — actually applies the MSVC
  compile flags to the extension (previously `setup_msvc` set them but never
  assigned them, so only the compiler default was used).
- **Verified:** clean rebuild with `/std:c++17`, `import gizmo` OK, app runs.

### Segment C — Build-system modernization (DONE)
- **Migrated** `setup.py` off `distutils` (removed in Python 3.12) to `setuptools`
  equivalents (`setuptools.Command`, `setuptools.command.build_py`,
  `setuptools.errors.CompileError`), with a guarded fallback for old setuptools.
- **Added** `pyproject.toml` (PEP 517 build metadata: setuptools + pybind11 + wheel).
- **Bumped** `python_requires` from `>=3.5` to `>=3.9`.
- **Verified:** clean rebuild, `import gizmo` OK, `run --version` OK.

### Segment L — Dependency updates (DONE)
- **Raised** dependency floors in `setup.py` and `requirements.txt`:
  `pysubs2>=1.6`, `PyYAML>=6.0`, `requests>=2.31`, `pybind11>=2.10`,
  `pycryptodome>=3.19`, `cryptography>=42.0` (Darwin), `wxPython>=4.2`.
- Confirmed YAML loading already uses `yaml.safe_load` (no unsafe `yaml.load`).
- **Verified** against installed versions (pysubs2 1.8.1, PyYAML 6.0.3,
  requests 2.34.2, pycryptodome 3.23.0, wxPython 4.2.5, pybind11 3.0.4): imports OK,
  app runs.

### Segment B — Reproduce the known-good build on modern Python (DONE)
**Goal:** build the native `gizmo` C++ extension from source on Python 3.11 against the
proven stack (FFmpeg 5.1 + classic PocketSphinx), with **zero C++ source changes**.

- **Added** FFmpeg 5.1.2 shared dev libraries (GyanD build) staged under
  `C:\subsync-deps\ffmpeg-5.1` (confirmed `avcodec-59`, i.e. the last line that still
  ships `avcodec_decode_subtitle2`, removed in FFmpeg 6.0).
- **Added** classic PocketSphinx headers (tag `last-pre-1.0`) and SphinxBase classic
  headers (incl. `win32/config.h`) for the `ps_args`/`cmd_ln_*` API this code uses.
- **Generated** import libraries (`sphinxbase.lib`, `pocketsphinx.lib`) directly from
  the known-good working DLLs (dumpbin → `.def` → `lib`), guaranteeing an ABI match
  and avoiding the fragile legacy Visual Studio solution build. Verified symbols:
  `ps_init`, `ps_process_raw`, `ps_args`, `cmd_ln_parse_r`, `err_set_callback`.
- **Built** `gizmo.cp311-win_amd64.pyd` with MSVC 14.51 (all 26 `.cpp` compiled and
  linked; only benign deprecation/narrowing warnings).
- **Installed** runtime dependencies: `pysubs2`, `pycryptodome`, `PyYAML`, `requests`,
  `certifi`, `wxPython 4.2.5`; build deps `pybind11 3.0.4`, `setuptools`, `wheel`.
- **Generated** `subsync/config.py` and `subsync/version.py` (`version_short = 0.16.1`).
- **Added** `doc/BUILD_WINDOWS.md` — full reproducible Windows build recipe.
- **Added** `tools/build-gizmo-windows.ps1` — one-command rebuild script.
- **Added** `run-app.cmd` — launcher for the from-source build (GUI/CLI).
- **Added** `BUILD_LOGIC.txt` — running plain-English progress/context log.

**Verified working:**
- `import gizmo` → all classes exposed (Correlator, Demux, SpeechRecognition, …).
- `run-app.cmd --version` → `subsync version 0.16.1 on win32`.
- `run-app.cmd --help` → full CLI options print.
- `subsync.gui.mainwin` imports (GUI layer loads under wxPython 4.2.5).
- Reads installed speech/dictionary assets from `C:\ProgramData\subsync\assets`.

**Notes:**
- No source files were modified. All changes are additive; generated artifacts
  (`config.py`, `version.py`, `*.pyd`, `*.dll`, `build/`) remain git-ignored.

### Segment A — Fork & git baseline (DONE)
- **Initialized** a git repository in the source tree (the binary install copy is kept
  out of git).
- **Configured** local git identity and `core.autocrlf=false` to preserve the pristine
  Unix line endings.
- **Committed** the pristine upstream source as the baseline
  (`baseline: pristine upstream sc0ty/subsync source (archived)`).
- **Added** `MODERNIZATION_ROADMAP.md` (15-segment plan A–O) in a second commit.
- **Tagged** `v-baseline` (human marker) and `0.16` (numeric tag required so
  `setup.py`'s `git describe` versioning yields a valid PEP 440 version).
- **Created** the `modernize` working branch; kept `master` pristine.

---

## Baseline — upstream import

- Imported upstream **sc0ty/subsync** source (archived by the original author on
  2024-10-01) as the starting point for this fork.
- Known-good reference stack captured from the working install: Python 3.6.8,
  FFmpeg 5.1, classic PocketSphinx + SphinxBase, wxPython 4.1, MSVC 140, pycryptodome.
