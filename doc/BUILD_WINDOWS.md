# Building SubSync (gizmo) on Windows from source

This is the exact, reproducible recipe used to build the native `gizmo` extension
on Python 3.11 against the **known-good** stack (FFmpeg 5.1 + classic PocketSphinx).
No C++ source changes are required for this baseline build.

## Result of this recipe
- `gizmo.cp311-win_amd64.pyd` built in-place
- `import gizmo` works on Python 3.11
- `py -3.11 run.py` launches the app (CLI verified, GUI loads)

---

## 1. Prerequisites

- **Visual Studio 2022/2026 Build Tools** with **"Desktop development with C++"**
  (MSVC v14.x + Windows SDK). Verified working: MSVC 14.51 under
  `C:\Program Files\Microsoft Visual Studio\18\Community`.
- **Python 3.11** (verified 3.11.9). `py -3.11 --version`.
- **7-Zip** (`C:\Program Files\7-Zip\7z.exe`) for extracting the FFmpeg archive.
- **git**.
- Python build packages:
  ```powershell
  py -3.11 -m pip install --upgrade pybind11 setuptools wheel
  ```

All native dependencies are staged under `%DEPS%\\`.

---

## 2. FFmpeg 5.1 (pre-compiled, downloadable)

We need **FFmpeg 5.1** specifically: it is the last major line that still exposes
`avcodec_decode_subtitle2()` (removed in FFmpeg 6.0), which `gizmo/media/subdec.cpp`
uses. Selection rule: the `bin\` must contain **`avcodec-59.dll`**.

```powershell
New-Item -ItemType Directory -Force %DEPS% | Out-Null
$url = "https://github.com/GyanD/codexffmpeg/releases/download/5.1.2/ffmpeg-5.1.2-full_build-shared.zip"
Invoke-WebRequest $url -OutFile %DEPS%\\ffmpeg-5.1.2-shared.zip
& "C:\Program Files\7-Zip\7z.exe" x %DEPS%\\ffmpeg-5.1.2-shared.zip -o%DEPS% -y
Rename-Item %DEPS%\\ffmpeg-5.1.2-full_build-shared %DEPS%\\ffmpeg-5.1
```
Layout produced: `%DEPS%\\ffmpeg-5.1\{include,lib,bin}`.

---

## 3. Classic PocketSphinx + SphinxBase

The modern `pocketsphinx >= 5.0` dropped `sphinxbase` and the `cmd_ln_*`/`ps_args`
API that this code uses, so we use the **classic** sources for headers and generate
import libraries from the **known-good working DLLs** (no fragile old-VS-solution build).

### 3.1 Headers (from classic sources)
```powershell
cd %DEPS%
git clone https://github.com/cmusphinx/sphinxbase.git
git clone https://github.com/cmusphinx/pocketsphinx.git
git -C pocketsphinx checkout last-pre-1.0
```
- `sphinxbase` default branch still contains `include\sphinxbase\*.h` and
  `include\win32\config.h` / `sphinx_config.h`.
- `pocketsphinx` tag **`last-pre-1.0`** is the classic API (`ps_args`, `cmd_ln_*`).

### 3.2 Import libraries (generated from the working DLLs)
The runtime DLLs come from the working install copy
(from an existing SubSync installation, e.g. `C:\Program Files\subsync\{sphinxbase,pocketsphinx}.dll`).
`setup.py` expects them under `<dep>\bin\Release\x64\`.

```powershell
$inst = "C:\Program Files\subsync"
New-Item -ItemType Directory -Force %DEPS%\\sphinxbase\bin\Release\x64 | Out-Null
New-Item -ItemType Directory -Force %DEPS%\\pocketsphinx\bin\Release\x64 | Out-Null
Copy-Item "$inst\sphinxbase.dll"   %DEPS%\\sphinxbase\bin\Release\x64\   -Force
Copy-Item "$inst\pocketsphinx.dll" %DEPS%\\pocketsphinx\bin\Release\x64\ -Force
```

Create a small MSVC helper `%DEPS%\\run-msvc.cmd`:
```bat
@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
%*
```

Dump exports, build `.def`, and create `.lib` (repeat for both libraries):
```powershell
# Example for sphinxbase (do the same for pocketsphinx):
$root = "%DEPS%\\sphinxbase\bin\Release\x64"
cmd /c "%DEPS%\\run-msvc.cmd dumpbin /nologo /exports `"$root\sphinxbase.dll`"" > $root\exports.txt
# Parse names between the RVA column and end-of-line into a .def:
"EXPORTS" | Set-Content $root\sphinxbase.def
Get-Content $root\exports.txt | ForEach-Object {
  if ($_ -match '^\s+\d+\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+(\S+)') { $Matches[1] }
} | Sort-Object -Unique | Add-Content $root\sphinxbase.def
cmd /c "%DEPS%\\run-msvc.cmd lib /nologo /def:`"$root\sphinxbase.def`" /machine:x64 /out:`"$root\sphinxbase.lib`""
```

Final layout:
```
%DEPS%\\
  ffmpeg-5.1\    include\  lib\  bin\
  sphinxbase\    include\  include\win32\  bin\Release\x64\ (sphinxbase.lib + .dll)
  pocketsphinx\  include\  bin\Release\x64\ (pocketsphinx.lib + .dll)
```

---

## 4. Build the extension

From the repo root:
```powershell
$env:FFMPEG_DIR       = "%DEPS%\\ffmpeg-5.1"
$env:SPHINXBASE_DIR   = "%DEPS%\\sphinxbase"
$env:POCKETSPHINX_DIR = "%DEPS%\\pocketsphinx"

py -3.11 setup.py build_ext --inplace
py -3.11 setup.py build_py          # generates subsync\config.py and subsync\version.py
```

> Note: `setup.py` derives its version from `git describe --tags`, so a **numeric**
> tag must exist (we tag the baseline `0.16`). A non-numeric tag makes setup fail
> with `InvalidVersion`.

---

## 5. Stage runtime DLLs next to gizmo.pyd

`gizmo.pyd` dynamically links FFmpeg/Sphinx, so their DLLs must sit beside it
(the repo root) or be added via `os.add_dll_directory`:
```powershell
cd C:\path\to\subsync
Copy-Item %DEPS%\\ffmpeg-5.1\bin\*.dll .                                   -Force
Copy-Item %DEPS%\\sphinxbase\bin\Release\x64\sphinxbase.dll     .          -Force
Copy-Item %DEPS%\\pocketsphinx\bin\Release\x64\pocketsphinx.dll .          -Force
```
(These `*.dll` and `*.pyd` are covered by `.gitignore`.)

---

## 6. Runtime dependencies + run

```powershell
py -3.11 -m pip install pysubs2 pycryptodome PyYAML requests certifi wxPython
py -3.11 run.py --version      # -> subsync version 0.16.1 on win32
py -3.11 run.py --help         # CLI options
py -3.11 run.py                # GUI
```

Speech models / dictionaries are read from `C:\ProgramData\subsync\assets`
(shared with the installed app). They can also be downloaded on demand from the
(still-live) upstream asset server.

---

## Troubleshooting

- **`InvalidVersion: '1.gd...'`** — add a numeric git tag: `git tag 0.16 <baseline-commit>`.
- **`ImportError: DLL load failed` on `import gizmo`** — the FFmpeg/Sphinx DLLs are
  not next to `gizmo.pyd`; re-run step 5.
- **Wrong FFmpeg** — if `bin\` has `avcodec-60/61`, that's FFmpeg 6/7 and will fail
  to compile `subdec.cpp` (uses `avcodec_decode_subtitle2`). Use 5.1.x.
