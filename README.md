# SubSync (modernized fork)

**SubSync automatically synchronizes movie subtitles to the video — no more
manually nudging the delay.** It does this by *listening* to the movie's audio,
transcribing the speech, and lining those words up with the words in your
subtitle file. From those matches it computes a timing correction and rewrites
the subtitle timestamps so the lines appear exactly when they're spoken.

Because it works from the actual audio (not just another subtitle), it can fix
subtitles even when you have no correctly-timed reference — and it can sync
subtitles that are in a **different language** than the audio by translating
words through a built-in dictionary.

> **This is a fork.** It is based on [sc0ty/subsync](https://github.com/sc0ty/subsync)
> by Michał Szymaniak, which was archived/deprecated in October 2024
> ([#197](https://github.com/sc0ty/subsync/issues/197)). All credit for the
> original work goes to the upstream author. This fork revives and modernizes the
> project and is **not** affiliated with or endorsed by them.

## How it works
1. **Decode audio** from the movie (FFmpeg) and run **speech recognition** to get
   timed words.
2. **Parse the subtitle** into timed words (translating them if the audio is a
   different language).
3. **Correlate** the two streams: each recognized word is matched to a similar
   subtitle word within a time window, producing a scatter of
   *(subtitle time, real time)* points.
4. **Fit a line** through those points (`real = a·sub + b`) with robust outlier
   rejection — this is the correction (delay + pace).
5. **Rewrite the timestamps** and save, preserving the original subtitle's
   formatting/styling.

Speech recognition is imperfect, but SubSync discards mismatched words and only
needs enough correct ones to lock in the timing.

## What it can sync
- **Subtitle → video/audio** — the main use case (listens to the audio track).
- **Subtitle → subtitle** — align against an already-correct subtitle.
- **Cross-language** — e.g. English audio with Croatian subtitles, via dictionaries.
- **Formats**: SRT, ASS/SSA, **WebVTT (.vtt)**, MicroDVD, TMP.
- **Batch mode** — synchronize many files at once.
- **Command-line / headless mode** — for scripts and tools like Bazarr.

## Speech engines
This fork adds a **selectable multi-engine backend** (pick in Settings or with
`--engine`):

| Engine | Notes |
|--------|-------|
| **PocketSphinx** | Classic, lightweight, built-in. |
| **Vosk** *(recommended)* | Kaldi-based — faster and more accurate; word-level timestamps; runs on CPU. |
| **Whisper** *(opt-in)* | Highest accuracy, **multilingual** (one model covers ~all languages); heavier. |

## Download (Windows)
Grab a build from the [Releases](https://github.com/neck0l/subsync/releases) page:
- **Installer** (`subsync-*-setup.exe`) — Start-Menu shortcut + uninstaller.
- **Portable** (`subsync-portable.exe`) — single file, no installation.

Both bundle all three engines and every required native library.

## Usage
**GUI:** launch SubSync, drop your subtitle into *Subtitles* and the movie into
*Reference*, set the languages if needed, and press **Start**.

**Command line (headless):**
```
subsync --cli --engine vosk sync ^
    --sub  "movie.srt"  --sub-lang eng ^
    --ref  "movie.mkv"  --ref-stream-by-type audio --ref-lang eng ^
    --out  "movie.synced.srt"
```
See the [wiki](https://github.com/neck0l/subsync/wiki) for the full
command-line reference, FAQ, asset/model format, and Python API.

Speech models and dictionaries are downloaded on demand and stored per-user
(e.g. `%ProgramData%\subsync\assets` on Windows).

## What this fork changes
Continuing the upstream `0.17` line (full details in [`CHANGELOG.md`](CHANGELOG.md)):

- Builds and runs on **Python 3.11+**, **FFmpeg 5.1–7.x**, **C++17**, **wxPython 4.2**;
  build system moved off the removed `distutils` to `setuptools` + `pyproject.toml`.
- **Multi-engine speech recognition** (PocketSphinx / Vosk / Whisper).
- Preserves original subtitle formatting/positioning on output.
- Respects the configured output encoding (was always UTF-8) and keeps trying in
  batch instead of giving up early.
- Headless CLI no longer spawns a stray console; clearer success/failure output.
- WebVTT support, Windows taskbar progress, batch "use one reference for all rows",
  experimental dark theme, and many Python 3 / wxPython 4.2 GUI-crash fixes.

## Building from source
See [`doc/BUILD_WINDOWS.md`](doc/BUILD_WINDOWS.md) for the full from-source build
(the native `gizmo` extension + FFmpeg + speech engines). Bundled third-party
components and their licenses are listed in
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).

## License
GNU General Public License v3.0 — see [`LICENSE`](LICENSE).

This program is free software: you can redistribute it and/or modify it under the
terms of the GNU GPL v3. It is distributed WITHOUT ANY WARRANTY. The original work
is Copyright © Michał Szymaniak; modifications in this fork are Copyright © the
fork contributors, released under the same GPLv3.
