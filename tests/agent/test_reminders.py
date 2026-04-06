"""Tests for ReminderEngine."""

import pytest

from nanobot.agent.reminders import (
    DriftDetectors,
    Reminder,
    ReminderConfig,
    ReminderEngine,
    TriggerType,
)


def test_drift_unauthorized_delete() -> None:
    assert DriftDetectors.unauthorized_file_delete("ran rm -rf /tmp/x")
    assert not DriftDetectors.unauthorized_file_delete("hello")


def test_drift_apology_loop() -> None:
    text = "I apologize. sorry about that, let me try again"
    assert DriftDetectors.apology_loop(text)


def test_periodic_fires_at_interval() -> None:
    eng = ReminderEngine(ReminderConfig(periodic_interval=4, accelerated_after=999))
    out = eng.check(4, last_assistant_msg="", budget_utilization=0.0)
    assert any("[Reminder]" in m for m in out)


def test_budget_pressure() -> None:
    eng = ReminderEngine()
    out = eng.check(
        5,
        last_assistant_msg="",
        budget_utilization=0.85,
    )
    assert any("Context window" in m for m in out)


def test_register_custom() -> None:
    eng = ReminderEngine()
    eng.unregister("conciseness")
    eng.register(
        Reminder(
            name="custom",
            message="Custom note",
            trigger_type=TriggerType.CONTENT_MATCH,
            trigger_value=r"SECRET",
            priority=10,
            cooldown=0,
        ),
    )
    out = eng.check(1, last_assistant_msg="SECRET code")
    assert any("Custom note" in m for m in out)


def test_stats() -> None:
    eng = ReminderEngine()
    eng.check(12, budget_utilization=0.0)
    s = eng.stats()
    assert "tool_discipline" in s
