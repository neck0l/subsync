@echo off
REM Launch the from-source SubSync build (Python 3.11).
REM DLLs for gizmo (FFmpeg 5.1 + PocketSphinx) are staged in this folder.
REM Pass --cli / --help / etc. through to the app, e.g.:  run-app.cmd --version
cd /d "%~dp0"
py -3.11 run.py %*
