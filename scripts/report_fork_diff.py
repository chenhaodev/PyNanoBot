#!/usr/bin/env python3
"""Print ``git diff --stat`` for ``nanobot/`` against ``upstream/main`` if available.

Usage (from repo root)::

    python scripts/report_fork_diff.py

Requires ``git remote add upstream https://github.com/HKUDS/nanobot.git`` and
``git fetch upstream`` for meaningful output.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(
    args: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    up = _run(["git", "rev-parse", "--verify", "upstream/main"], cwd=root)
    if up.returncode != 0:
        print(
            "No local ref upstream/main. Configure and fetch, e.g.:\n"
            "  git remote add upstream https://github.com/HKUDS/nanobot.git\n"
            "  git fetch upstream main",
            file=sys.stderr,
        )
        return 1
    diff = _run(
        ["git", "diff", "--stat", "upstream/main", "--", "nanobot/"],
        cwd=root,
    )
    if diff.stdout.strip():
        print(diff.stdout.rstrip())
    else:
        print("No diff under nanobot/ vs upstream/main (trees may match).")
    if diff.stderr.strip():
        print(diff.stderr, file=sys.stderr)
    return 0 if diff.returncode == 0 else diff.returncode


if __name__ == "__main__":
    raise SystemExit(main())
