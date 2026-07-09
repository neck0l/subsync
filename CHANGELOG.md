# Changelog

All notable changes to this fork of **SubSync** are documented here.
This fork revives the archived upstream project (sc0ty/subsync) and modernizes it.

Format: newest entries on top. Dates are local.

---

## [Unreleased] — modernize branch

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
