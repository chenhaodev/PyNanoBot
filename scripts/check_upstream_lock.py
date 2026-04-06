#!/usr/bin/env python3
"""Verify upstream.lock pynanobot.version matches pyproject.toml [project].version."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    pv_match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject)
    if not pv_match:
        print("Could not find [project] version in pyproject.toml", file=sys.stderr)
        raise SystemExit(1)
    pv = pv_match.group(1)

    raw = (root / "upstream.lock").read_text(encoding="utf-8")
    lv_match = re.search(r"(?m)^\s+version:\s*(.+)\s*$", raw)
    if not lv_match:
        print("Could not find pynanobot.version in upstream.lock", file=sys.stderr)
        raise SystemExit(1)
    lv = lv_match.group(1).strip().strip('"')

    if pv != lv:
        print(
            f"Version mismatch: pyproject.toml={pv!r} upstream.lock={lv!r}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"OK: version {pv} matches upstream.lock")


if __name__ == "__main__":
    main()
