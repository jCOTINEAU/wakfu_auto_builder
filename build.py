#!/usr/bin/env python3
"""Build the desktop binary via pyside6-deploy.

pyside6-deploy auto-bundles every subdir next to main.py that isn't in its
hardcoded ignore list, which for us picks up .venv, .cursor, métier, etc.
We work around this by staging only the declared project files + resource
dirs into a temp directory, running the deploy from there, and copying the
resulting .app / .bin back into dist/.

Usage:
    python build.py                # build for current platform
    python build.py --keep-staging # don't delete the temp build dir
"""

import argparse
import contextlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
RESOURCE_DIRS = ["views", "assets", "data", "data_overrides"]
CONFIG_FILES = ["pysidedeploy.spec", "auto_builder.pyproject"]

# PySide6 6.10 ships QtQuick.Shapes.DesignHelpers whose .dylib references
# a framework that isn't actually included in the wheel. Nuitka scans qml
# plugins eagerly (--noinclude-dlls doesn't stop it), so we side-step it
# by hiding the folder from disk during the build. Restored on exit.
BROKEN_PLUGIN_DIRS = [
    "PySide6/Qt/qml/QtQuick/Shapes/DesignHelpers",
]


def _pyside6_site_root() -> Path:
    """Find the PySide6 package root next to which the buggy plugins sit."""
    import PySide6
    # __file__ is <site-packages>/PySide6/__init__.py → parent.parent = site-packages
    return Path(PySide6.__file__).resolve().parent.parent


@contextlib.contextmanager
def hidden_broken_plugins():
    """Temporarily move known-broken plugin dirs OUTSIDE the PySide6 tree
    so Nuitka's Qt plugin scan doesn't trip on them. Renaming in-place is
    not enough — Nuitka finds the plugin regardless of the folder name."""
    site = _pyside6_site_root()
    stash_root = Path(tempfile.mkdtemp(prefix="wakfu-plugin-stash-"))
    moved: list[tuple[Path, Path]] = []
    try:
        for rel in BROKEN_PLUGIN_DIRS:
            src = site / rel
            if src.exists():
                # Preserve the same relative path inside the stash so the
                # restore is unambiguous.
                dst = stash_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                moved.append((dst, src))
                print(f"[build] hiding {rel} → {dst}")
        yield
    finally:
        for dst, src in moved:
            if dst.exists() and not src.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                print(f"[build] restored {src.relative_to(site)}")
        shutil.rmtree(stash_root, ignore_errors=True)


def project_files() -> list[str]:
    """Read the file list from auto_builder.pyproject (single source of truth)."""
    with open(REPO / "auto_builder.pyproject", encoding="utf-8") as f:
        return json.load(f)["files"]


def stage(staging: Path) -> None:
    for name in CONFIG_FILES:
        shutil.copy2(REPO / name, staging / name)

    # Resource dirs first — they carry every non-python file we need
    # (QML, JSON, SVG assets).
    for d in RESOURCE_DIRS:
        src = REPO / d
        if src.exists():
            shutil.copytree(src, staging / d)

    # Then top-level Python files. Anything inside a RESOURCE_DIR (QML)
    # is already staged, skip it.
    resource_prefixes = tuple(f"{d}/" for d in RESOURCE_DIRS)
    for rel in project_files():
        if rel.startswith(resource_prefixes):
            continue
        src = REPO / rel
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def collect_output(staging: Path, dist: Path) -> Path | None:
    """Locate the built artifact and copy it to dist/.

    pyside6-deploy puts the final .app / .exe at the exec_directory (staging
    root by default, since our spec sets `exec_directory = .`). Nuitka's
    intermediate output goes to staging/deployment/. Check both.
    """
    search_dirs = [staging, staging / "deployment"]
    for search in search_dirs:
        if not search.exists():
            continue
        candidates = (list(search.glob("*.app"))
                      + list(search.glob("*.exe"))
                      + list(search.glob("*.bin")))
        if candidates:
            out = candidates[0]
            dist.mkdir(exist_ok=True)
            target = dist / out.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            if out.is_dir():
                shutil.copytree(out, target, symlinks=True)
            else:
                shutil.copy2(out, target)
            return target
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-staging", action="store_true",
                        help="Don't delete the temp staging dir (for debugging).")
    args = parser.parse_args()

    tmp = tempfile.mkdtemp(prefix="wakfu-build-")
    staging = Path(tmp)
    try:
        print(f"[build] staging in {staging}")
        stage(staging)

        cmd = ["pyside6-deploy", "--force", "main.py"]
        print(f"[build] running: {' '.join(cmd)}")
        with hidden_broken_plugins():
            subprocess.check_call(cmd, cwd=staging)

        dist = REPO / "dist"
        out = collect_output(staging, dist)
        if out is None:
            print("[build] ERROR: no output artifact found in staging/deployment/",
                  file=sys.stderr)
            return 1
        print(f"[build] → {out}")
        return 0
    finally:
        if args.keep_staging:
            print(f"[build] kept staging: {staging}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
