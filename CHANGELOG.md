# Changelog

All notable changes to this fork of **SubSync** are documented here.
This fork revives the archived upstream project (sc0ty/subsync) and modernizes it.

Format: newest entries on top. Dates are local.

---

## [0.17.0] — 2026-07-09 (fork: modernized + multi-engine)

First release of the modernized fork, continuing upstream's 0.17 line: builds and
runs on Python 3.11 with FFmpeg 5.1/7.1, C++17, wxPython 4.2, and a selectable
multi-engine speech backend (PocketSphinx / Vosk / Whisper). Segments A–O of the
modernization roadmap.

### Known limitations
- **#55** (batch stuck on "Queued") — investigated: batch tasks run sequentially
  and a per-task error is caught so it won't queue-lock the rest; "all stuck"
  indicates a blocking hang (extraction/asset step) that isn't reproducible here
  and is an old report. Not changed speculatively; batch robustness is improved by
  #139 (keep-trying) and #149 (encoding) plus modern FFmpeg. Reopen with a sample
  if it recurs.
- **#164** (small/variable delay) — investigated with a ground-truth test: the
  perfect Croatian srt was distorted with a known +0.4s/+1.6s step and re-synced.
  SubSync recovers **constant** offsets perfectly (a +0.6s offset was recovered as
  −0.6001s), but uses a **single linear fit** `ref = a·sub + b`, so a delay that
  *drifts through the video* is averaged (≈1.07s max residual on the step test).
  A piecewise/changepoint approach was prototyped and ground-truth tested: it
  located the breakpoint but only marginally/inconsistently improved accuracy
  (≈0.7s), because the underlying word-correlation points carry ~0.4–0.7s of
  inherent noise (subtitle display time ≠ speech time). Conclusion: not integrated
  — the gain didn't justify the overfitting risk. Documented as a known limitation.

### Upstream issue fixes
- **#139** — batch reliability: batch (non-interactive) previously stopped at
  `minEffort` even when it hadn't correlated yet, so harder files failed in batch
  though they'd succeed in single (interactive) sync. Batch now keeps processing
  until it correlates (or effort is exhausted). Files that correlate early are
  unaffected. Verified a 2-task batch still correlates + saves both.
- **#174** — batch: new context-menu item **"Use as reference for all rows"** on a
  reference cell copies that reference file to every row — no more dropping the
  same episode/video onto 12+ subtitle rows one by one. Verified.
- **#102** — Windows taskbar progress: the app's taskbar icon now shows sync
  progress (via the `ITaskbarList3` COM interface through ctypes, since wxPython
  4.2 doesn't expose it). Fully defensive — silent no-op on any failure / non
  -Windows. Wired into the sync progress window (set on update, cleared on close).
- **#165(c)** — dark theme (experimental, opt-in): new `darkMode` setting
  (Light / Dark / System) + Settings dropdown. wxWidgets 3.2 has no native
  dark-mode switch, so the theme sets the Windows process dark app-mode + a dark
  DWM title bar and recolors controls recursively (dark frame/panels + light text
  + dark inputs/buttons). Applied to Main / Batch / Sync / Settings / Open windows,
  not just Settings. Default Light so nothing changes unless chosen.
  (Note: an early build had a bug where referencing the non-existent
  `wx.HyperlinkCtrl` threw for every widget that reached it, so only Settings
  looked dark; fixed — now all listed windows recolor fully.)
  All secondary dialogs (Channels / Fps / About / Output-pattern / Stream-select /
  Download / Error) are also auto-themed via a ShowModal/Show hook. Group boxes
  blend into the dark (dimmed label, panel-matched background). Theme changes take
  effect on app restart. A fully *native* dark mode needs wxWidgets 3.3
  (wxPython 4.3), which is not yet on PyPI — the notebook tab strip stays light.
- **#165(b)** — default launch view: new `startView` setting (Basic / Batch) with a
  dropdown in Settings → General; the app opens the chosen view on startup.
- **#165(a)** — default language: already served by the existing `lastSubLang` /
  `lastRefLang` settings (the file-open dialog pre-fills the last-used language);
  documented rather than duplicated.
- Settings engine dropdown now also lists **Whisper** (was missing sphinx/vosk only).
- **#146** — confirmed multi-core works in this fork: `--jobs N` creates N parallel
  reference pipelines (verified 8/8 job windows + threads Pipeline0–8), each in its
  own GIL-releasing native thread. The old single-core report was an old
  Linux/docker build; no change needed here.
- **#149** — batch/CLI output encoding no longer forced to UTF-8. `OutputFile`
  previously defaulted `enc` to `'UTF-8'`, so the controller's
  `out.enc → outputCharEnc → sub.enc` chain always short-circuited to UTF-8,
  ignoring the *Output Encoding* setting and the source encoding. `enc` now
  defaults to `None`, so the setting (and "same as input") are respected.
  Verified: `outputCharEnc='cp1250'` yields a cp1250 file; `'UTF-8'` stays UTF-8.
- **#189** — preserve original subtitle formatting: for an external subtitle
  file the timing formula is now applied to the **original file** (positioning
  `{\an8}`, italics, colors, styles, HTML tags all kept) instead of the
  FFmpeg-decoded reconstruction. Embedded/other sources fall back to the decoded
  collector. Verified: tags preserved + timings shifted; real sync keeps all 834
  events and text intact.
- **#191** — headless CLI on Windows no longer unconditionally spawns a new
  console window: if a terminal is already present its output stays there
  (piped output preserved); it attaches to the launching terminal when possible,
  and only allocates a console as a last resort (e.g. double-clicked GUI exe).
- **#144** — WebVTT (`.vtt`) support: added to the subtitle format list, so `.vtt`
  can be selected as input and output. Verified end-to-end (read `.vtt` sub →
  sync → save `.vtt`).
- **noise** — benign FFmpeg `Could not find codec parameters` warnings (from the
  MKV's bitmap/PGS subtitle tracks that SubSync never decodes) are now filtered
  out of the log; real FFmpeg errors and all other messages still pass through.
- **#150** — Czech now accepts the correct ISO 639-3 code `ces` (added as an
  alias for `cze`).
- **#97 / #182** — literal output paths containing `[...]` release tags or
  `{`/`}` braces no longer crash as "invalid output pattern"; a path with no real
  placeholder is treated literally.
- **#167** — fixed wxPython 4.1+ `wxLocale::GetInfo` C-locale assertion on
  Windows/Py3.8+ (GUI `wx.App.InitLocale` pins the C locale).
- **#160 / #120** — CLI now explains *why* a sync failed (points found + best
  correlation + hints) and prints a goodness-of-fit line on success (points,
  correlation, max change).
- **#169** — verified already working: `--sub-lang`/`--ref-lang` accept 2-letter
  codes (`en`→`eng`, `hr`→`hrv`); no change needed.
- **#194 / #187 / #179 / #85 / #52** — "can't sync language X / need model for X"
  is addressed by the multilingual Whisper engine (one model, ~99 languages);
  Whisper language is auto-derived from the reference language.

### GUI modernization fixes — wxPython 4.2 / Python 3 (DONE, simulated)
Python 3's `/` yields floats where wxPython 4.2 requires `int`, which crashed
several windows. All wrapped in `int()`:
- `gui/mainwin.py` — max-distance `Slider.SetValue`.
- `gui/batchwin.py` — max-distance/effort sliders + current/total progress gauges.
- `gui/syncwin.py` — progress gauge.
- `gui/busydlg.py` — `wx.Timer.Start` interval (this crashed drag-and-drop of a
  reference file).
- `gui/settingswin.py` — log-level `SetSelection` (fixed alongside Segment M).

**Simulated headlessly** (real MKV + Croatian SRT) to verify the full workflow:
- All standalone dialogs construct (About/Settings/Fps/Languages/CharEnc/OutPattern/Error).
- MainWin + BatchWin construct.
- Drag-drop reference → OpenWin renders all streams (incl. 6-ch audio) + ChannelsWin.
- Start → SyncWin correlates (formula `1.0000x−2.393`) and Save writes a valid output.
No remaining type errors in the common path.

### Segment H — Whisper engine (opt-in) (DONE, verified end-to-end)
- **Added** `gizmo/media/whisperrec.{h,cpp}` — `WhisperSpeechRecognition` (whisper.cpp),
  a chunked `AVOutput` (buffers 16 kHz mono float32, decodes in 30 s chunks, emits
  words with proportional timing). Gated by `WITH_WHISPER` (+ `WHISPER_DIR`).
- **Bound** `gizmo.WhisperSpeechRecognition`; `speech.py` gains a `whisper` engine
  branch (float32 format) + `loadWhisperModel`; `--engine whisper` added.
- Built whisper.cpp as a shared lib (MSVC + cmake); staged SDK at `C:\subsync-deps\whisper`.
- **Verified** end-to-end (ggml-tiny.en): correlated True, 93 points, R=0.9999995,
  `ref=0.99999708·sub−2.45`, ~13.5 s.

### Segment N — Windows packaging (DONE)
- `windows.spec` now bundles the Vosk runtime (`libvosk` + MinGW deps) and
  `fork.pub` when `VOSK_DIR` is set, plus an optional default model via
  `SUBSYNC_BUNDLE_VOSK_MODEL`. Plain Sphinx-only builds are unchanged.

### Segment K — Multi-key asset signing (DONE)
- `subsync/pubkey.py` verifies signatures against **any** trusted `*.pub`
  (upstream `key.pub` + fork `fork.pub`). Generated a 4096-bit fork keypair
  (public bundled; private kept out of the repo). Sign/verify roundtrip tested.
- `doc/ASSETS_HOSTING.md` documents signing + hosting new engine models.

### Segment M — GUI engine selector (DONE)
- Speech-engine dropdown added to the Settings window (PocketSphinx / Vosk /
  Whisper). Fixed a latent Python 3 / wxPython 4.2 crash (`SetSelection(float)`).

### Segment J — Engine-aware effort (DONE)
- `speechEngine` setting + `--engine` CLI flag. When Vosk/Whisper is selected and
  the user left effort at default, `minEffort` auto-drops to 0.15 (they are ~4×
  more word-dense than Sphinx) — big speed win at equal accuracy.

### Segments F + G — Multi-engine speech + Vosk (DONE, verified end-to-end)
- **Added** a second speech engine, **Vosk (Kaldi)**, alongside the classic
  PocketSphinx, selectable per speech-model descriptor via a new `engine` field
  (absent ⇒ `sphinx`, so 100% backward compatible).
- **New** `gizmo/media/voskrec.{h,cpp}` — `VoskSpeechRecognition`, a drop-in
  `AVOutput` implementing the same words-listener contract as the Sphinx class,
  with the identical absolute-time mapping (`m_deltaTime` on first frame, reset on
  discontinuity). Vendored `gizmo/thirdparty/json.hpp` (nlohmann/json) to parse
  Vosk word results.
- **New** pybind class `gizmo.VoskSpeechRecognition` (gated by `WITH_VOSK`).
- **Build:** `setup.py` gains `WITH_VOSK=1` + `VOSK_DIR=...` env switches; when
  off, nothing about the build changes (no bloat).
- **Python:** `subsync/synchro/speech.py::createSpeechRec` now selects the engine;
  `subsync/assets/item.py` resolves relative Vosk model paths.
- **Verified end-to-end** on the same movie (Croatian sub vs English audio):
  - Sphinx @0.5 effort: R=0.99999951, **83** points, `ref=0.99998·sub−2.17`, ~20 s.
  - **Vosk @0.15 effort: R=0.99999923, 89 points, `ref=0.99996·sub−2.38`, ~9.4 s.**
  - i.e. **Vosk tuned is ~2× faster than Sphinx at equal accuracy.**
  - **Performance:** added a process-wide shared `VoskModel` cache (loaded once,
    shared across all parallel jobs instead of reloaded per job). Because Vosk is
    ~4× more information-dense, a lower effort budget (~0.15) gives the same result
    with much less audio processed.
  - Regression: Sphinx re-run on the Vosk-enabled build = 85 points, −2.20 s (intact).
- **Tooling:** `tools/vosk_sync.py` (engine A/B harness, `SUBSYNC_MIN_EFFORT` env).

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
