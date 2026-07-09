<#
    build-gizmo-windows.ps1
    Reproducible build of the native 'gizmo' extension on Windows (Python 3.11)
    against the known-good stack: FFmpeg 5.1 + classic PocketSphinx.

    Assumes dependencies are already staged under $DepsDir (see doc/BUILD_WINDOWS.md):
        <DepsDir>\ffmpeg-5.1\{include,lib,bin}
        <DepsDir>\sphinxbase\{include, include\win32, bin\Release\x64\sphinxbase.{lib,dll}}
        <DepsDir>\pocketsphinx\{include, bin\Release\x64\pocketsphinx.{lib,dll}}

    Usage:
        pwsh -File tools\build-gizmo-windows.ps1
        pwsh -File tools\build-gizmo-windows.ps1 -DepsDir C:\subsync-deps -Python "py -3.11"
#>
param(
    [string]$DepsDir = "C:\subsync-deps",
    [string]$Python  = "py -3.11"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot   # repo root = parent of tools\
Set-Location $repo

Write-Host "== SubSync gizmo build ==" -ForegroundColor Cyan
Write-Host "Repo:  $repo"
Write-Host "Deps:  $DepsDir"

$env:FFMPEG_DIR       = Join-Path $DepsDir "ffmpeg-5.1"
$env:SPHINXBASE_DIR   = Join-Path $DepsDir "sphinxbase"
$env:POCKETSPHINX_DIR = Join-Path $DepsDir "pocketsphinx"

foreach ($d in @($env:FFMPEG_DIR, $env:SPHINXBASE_DIR, $env:POCKETSPHINX_DIR)) {
    if (-not (Test-Path $d)) { throw "Missing dependency dir: $d  (see doc/BUILD_WINDOWS.md)" }
}

Write-Host "`n-- Ensuring build packages --" -ForegroundColor Cyan
& cmd /c "$Python -m pip install --upgrade pybind11 setuptools wheel"

Write-Host "`n-- build_ext --inplace --" -ForegroundColor Cyan
& cmd /c "$Python setup.py build_ext --inplace"

Write-Host "`n-- build_py (config.py + version.py) --" -ForegroundColor Cyan
& cmd /c "$Python setup.py build_py"

Write-Host "`n-- Staging runtime DLLs next to gizmo.pyd --" -ForegroundColor Cyan
Copy-Item (Join-Path $env:FFMPEG_DIR "bin\*.dll") $repo -Force
Copy-Item (Join-Path $env:SPHINXBASE_DIR   "bin\Release\x64\sphinxbase.dll")   $repo -Force
Copy-Item (Join-Path $env:POCKETSPHINX_DIR "bin\Release\x64\pocketsphinx.dll") $repo -Force

Write-Host "`n-- Validating import gizmo --" -ForegroundColor Cyan
& cmd /c "$Python -c ""import gizmo; print('gizmo OK')"""

Write-Host "`nDone. Run the app with:  run-app.cmd" -ForegroundColor Green
