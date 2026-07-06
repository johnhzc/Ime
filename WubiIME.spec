# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the legacy Python prototype version.
# The primary implementation is now the TSF native DLL in wubi_ime_tsf/.


a = Analysis(
    ['wubi_ime\\launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('wubi_ime', 'wubi_ime')],
    hiddenimports=['keyboard', 'pynput.keyboard._win32', 'pynput.mouse._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WubiIME',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
