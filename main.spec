# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for WakfuAutoBuilder.

Produces:
- onefile binary on Linux (`WakfuAutoBuilder`)
- onefile binary on Windows (`WakfuAutoBuilder.exe`, no console)
- .app bundle on macOS (`WakfuAutoBuilder.app`)

All bundled resources are resolved at runtime via paths.resource_path(),
which uses sys._MEIPASS (PyInstaller's extraction dir).
"""

import sys
from PyInstaller.utils.hooks import collect_all

# OR-Tools ships native .pyd/.so/.dylib as package data + has some dynamic
# submodule loading. collect_all pulls in everything (binaries, data, hidden
# imports) so pywraplp works at runtime.
ortools_datas, ortools_binaries, ortools_hidden = collect_all("ortools")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=ortools_binaries,
    datas=[
        ("data",           "data"),
        ("data_overrides", "data_overrides"),
        ("assets",         "assets"),
        ("views",          "views"),
    ] + ortools_datas,
    hiddenimports=ortools_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Test-only modules — bundling them pulls in a lot for no runtime value.
    excludes=["unittest", "pytest", "doctest", "pdb"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="WakfuAutoBuilder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS: wrap the binary in a proper .app bundle so double-clicking works
# and the OS treats it as a native application.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="WakfuAutoBuilder.app",
        icon=None,
        bundle_identifier="com.jeremycotineau.wakfuautobuilder",
    )
