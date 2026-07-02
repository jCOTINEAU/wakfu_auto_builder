#!/usr/bin/env python3
"""Build the desktop binary via PyInstaller.

Runs `pyinstaller main.spec` and lists the output in dist/.
Produces per-platform: WakfuAutoBuilder.app (macOS), .exe (Windows),
WakfuAutoBuilder (Linux).

Usage:
    python build.py            # incremental build
    python build.py --clean    # wipe build/ and dist/ first
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
                        help="Remove build/ and dist/ before running.")
    args = parser.parse_args()

    if args.clean:
        for d in ("build", "dist"):
            shutil.rmtree(REPO / d, ignore_errors=True)
            print(f"[build] cleaned {d}/")

    cmd = ["pyinstaller", "main.spec", "--noconfirm"]
    print(f"[build] running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=REPO)

    dist = REPO / "dist"
    if not dist.exists():
        print("[build] ERROR: dist/ not found after PyInstaller run",
              file=sys.stderr)
        return 1

    outputs = list(dist.iterdir())
    if not outputs:
        print("[build] ERROR: dist/ is empty", file=sys.stderr)
        return 1
    for out in outputs:
        print(f"[build] -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
