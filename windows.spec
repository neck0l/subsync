# -*- mode: python ; coding: utf-8 -*-

import os

# Segment N: optionally bundle the Vosk engine runtime + (optionally) a default
# model. Controlled by env vars so a plain Sphinx-only build is unchanged:
#   VOSK_DIR                 - path to the Vosk SDK (libvosk.dll + MinGW runtime)
#   SUBSYNC_BUNDLE_VOSK_MODEL - path to a vosk model dir to ship inside the app
vosk_binaries = []
vosk_datas = []
_vosk_dir = os.environ.get('VOSK_DIR')
if _vosk_dir:
    for _dll in ('libvosk.dll', 'libgcc_s_seh-1.dll', 'libstdc++-6.dll', 'libwinpthread-1.dll'):
        _p = os.path.join(_vosk_dir, _dll)
        if os.path.isfile(_p):
            vosk_binaries.append((_p, '.'))
_vosk_model = os.environ.get('SUBSYNC_BUNDLE_VOSK_MODEL')
if _vosk_model and os.path.isdir(_vosk_model):
    vosk_datas.append((_vosk_model, os.path.join('assets', 'speech', os.path.basename(_vosk_model))))

_common_datas = [
    ('LICENSE', '.'),
    ('subsync/key.pub', '.'),
    ('subsync/fork.pub', '.'),
    ('subsync/img', 'img'),
    ('subsync/locale', 'locale'),
] + vosk_datas


main_a = Analysis(['bin/subsync'],
        pathex=['.'],
        binaries=vosk_binaries,
        datas=_common_datas,
        hiddenimports=[],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None,
        noarchive=False)

main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=None)

main_exe = EXE(main_pyz,
        main_a.scripts,
        [],
        exclude_binaries=True,
        name='subsync',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon='resources/icon.ico')

main_dbg = EXE(main_pyz,
        main_a.scripts,
        [],
        exclude_binaries=True,
        name='subsync-debug',
        debug=True,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        icon='resources/icon.ico')

main_cmd = EXE(main_pyz,
        main_a.scripts,
        [],
        exclude_binaries=True,
        name='subsync-cmd',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        icon='resources/icon.ico')

main_coll = COLLECT(main_exe,
        main_dbg,
        main_cmd,
        main_a.binaries,
        main_a.zipfiles,
        main_a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='subsync')

portable_a = Analysis(['bin/portable'],
        pathex=['.'],
        binaries=vosk_binaries,
        datas=_common_datas,
        hiddenimports=[],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None,
        noarchive=False)

portable_pyz = PYZ(portable_a.pure, portable_a.zipped_data, cipher=None)

portable_exe = EXE(portable_pyz,
        portable_a.scripts,
        portable_a.binaries,
        portable_a.zipfiles,
        portable_a.datas,
        [],
        name='subsync-portable',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon='resources/icon.ico')
