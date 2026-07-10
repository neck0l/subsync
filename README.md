# SubSync (modernized fork)

Automatic movie subtitle synchronization tool.

> **This is a fork.** It is based on [sc0ty/subsync](https://github.com/sc0ty/subsync)
> by Michał Szymaniak, which was archived/deprecated in October 2024
> ([#197](https://github.com/sc0ty/subsync/issues/197)). All credit for the
> original work goes to the upstream author. This fork revives and modernizes the
> project. It is **not** affiliated with or endorsed by the original author.

## What this fork changes
Continuing the upstream `0.17` line. Highlights (full details in
[`CHANGELOG.md`](CHANGELOG.md)):

- Builds and runs on **Python 3.11+**, **FFmpeg 5.1–7.x**, **C++17**, **wxPython 4.2**.
- Build system moved off the removed `distutils` to `setuptools` + `pyproject.toml`.
- **Multi-engine speech recognition**: classic **PocketSphinx**, **Vosk** (fast,
  recommended), and **Whisper** (opt-in, multilingual) — selectable in Settings /
  via `--engine`.
- Numerous upstream issue fixes (WebVTT, batch encoding, headless CLI, subtitle
  formatting preservation, taskbar progress, batch UX, dark theme, …).

## Building
See [`doc/BUILD_WINDOWS.md`](doc/BUILD_WINDOWS.md) for the full from-source build
(native `gizmo` extension + FFmpeg + speech engines). Third-party components and
their licenses are listed in [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).

## License
GNU General Public License v3.0 — see [`LICENSE`](LICENSE).

This program is free software: you can redistribute it and/or modify it under the
terms of the GNU GPL v3. It is distributed WITHOUT ANY WARRANTY. The original
work is Copyright © Michał Szymaniak; modifications in this fork are Copyright ©
the fork contributors, released under the same GPLv3.
