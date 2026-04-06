"""CLI entry that delegates to upstream ``nanobot`` Typer app."""

from __future__ import annotations


def main() -> None:
    from nanobot.cli.commands import app

    app()


if __name__ == "__main__":
    main()
