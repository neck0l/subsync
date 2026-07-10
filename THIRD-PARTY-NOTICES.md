# Third-party notices

This project (GPLv3) uses / links / bundles the following components. All listed
licenses are compatible with GPLv3.

| Component | Role | License |
|-----------|------|---------|
| [sc0ty/subsync](https://github.com/sc0ty/subsync) | upstream project this is forked from | GPL-3.0 |
| [FFmpeg](https://ffmpeg.org) (libav*, swresample) | media demux/decode/resample | LGPL-2.1+/GPL (per build) |
| [PocketSphinx / SphinxBase](https://github.com/cmusphinx) | speech engine (classic) | BSD-2-Clause |
| [Vosk](https://github.com/alphacep/vosk-api) | speech engine (optional) | Apache-2.0 |
| [whisper.cpp / ggml](https://github.com/ggerganov/whisper.cpp) | speech engine (optional) | MIT |
| [pybind11](https://github.com/pybind/pybind11) | C++/Python bindings | BSD-3-Clause |
| [nlohmann/json](https://github.com/nlohmann/json) (vendored `gizmo/thirdparty/json.hpp`) | JSON parsing | MIT |
| [wxPython / wxWidgets](https://www.wxpython.org) | GUI | wxWindows Licence (LGPL-like) |
| [pysubs2](https://github.com/tkarabela/pysubs2) | subtitle I/O | MIT |
| [pycryptodome](https://www.pycryptodome.org) | signature verification | BSD-2-Clause / public domain |
| [PyYAML](https://pyyaml.org), [requests](https://requests.readthedocs.io), [certifi](https://github.com/certifi/python-certifi) | task files / networking / CA certs | MIT / Apache-2.0 / MPL-2.0 |

Notes:
- If you **redistribute binaries** that bundle FFmpeg, include FFmpeg's license
  texts and, for GPL FFmpeg builds, the corresponding source offer. LGPL FFmpeg
  builds (dynamically linked) are simplest.
- Speech-recognition **models** (PocketSphinx / Vosk / Whisper `ggml` files) have
  their own licenses from their respective providers; they are downloaded/added by
  the user and are not part of this repository.
- The vendored `gizmo/thirdparty/json.hpp` retains its MIT license header.
