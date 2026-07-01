"""Path resolution helpers for dev + frozen (PyInstaller / Nuitka) runtimes.

Two kinds of paths matter:

- **Bundled read-only resources** (data/, assets/, data_overrides/, views/):
  ship with the binary. Resolved from `sys.executable`'s dir when frozen,
  else next to this module in dev.
- **User writable data** (saved_builds.json, saved_stat_profiles.json):
  never inside the bundle. Lives in the OS-specific user data dir.
"""

import os
import shutil
import sys

APP_ID = "WakfuAutoBuilder"


def is_frozen() -> bool:
    """True when running from a packaged binary (PyInstaller / Nuitka onefile)."""
    return (
        getattr(sys, "frozen", False)
        or "NUITKA_ONEFILE_PARENT" in os.environ
    )


def app_root() -> str:
    """Directory holding bundled resources.

    - Dev: repo root (dirname of this file).
    - PyInstaller (onefile / standalone): sys._MEIPASS (extraction dir).
    - Nuitka (onefile / standalone): dirname(__file__) — Nuitka rewrites
      __file__ of bundled modules to point into the extraction dir.
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts) -> str:
    """Absolute path to a bundled read-only resource."""
    return os.path.join(app_root(), *parts)


def user_data_dir() -> str:
    """OS-appropriate writable dir for user data (saved builds, profiles).

    macOS:   ~/Library/Application Support/<APP_ID>/
    Windows: %APPDATA%/<APP_ID>/
    Linux:   $XDG_DATA_HOME/<APP_ID>/  (default ~/.local/share/<APP_ID>/)

    Directory is created on first call.
    """
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    path = os.path.join(base, APP_ID)
    os.makedirs(path, exist_ok=True)
    return path


def user_data_file(name: str) -> str:
    """Absolute path to a file inside user_data_dir()."""
    return os.path.join(user_data_dir(), name)


def migrate_legacy_file(legacy_path: str, new_path: str) -> None:
    """One-shot migration: copy a repo-root JSON to the user data dir on
    first launch after upgrade. No-op if new file already exists or legacy
    is missing. Leaves the legacy file in place — do NOT delete, so the
    original stays accessible if something goes wrong.
    """
    if not os.path.exists(legacy_path):
        return
    if os.path.exists(new_path):
        return
    try:
        shutil.copy2(legacy_path, new_path)
        print(f"[migrate] {legacy_path}  →  {new_path}")
    except OSError as e:
        print(f"[migrate] warning: could not copy {legacy_path}: {e}")
