"""PyNanoBot distribution namespace.

Top-level imports from ``nanobot`` are **lazy** (PEP 562) so that
``pynanobot.ext`` can load while ``nanobot`` is still initializing.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "Nanobot",
    "RunResult",
    "upstream_logo",
    "upstream_version",
]


def __getattr__(name: str) -> Any:
    if name == "Nanobot":
        from nanobot import Nanobot

        return Nanobot
    if name == "RunResult":
        from nanobot import RunResult

        return RunResult
    if name == "upstream_logo":
        from nanobot import __logo__ as upstream_logo

        return upstream_logo
    if name == "upstream_version":
        from nanobot import __version__ as upstream_version

        return upstream_version
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
