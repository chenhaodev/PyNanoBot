"""Ensure pynanobot re-exports resolve to nanobot."""

from __future__ import annotations


def test_pynanobot_top_level_exports():
    import pynanobot

    assert pynanobot.Nanobot is not None
    assert pynanobot.RunResult is not None
    assert isinstance(pynanobot.upstream_version, str)


def test_pynanobot_agent_reexport():
    from pynanobot.agent import AgentLoop, ReminderEngine

    assert AgentLoop.__name__ == "AgentLoop"
    assert ReminderEngine.__name__ == "ReminderEngine"


def test_pynanobot_ext_package():
    import pynanobot.ext

    assert pynanobot.ext.__doc__ is not None
