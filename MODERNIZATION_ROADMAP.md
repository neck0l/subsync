# SubSync — Fork & Modernization Roadmap

> Status: PLANNING ONLY. No source code has been modified. This document is the
> agreed plan before any change is made.
>
> Guiding rule from the owner: **do not break the currently working app, and do
> not delete anything.** Every change must be additive, reversible, and validated
> against the known-good baseline before replacing anything.

---

## 0. Known-Good Baseline (verified from the working install)

The installed/working copy (`C:\Users\ki\Desktop\subsync-master\subsync` and
`C:\Program Files\subsync`) was inspected. It pins the exact stack that is proven
to work. **This is our reference target — we reproduce this first, then modernize.**

| Component      | Version (proven working)                                   |
|----------------|------------------------------------------------------------|
| Python (frozen)| 3.6.8                                                      |
| FFmpeg         | 5.1 — `avcodec-59.dll` 59.2.100, `avformat-59` 59.3.101, `avutil-57` 57.0.100, `swresample-4` 4.0.100 |
| Speech engine  | PocketSphinx + SphinxBase (classic `cmd_ln_*` / `ps_args` API) |
| GUI            | wxPython 4.1.x (wxWidgets 3.1.5, `wxmsw315u_*` DLLs)       |
| C runtime      | MSVC 140 (VCRUNTIME140 / MSVCP140)                         |
| Crypto         | pycryptodome (`Crypto/`)                                    |
| Serialization  | PyYAML (`yaml/`), certifi                                   |

Asset server is **still live** (`https://github.com/sc0ty/subsync/releases/download/assets/assets.json`
returns HTTP 200), so speech models and dictionaries still download even though
the upstream repo is archived.

Installed asset layout (reference for engine design):
```
%ProgramData%\subsync\assets\
  dict\eng-hrv.dict
  speech\eng.speech                     <- JSON model descriptor
  speech\eng-us-cmusphinx\...           <- HMM / LM / dict data
```

`eng.speech` descriptor (the format the multi-engine design must extend):
```json
{
  "lang": "eng",
  "dir": "./eng-us-cmusphinx",
  "version": "1.0.0",
  "samplerate": "16000",
  "sampleformat": "S16",
  "sphinx": {
    "-hmm": "./eng-us-cmusphinx/cmusphinx-en-us-ptm-5.2",
    "-lm":  "./eng-us-cmusphinx/cmusphinx-5.0-en-us.lm.bin",
    "-dict":"./eng-us-cmusphinx/cmudict-en-us.dict",
    "-ds": "2", "-maxhmmpf": "500"
  }
}
```

---

## 1. Architecture Recap (so every later segment has context)

SubSync aligns subtitles to a reference **by matching timed words**, not waveforms.

```
Media file
   │  gizmo.Demux (FFmpeg avformat)
   ├── audio stream ──> gizmo.AudioDec (avcodec) ──> gizmo.Resampler (swresample, →16kHz mono S16)
   │                        └──> gizmo.SpeechRecognition (PocketSphinx) ──> timed words (REF)
   └── subtitle stream ─> gizmo.SubtitleDec (avcodec) ──> SSAParser ──> timed words
Subtitle file (.srt/.ass/…) ─> pysubs2 / SubtitleDec ──> timed words (SUB)
         (optional cross-language: gizmo.Dictionary + gizmo.Translator)

Words (SUB) + Words (REF)
   └──> gizmo.Correlator ──> Synchronizer ──> LineFinder (RANSAC-like)
                └── fits  ref_time = a·sub_time + b  (Line.interpolate = least squares + R²)
                └── outlier rejection (removeFurthestPoint) until R²>min & dist<max & points>min
   └──> CorrelationStats {correlated, factor(R²), points, maxDistance, formula}
Subtitle.synchronize(formula) ─> transform_framerate + shift ─> save via pysubs2
```

**Precision is dominated by two things:**
1. How many *correct* word timestamps the speech engine produces (PocketSphinx is the weak link).
2. The line-fit tolerances (`windowSize`, `minCorrelation`, `maxPointDist`, `minPointsNo`, `minWordsSim`).

Key files:
- Python orchestration: `subsync/synchro/` (controller, synchronizer, pipeline, speech, dictionary)
- Native engine: `gizmo/` (media, text, math, correlator, python bindings)
- Speech engine seam (where new engines plug in): `gizmo/media/speechrec.{h,cpp}` +
  `subsync/synchro/speech.py` + `subsync/assets/item.py` (`SpeechAsset`)
- Build: `setup.py`, `windows.spec`, `subsync/Makefile`
- GUI: `subsync/gui/` (settings window is where the engine selector goes)

---

## 2. Segment Overview (execution order)

| # | Segment | Risk | Depends on |
|---|---------|------|-----------|
| A | Fork & git baseline | none | — |
| B | Reproduce known-good build (FFmpeg 5.1 + Sphinx) | med | A |
| C | Build-system modernization (setuptools/pyproject) | low | B |
| D | FFmpeg 6/7 migration (subtitle API) | med-high | B |
| E | C++17 modernization | low-med | B |
| F | Speech-engine abstraction layer (multi-engine seam) | med | B |
| G | Vosk engine (new default) | med-high | F |
| H | Whisper engine (optional add-on) | high | F |
| I | PocketSphinx engine (kept as fallback) | low | F |
| J | Sync-precision improvements | med | F |
| K | Asset system extension (multi-engine models) | med | F |
| L | Python dependency updates | low | C |
| M | GUI: engine selector + settings | low | F, L |
| N | Packaging: full installer + portable | med | all |
| O | Testing / regression / rollback | ongoing | all |

Each segment below lists: **Goal · Files touched · Exact changes · Validation · Rollback.**

---

## SEGMENT A — Fork & Git Baseline

**Goal:** Make everything reversible before any edit; establish the fork.

**Changes**
1. `git init` in `subsync-master/`; add a sensible `.gitignore` (already present — keep it,
   it excludes `config.py` and `version.py`).
2. Commit the pristine source as commit #1 (`baseline: upstream sc0ty/subsync @ archive`).
3. Add `MODERNIZATION_ROADMAP.md` (this file) as commit #2.
4. Create branch `modernize`; keep `master`/`main` pristine.
5. Record upstream provenance + GPLv3 obligations in README (fork must stay GPLv3).
6. Optionally add the working install DLLs’ version manifest to `doc/` for reference
   (do NOT commit large DLLs — just a text manifest).

**Validation:** `git status` clean; baseline tag `v-baseline` created.

**Rollback:** trivial — everything is in git from the start.

---

## SEGMENT B — Reproduce the Known-Good Build (highest priority, do first)

**Goal:** Build `gizmo` from source on Windows against **FFmpeg 5.1 + classic
PocketSphinx**, matching the working binary, BEFORE changing any library. This
proves our toolchain is correct and gives a baseline to diff against.

**Why 5.1 first, not 6/7:** the source uses `avcodec_decode_subtitle2()`
(`gizmo/media/subdec.cpp:93`), which was **removed in FFmpeg 6.0**. Building
against 5.1 = zero source changes = guaranteed-equivalent binary.

**Native prerequisites (Windows x64)**
- Visual Studio 2019/2022 Build Tools (MSVC 14.x — matches VCRUNTIME140).
- FFmpeg 5.1 **dev** libraries (shared) — headers + import libs + DLLs:
  `avdevice, avformat, avfilter, avcodec, swresample, swscale, avutil`.
  Source options: gyan.dev / BtbN FFmpeg 5.1 shared+dev builds.
- PocketSphinx + SphinxBase (classic 0.8/5prealpha API that exposes
  `sphinxbase.dll`). NOTE: modern pocketsphinx ≥5.0 **merged sphinxbase and
  removed `cmd_ln_*`/`ps_args`** — do not use it for segment B. Build the classic
  API from the pinned commit, or reuse the working DLLs + matching headers.
- pybind11 ≥ 2.4 (pip), Python (build with the interpreter you intend to ship;
  3.6 is EOL — see decision below).

**Python-version decision**
- The frozen app uses 3.6.8 (EOL). For the fork, target a supported Python:
  **3.11 or 3.12**. 3.11 is safest first (matches the machine: 3.11.9). 3.12 later
  after setuptools migration (Segment C) since `distutils` is gone in 3.12.
- `pybind11` handles the ABI; no code change needed for the interpreter bump.

**Build invocation (documented, not yet automated)**
```
set FFMPEG_DIR=...\ffmpeg-5.1-dev
set SPHINXBASE_DIR=...\sphinxbase
set POCKETSPHINX_DIR=...\pocketsphinx
py -3.11 setup.py build_ext --inplace
py -3.11 run.py           # smoke test GUI/CLI
```

**Validation**
- `python -c "import gizmo"` succeeds.
- CLI sync of a known sample against a known video reproduces the *same formula*
  (within tolerance) as the installed app on the same inputs. This is the
  **golden reference** for all later segments.

**Rollback:** none needed (no source edits; env-only).

**Deliverable:** `doc/BUILD_WINDOWS.md` capturing the exact working recipe.

---

## SEGMENT C — Build-System Modernization

**Goal:** Remove `distutils` (gone in Python 3.12), keep behavior identical.

**Files:** `setup.py`, new `pyproject.toml`, `subsync/Makefile`.

**Changes**
1. `setup.py:2` `import distutils.cmd, distutils.command.build_py` →
   `setuptools` equivalents:
   - `distutils.command.build_py.build_py` → `setuptools.command.build_py.build_py`
   - `distutils.cmd.Command` → `setuptools.Command`
   - `setuptools.distutils.errors.CompileError` reference (`setup.py:204`) → `distutils.errors` via
     `setuptools._distutils` or `try/except` import shim for 3.8–3.12.
2. Add `pyproject.toml` with `[build-system] requires = ["setuptools>=64", "pybind11>=2.10", "wheel"]`
   and `build-backend = "setuptools.build_meta"`. Keep `setup.py` for the custom
   `build_ext` (native flags) — hybrid is fine.
3. Keep custom commands (`gen_gui`, `gen_locales`, `gen_version`, `gen_doc`) but
   re-base on `setuptools.Command`.
4. Bump `python_requires` `>=3.5` → `>=3.9`.

**Validation:** `py -3.11 -m build` (or `setup.py build_ext`) still produces an
identical-behavior `gizmo`; golden sync test unchanged.

**Rollback:** revert `setup.py`; delete `pyproject.toml`.

---

## SEGMENT D — FFmpeg 6/7 Migration

**Goal:** Build against modern FFmpeg (6.x/7.x) so future dev uses current libs.
This is the only segment with a *required* C++ API change.

**Files:** `gizmo/media/subdec.cpp`, `gizmo/media/audiodec.cpp`,
`gizmo/media/stream.cpp`, `gizmo/media/resampler.cpp`, `setup.py` (lib names).

**Changes**
1. **Subtitle decode (blocker):** `gizmo/media/subdec.cpp:93`
   `avcodec_decode_subtitle2()` was removed in FFmpeg 6.0. Two options:
   - (Preferred) Keep a compatibility shim: `#if LIBAVCODEC_VERSION_MAJOR < 60`
     use legacy call; else re-implement via the retained subtitle path. NOTE:
     FFmpeg kept subtitle decoding on the *legacy* API longer than audio/video;
     verify against the exact target version. If still available in 6.x under a
     compat header, gate by version. Provide both code paths so 5.1 build (Segment
     B) keeps working.
2. **Channel layout API:** FFmpeg 5.1→6/7 deprecated the old
   `av_get_default_channel_layout()`, `av_get_channel_name()`,
   `av_get_channel_description()`, `AV_CH_FRONT_CENTER`, and int64 channel masks
   in favor of the `AVChannelLayout` struct + `av_channel_*` API.
   - Files: `gizmo/media/stream.cpp` (AudioFormat), `gizmo/media/resampler.cpp`
     (`swr_alloc_set_opts` → `swr_alloc_set_opts2`, `swr_set_matrix`),
     `gizmo/python/stream.cpp` (channel name/description bindings),
     `subsync/synchro/channels.py` (consumes these).
   - Guard everything with `LIBAVUTIL_VERSION_MAJOR` `#if` so the 5.1 path stays.
3. **`av_init_packet` deprecation** (`demux.cpp`, `audiodec.cpp:flush`) →
   `av_packet_alloc`/`av_packet_free` (already partially modern).
4. `avcodec_close()` (`audiodec.cpp:62`) redundant — safe to drop under `free_context`.
5. `setup.py:76-84` lib list unchanged in name; only header/lib dir points to 6/7.

**Strategy:** version-gated compat (`#if LIBAVCODEC_VERSION_MAJOR >= 60`) so the
same source compiles against **5.1 (Segment B) and 6/7**. Never a hard cutover.

**Validation:** build twice (5.1 and 7.x); golden sync test matches on both.

**Rollback:** all changes are `#if`-gated; drop the `>=60` branches.

---

## SEGMENT E — C++17 Modernization

**Goal:** Compile cleanly on modern toolchains.

**Files:** `gizmo/general/exception.{h,cpp}`, `gizmo/general/current_function.h`,
and ~30 sites using dynamic exception specs.

**Changes**
1. Replace removed-in-C++17 `throw()` dynamic exception specs with `noexcept`.
2. `setup.py:137-140` bump `-std=c++14` → `-std=c++17` (with graceful fallback).
3. MSVC: `/EHsc` already set (`setup.py:155`); add `/std:c++17`.
4. Audit `std::` usage — mostly already C++11/14 clean.

**Validation:** zero-warning compile on GCC/Clang/MSVC; golden test unchanged.

**Rollback:** revert std flag + `noexcept` edits.

---

## SEGMENT F — Speech-Engine Abstraction Layer (the multi-engine seam)

**Goal:** Introduce a clean engine interface so **Vosk, Whisper, and PocketSphinx**
coexist without bloating or breaking anything. This is the backbone of the
owner’s multi-engine request.

### Design

Current coupling: `gizmo/media/speechrec.{h,cpp}` *is* PocketSphinx, and it
implements `AVOutput` (consumes resampled `AVFrame`s), emitting `Word`s via
`Notifier`. `subsync/synchro/speech.py` builds it from the `.speech` asset.

**Introduce an interface** in the native layer:
```
gizmo/media/speech/ISpeechEngine.h        (abstract: feed(AVFrame*), flush(),
                                            discontinuity(), word listeners,
                                            required input AudioFormat)
gizmo/media/speech/SphinxEngine.{h,cpp}    (existing speechrec.cpp, refactored in)
gizmo/media/speech/VoskEngine.{h,cpp}      (Segment G)
gizmo/media/speech/WhisperEngine.{h,cpp}   (Segment H)
gizmo/media/speech/SpeechFactory.{h,cpp}   (picks engine by descriptor "engine":)
```
- `gizmo/media/speechrec.{h,cpp}` becomes a thin adapter that delegates to the
  factory-selected engine (keeps the existing `gizmo.SpeechRecognition` Python
  symbol → zero breakage for `pipeline.py`/`speech.py`).
- Engines that need a different input format (Whisper wants 16k mono float32;
  Vosk wants 16k mono S16; Sphinx 16k mono S16) advertise their required
  `AudioFormat`; `Resampler` already adapts (`speech.py:getSpeechAudioFormat`
  just returns the requested format).

**Python side:** `subsync/synchro/speech.py`
- `createSpeechRec(model)` reads `model['engine']` (default `"sphinx"` for legacy
  assets that lack the field → backward compatible) and passes engine + its param
  block to `gizmo`.
- `getSpeechAudioFormat` returns the engine’s required format.

**Asset descriptor extension** (`.speech` JSON, backward compatible):
```json
{
  "lang": "eng",
  "engine": "vosk",              // NEW; absent ⇒ "sphinx"
  "version": "2.0.0",
  "samplerate": "16000",
  "sampleformat": "S16",
  "vosk":   { "model": "./vosk-model-small-en-us-0.15" },
  "sphinx": { "-hmm": "...", "-lm": "...", "-dict": "..." },
  "whisper":{ "model": "./ggml-base.en.bin", "threads": "4" }
}
```
A single language asset MAY ship multiple engine blocks, or engines ship as
separate assets (`eng.vosk.speech`, `eng.whisper.speech`) — decided in Segment K.

**Build flags:** each engine behind a compile switch so users/packagers can build
lean binaries:
```
setup.py define_macros / env:  WITH_SPHINX=1 (default on), WITH_VOSK=1 (default on),
                               WITH_WHISPER=0/1 (opt-in)
```
Engines not compiled in simply don’t register in the factory → **no bloat** for
builds that exclude Whisper.

**Validation:** with only Sphinx compiled, behavior is byte-identical to today.
Factory returns Sphinx for legacy assets. Golden test unchanged.

**Rollback:** the adapter keeps the old class; revert factory to direct Sphinx.

---

## SEGMENT G — Vosk Engine (new default)

**Goal:** Modern, light, offline, per-word timestamps → big precision gain over
Sphinx with modest footprint. Becomes the default engine.

**Why Vosk as default:** Kaldi-based, small models (~40–50 MB `small` models),
CPU-only, no GPU, native word-level timestamps (`result.words[].start/end/word`),
permissive Apache-2.0, C API (`vosk_api.h`) that fits the streaming `feed()` model.

**Files:** `gizmo/media/speech/VoskEngine.{h,cpp}`, `setup.py` (link `libvosk`),
`subsync/synchro/speech.py`, assets.

**Changes**
1. `VoskEngine` implements `ISpeechEngine`:
   - Requires 16 kHz mono **S16** (Resampler already provides).
   - `vosk_model_new(path)`, `vosk_recognizer_new(model, 16000.0f)`,
     `vosk_recognizer_set_words(rec, 1)` for word timestamps.
   - `feed(AVFrame*)`: `vosk_recognizer_accept_waveform(rec, int16*, nbytes)`;
     on segment end parse JSON (`result` / `partial-final`) → emit `Word{text,
     time=start, duration=end-start, score=conf}`.
   - `flush()`: `vosk_recognizer_final_result` → emit remaining words.
   - `discontinuity()`: `vosk_recognizer_reset`.
2. JSON parsing: reuse a tiny header-only JSON lib (or the existing YAML/py path);
   prefer a vendored single-header (e.g. `nlohmann/json`) compiled in.
3. `setup.py`: `WITH_VOSK` default on; link `vosk` (ships `libvosk.dll`/`.so`).
4. Default model policy: `small` model per language for speed; optional larger
   model as an alternative asset.

**Precision notes:** Vosk gives true word start/end → more, better-placed
correlation points → tighter `LineFinder` fit than Sphinx phoneme-ish output.

**Validation:** compare formula + `maxChange` + point count vs Sphinx on the same
sample set; expect equal-or-better correlation with fewer outliers.

**Rollback:** `WITH_VOSK=0` and set default engine back to sphinx in `speech.py`.

---

## SEGMENT H — Whisper Engine (optional add-on)

**Goal:** Highest accuracy for hard cases (noisy audio, accents, music), offered
as an **opt-in** alternative — NOT bundled by default to avoid bloat.

**Why opt-in:** whisper.cpp is CPU-capable but models are larger
(`base` ~140 MB, `small` ~460 MB) and slower; GPU optional. Great as a “max
precision” toggle.

**Files:** `gizmo/media/speech/WhisperEngine.{h,cpp}` (whisper.cpp), `setup.py`
(`WITH_WHISPER` default OFF), assets.

**Changes**
1. Integrate **whisper.cpp** (MIT) as a git submodule / vendored, compiled only
   when `WITH_WHISPER=1`.
2. `WhisperEngine` requires 16 kHz mono **float32** (advertise format; Resampler
   converts). Buffer audio into ~10–30 s chunks (Whisper is not truly streaming),
   run `whisper_full`, read segment/token timestamps → emit `Word`s.
   - Use `token_timestamps=true` for word-ish timing; or segment-level split.
   - Respect `discontinuity()` = flush current buffer + reset.
3. Config block in `.speech`: model path, `threads`, `language`, `beam_size`.
4. Packaging: Whisper models are large → downloaded on demand via asset system,
   never bundled in the base installer.

**Trade-off documented in GUI:** “Whisper (most accurate, slower, larger download)”.

**Validation:** accuracy A/B vs Vosk on a noisy sample; ensure it degrades
gracefully (timeout / cancel) via existing `Extractor` interrupt path.

**Rollback:** `WITH_WHISPER=0` (default) — feature simply absent.

---

## SEGMENT I — PocketSphinx Engine (kept as fallback)

**Goal:** Preserve the original engine for continuity and lowest footprint.

**Files:** `gizmo/media/speech/SphinxEngine.{h,cpp}` (the refactored existing code).

**Changes**
1. Move existing `speechrec.cpp` logic behind `SphinxEngine` unchanged.
2. Decision on library version:
   - **Keep classic sphinxbase API** (matches existing assets/params) → zero asset
     changes; OR
   - Migrate to **pocketsphinx ≥5.0** (merged, `ps_config_*` replaces `cmd_ln_*`,
     no sphinxbase). This changes `setParam` mapping and needs new/rebuilt models.
   - **Recommendation:** keep classic API as the fallback engine (least churn,
     existing `eng-us-cmusphinx` assets keep working). Only consider 5.x if we
     drop Sphinx model hosting.
3. Legacy `.speech` assets (no `engine` field) resolve to this engine → existing
   downloads keep working.

**Validation:** identical to today’s output (this is the golden reference).

**Rollback:** n/a (this IS the baseline behavior).

---

## SEGMENT J — Sync-Precision Improvements (engine-independent)

**Goal:** Squeeze more accuracy from the correlation stage regardless of engine.

**Files:** `gizmo/math/linefinder.cpp`, `gizmo/synchro/synchronizer.cpp`,
`gizmo/correlator.cpp`, `subsync/synchro/synchronizer.py`, `settings.py`.

**Opportunities (each independently toggleable, validated against golden set)**
1. **Sub-word timing quality:** with Vosk/Whisper word timestamps, feed real
   word *centers* (start+dur/2) instead of Sphinx frame approximations.
2. **Weighted regression:** weight correlation points by word confidence/score
   (already carried on `Word.score`) in `Line::interpolate` — down-weight
   low-confidence matches.
3. **Two-pass / piecewise fit:** current model is a single global line
   `ref=a·sub+b`. Add optional **segmented** fit for subtitles with variable
   drift (splice edits, ad breaks) — behind a setting, default off.
4. **Tolerance tuning defaults** (`windowSize`, `maxPointDist`, `minWordsSim`)
   re-benchmarked per engine (Vosk can tolerate tighter `minWordsSim`).
5. **VAD pre-filter** already implicit in engines; ensure silence gaps don’t
   inject spurious points.

**Validation:** benchmark harness (Segment O) reports `maxChange`, R², point count,
and human-verified offset error across a corpus, per engine, per setting.

**Rollback:** all new behavior gated by settings defaulting to current values.

---

## SEGMENT K — Asset System Extension (multi-engine models)

**Goal:** Host & deliver Vosk/Whisper models cleanly; the upstream asset server
is archived (read-only) so we must plan our own hosting.

**Files:** `subsync/assets/item.py` (`SpeechAsset`), `subsync/assets/mgr.py`,
`subsync/config.py.template` (`assetsurl`), `assets/Makefile`, `scripts/sign.py`.

**Changes**
1. **New asset origin:** point `assetsurl` (`config.py.template:41`) to the fork’s
   own release/hosting for *new* engine models, while still allowing the legacy
   URL for existing Sphinx models (both are just signed zips + `assets.json`).
2. **Signing:** downloads are RSA-verified against `subsync/key.pub`
   (`pubkey.py`). We must **generate a new fork keypair** and re-sign our hosted
   assets (we don’t have upstream’s private key). Keep upstream `key.pub` too if
   we continue serving upstream Sphinx assets unmodified from their URL.
   → Support a **key list** (verify against any trusted key) so both work.
3. `SpeechAsset.readSpeechModel()` (`item.py:186+`) already fixes relative paths;
   extend to surface the `engine` field and engine-specific blocks.
4. `assets.json` gains engine metadata + size (so GUI can warn “Whisper 460 MB”).
5. Per-engine model naming: `speech/<lang>.<engine>.speech` or one descriptor with
   multiple blocks (decide; recommend separate assets so users download only what
   they use → no bloat).

**Validation:** offline mode still works with pre-installed assets; download +
signature verify works for a new Vosk model from fork hosting.

**Rollback:** revert `assetsurl` and key list to upstream single key.

---

## SEGMENT L — Python Dependency Updates

**Goal:** Move off EOL pins without behavior change.

**Files:** `requirements.txt`, `setup.py:366-377`.

**Changes**
| Dep | Now | Target |
|-----|-----|--------|
| Python | ≥3.5 | ≥3.9 (build/run on 3.11; verify 3.12 after Segment C) |
| pysubs2 | ≥0.2.4 | ≥1.6 (verify `transform_framerate`/`shift` API — used in `subtitle.py`) |
| pybind11 | ≥2.4 | ≥2.11 |
| wxPython | ≥4.0 | ≥4.2 (wxWidgets 3.2) |
| requests | ≥2.0 | ≥2.31 |
| pycryptodome | ≥3.9 | ≥3.20 |
| PyYAML | any | ≥6.0 (use `yaml.safe_load` — check `SyncTaskList.load`) |
| certifi | any | latest |

**Watch items:**
- `pysubs2` API drift → verify `Subtitles.synchronize()` (`subtitle.py`).
- `yaml.load` without `Loader` is unsafe in PyYAML 6 → ensure `safe_load` in
  `synchro/task.py`.
- wxPython 4.2 regenerate `.fbp`→`.py` only if needed (layouts are 2019-era but
  usually forward-compatible).

**Validation:** full GUI + CLI smoke; golden sync unchanged.

**Rollback:** pin back per-dependency.

---

## SEGMENT M — GUI: Engine Selector & Settings

**Goal:** Let users pick engine (Vosk default / Whisper / PocketSphinx) and manage
per-engine model downloads.

**Files:** `subsync/gui/settingswin.{py,fbp}`, `subsync/settings.py`
(`persistent` defaults + `synchronizationOptions`), `subsync/gui/components/`
(a new engine chooser like existing `choicelang.py`), `subsync/gui/downloadwin.py`,
`subsync/gui/components/assetsdlg.py`, `subsync/data/descriptions.py`.

**Changes**
1. Add `speechEngine` setting (`settings.py:persistent`) default `"vosk"`; include
   in `synchronizationOptions` so it flows to `Synchronizer`.
2. Settings UI: dropdown Engine {Vosk (recommended), Whisper (most accurate,
   large), PocketSphinx (legacy, small)} with tooltips from `descriptions.py`.
3. Asset/download dialog shows model size + engine; Whisper models flagged “large”.
4. CLI: add `--engine vosk|whisper|sphinx` in `cmdargs.py` (default vosk); keep
   old behavior if omitted and only Sphinx assets present.
5. Backward compat: if selected engine’s model missing, prompt to download or
   fall back with a clear message (don’t silently fail).

**Validation:** switching engines re-runs sync with correct model; settings persist.

**Rollback:** hide selector, force `sphinx` default.

---

## SEGMENT N — Packaging: Full Installer + Portable

**Goal:** Ship **Windows full (MSI) installer** and **portable (self-extracting
EXE)**, each in “lean” (Vosk+Sphinx) and “full” (adds Whisper) flavors — without
bloating the default download.

**Files:** `windows.spec`, `tools/package-windows.cmd`,
`tools/package-windows-portable.cmd`, `resources/subsync.wxs`,
`resources/wixui.wxs`, `tools/mkpackage`, `bin/portable`.

**Changes**
1. **PyInstaller (`windows.spec`)**: add new native deps to bundled binaries:
   `libvosk.dll` (+ its deps), optional `whisper` DLL when `WITH_WHISPER`. Keep
   the three EXEs (`subsync.exe` GUI, `-cmd`, `-debug`) and portable single-file.
2. **Installer flavors:**
   - *Standard MSI* (`tools/package-windows.cmd` + WiX): Vosk (default) + Sphinx
     engines; models downloaded on first use (small download).
   - *Portable* (`tools/package-windows-portable.cmd`, 7-Zip SFX): same engine set,
     `bin/portable` overrides config dirs to be self-contained.
   - *Full/offline* option: bundle a default Vosk small model so it works offline
     out of the box; Whisper always download-on-demand.
3. **Whisper as opt-in build:** produce Whisper-enabled artifacts separately
   (`subsync-full-*.exe/.msi`) so the base installer stays small.
4. Update version stamping (`tools/update_version.py`, `gen_version`) and code
   signing placeholder.
5. **mac/linux (documented, lower priority):** owner has no Mac hardware and snap
   is broken upstream. Plan:
   - Linux: provide a `pip install` + system-FFmpeg path and/or a rebuilt Flatpak
     or AppImage instead of the broken snap (future segment).
   - macOS: leave `macos.spec` intact; mark unsupported until hardware available.

**Validation:** clean-VM install of MSI and portable; first-run downloads Vosk
model; sync works; uninstall clean. Full flavor runs Whisper.

**Rollback:** ship only the standard MSI (current behavior) built against new libs.

---

## SEGMENT O — Testing, Regression & Rollback (runs throughout)

**Goal:** Guarantee “don’t break the working app” with objective checks.

**Assets for testing**
- Keep a small corpus: a few videos + matching correct subtitles + deliberately
  desynced subtitles (fixed offset, linear drift, splice) across ≥3 languages.

**Harness**
1. **Golden formula test:** for each (sub, ref) pair, record baseline
   `formula (a,b)`, `maxChange`, R², points from the **known-good install**
   (Segment B). CI/local script asserts new builds stay within tolerance
   (or improve, for engine upgrades).
2. **Import test:** `import gizmo` + all pybind11 symbols present.
3. **CLI end-to-end:** `run.py --cli --sync ...` produces expected output file.
4. **Engine matrix:** run corpus through Sphinx/Vosk/Whisper; report accuracy table.
5. **Cross-platform build:** GCC/Clang/MSVC compile with `-std=c++17`, FFmpeg 5.1
   and 7.x (matrix).

**Non-negotiables**
- Never delete the classic Sphinx path.
- Every engine/precision change is behind a flag/setting defaulting to prior
  behavior until validated.
- Keep `master` pristine; merge to it only after golden tests pass.

---

## 3. Recommended Milestones

| Milestone | Contains | Exit criteria |
|-----------|----------|---------------|
| M1 “Baseline” | A, B | `gizmo` builds from source (FFmpeg 5.1+Sphinx); golden test recorded |
| M2 “Modern build” | C, E, L | Builds on Py 3.11/3.12 + C++17; behavior identical |
| M3 “Modern FFmpeg” | D | Builds on FFmpeg 7.x (version-gated); golden test passes |
| M4 “Multi-engine core” | F, I | Engine seam in place; Sphinx via factory = identical output |
| M5 “Vosk default” | G, K(partial), M(partial) | Vosk is default; better/equal accuracy; models download |
| M6 “Whisper opt-in” | H, K, M | Whisper selectable; large models on demand |
| M7 “Precision” | J | Measured accuracy improvement on corpus |
| M8 “Ship” | N, O | Signed MSI + portable (lean & full); regression green |

---

## 4. Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Native toolchain hard on Windows | Reuse known-good lib versions first (Segment B); document exact recipe |
| FFmpeg 6/7 subtitle API removal | Version-gated compat shim; keep 5.1 path |
| Modern pocketsphinx dropped `cmd_ln`/sphinxbase | Keep classic API for fallback engine; don’t force 5.x |
| Upstream asset server is archived/read-only | Fork-owned hosting + multi-key signature verification |
| Whisper size/speed bloat | Opt-in build + download-on-demand; never in base installer |
| pysubs2 / PyYAML / wxPython API drift | Pin-then-bump per Segment L with smoke tests |
| Breaking the working app | Additive, flag-gated changes; golden regression; pristine `master` |

---

## 5. Immediate Next Actions (await owner go-ahead)

1. **Segment A** — `git init`, commit pristine baseline, create `modernize` branch.
2. **Segment B** — assemble FFmpeg 5.1 dev libs + classic PocketSphinx, build
   `gizmo` from source, record the golden reference. Produce `doc/BUILD_WINDOWS.md`.

Nothing above has been executed yet — this file is the plan for approval.
