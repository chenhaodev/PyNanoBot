"""Anti-drift reminder injection (periodic + contextual)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TriggerType(Enum):
    PERIODIC = auto()
    TOOL_MATCH = auto()
    CONTENT_MATCH = auto()
    DRIFT_DETECTED = auto()
    BUDGET_PRESSURE = auto()
    MANUAL = auto()


@dataclass
class Reminder:
    """A single reminder rule."""

    name: str
    message: str
    trigger_type: TriggerType
    trigger_value: str | int | None = None
    cooldown: int = 8
    priority: int = 5
    last_fired_turn: int = -100
    fire_count: int = 0
    enabled: bool = True

    @property
    def token_estimate(self) -> int:
        return max(1, int(len(self.message) / 3.5))


@dataclass
class ReminderConfig:
    """Global configuration for :class:`ReminderEngine`."""

    periodic_interval: int = 12
    accelerated_after: int = 30
    accelerated_interval: int = 8
    max_injection_tokens: int = 400
    contextual_enabled: bool = True


class DriftDetectors:
    """Pattern matchers for common drift in the assistant's last message."""

    @staticmethod
    def unauthorized_file_delete(text: str) -> bool:
        patterns = [
            r"rm\s+-rf?\s+",
            r"os\.remove\(",
            r"shutil\.rmtree\(",
            r"I'(?:ve|ll)\s+(?:deleted?|removed?)\s+",
            r"unlink\(",
        ]
        return any(re.search(p, text, re.I) for p in patterns)

    @staticmethod
    def apology_loop(text: str) -> bool:
        apology_phrases = [
            "I apologize",
            "sorry about that",
            "my mistake",
            "let me try again",
            "I made an error",
        ]
        count = sum(1 for p in apology_phrases if p.lower() in text.lower())
        return count >= 2

    @staticmethod
    def scope_creep(text: str) -> bool:
        patterns = [
            r"while I'?m at it",
            r"I(?:'ll| will) also (?:refactor|clean up|improve|update)",
            r"let me (?:also|additionally)",
            r"I noticed .+ could (?:also |)be (?:improved|refactored|cleaned)",
        ]
        return any(re.search(p, text, re.I) for p in patterns)

    @staticmethod
    def hallucinated_tool(text: str) -> bool:
        fake_tools = [
            "run_command",
            "execute_code",
            "search_web",
            "browse_url",
            "ask_user",
            "send_email",
        ]
        return any(tool in text for tool in fake_tools)

    @staticmethod
    def markdown_overuse(text: str) -> bool:
        header_count = len(re.findall(r"^#{1,3}\s", text, re.M))
        return header_count > 4


class ReminderEngine:
    """Returns reminder strings to inject; does not mutate conversation itself."""

    def __init__(self, config: Optional[ReminderConfig] = None) -> None:
        self.config = config or ReminderConfig()
        self.reminders: dict[str, Reminder] = {}
        self.turn_count: int = 0
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            Reminder(
                name="tool_discipline",
                message=(
                    "[Reminder] Use only the tools provided. Do not fabricate tool "
                    "names or assume tools exist. If you need a capability you don't "
                    "have, say so explicitly."
                ),
                trigger_type=TriggerType.PERIODIC,
                trigger_value=None,
                priority=9,
                cooldown=15,
            ),
        )
        self.register(
            Reminder(
                name="file_safety",
                message=(
                    "[Reminder] Before deleting, moving, or overwriting any file, "
                    "confirm with the user. Never run destructive operations silently."
                ),
                trigger_type=TriggerType.DRIFT_DETECTED,
                trigger_value="unauthorized_file_delete",
                priority=10,
                cooldown=5,
            ),
        )
        self.register(
            Reminder(
                name="stay_focused",
                message=(
                    "[Reminder] Complete the current task before starting new ones. "
                    "Do not refactor, rename, or restructure code the user didn't "
                    "ask you to change."
                ),
                trigger_type=TriggerType.DRIFT_DETECTED,
                trigger_value="scope_creep",
                priority=8,
                cooldown=10,
            ),
        )
        self.register(
            Reminder(
                name="break_apology_loop",
                message=(
                    "[Reminder] If an approach isn't working after 2 attempts, stop "
                    "and explain the blocker to the user instead of retrying the same "
                    "strategy. Ask for guidance."
                ),
                trigger_type=TriggerType.DRIFT_DETECTED,
                trigger_value="apology_loop",
                priority=9,
                cooldown=6,
            ),
        )
        self.register(
            Reminder(
                name="conciseness",
                message=(
                    "[Reminder] Keep explanations concise. Show the code change, "
                    "explain briefly why, move on. Don't repeat what the user already "
                    "knows."
                ),
                trigger_type=TriggerType.PERIODIC,
                trigger_value=None,
                priority=4,
                cooldown=20,
            ),
        )
        self.register(
            Reminder(
                name="budget_warning",
                message=(
                    "[Reminder] Context window is getting full. Be more concise in "
                    "responses. Summarize tool outputs instead of echoing them in full. "
                    "Focus on completing the current task."
                ),
                trigger_type=TriggerType.BUDGET_PRESSURE,
                trigger_value=None,
                priority=10,
                cooldown=10,
            ),
        )

    def register(self, reminder: Reminder) -> None:
        self.reminders[reminder.name] = reminder

    def unregister(self, name: str) -> None:
        self.reminders.pop(name, None)

    def enable(self, name: str) -> None:
        if name in self.reminders:
            self.reminders[name].enabled = True

    def disable(self, name: str) -> None:
        if name in self.reminders:
            self.reminders[name].enabled = False

    def check(
        self,
        turn_number: int,
        last_assistant_msg: str = "",
        pending_tool: str = "",
        budget_utilization: float = 0.0,
    ) -> list[str]:
        self.turn_count = turn_number
        candidates: list[Reminder] = []

        for reminder in self.reminders.values():
            if not reminder.enabled:
                continue
            if (turn_number - reminder.last_fired_turn) < reminder.cooldown:
                continue

            fired = False

            if reminder.trigger_type == TriggerType.PERIODIC:
                interval = self._current_interval()
                if turn_number > 0 and turn_number % interval == 0:
                    fired = True

            elif reminder.trigger_type == TriggerType.TOOL_MATCH:
                if pending_tool and reminder.trigger_value:
                    if re.search(str(reminder.trigger_value), pending_tool, re.I):
                        fired = True

            elif reminder.trigger_type == TriggerType.CONTENT_MATCH:
                if reminder.trigger_value and last_assistant_msg:
                    if re.search(str(reminder.trigger_value), last_assistant_msg, re.I):
                        fired = True

            elif reminder.trigger_type == TriggerType.DRIFT_DETECTED:
                if not self.config.contextual_enabled:
                    continue
                if last_assistant_msg and reminder.trigger_value:
                    detector = getattr(
                        DriftDetectors,
                        str(reminder.trigger_value),
                        None,
                    )
                    if detector and detector(last_assistant_msg):
                        fired = True

            elif reminder.trigger_type == TriggerType.BUDGET_PRESSURE:
                if budget_utilization > 0.80:
                    fired = True

            if fired:
                candidates.append(reminder)

        candidates.sort(key=lambda r: r.priority, reverse=True)
        selected: list[str] = []
        tokens_used = 0

        for reminder in candidates:
            if (
                tokens_used + reminder.token_estimate
                > self.config.max_injection_tokens
            ):
                continue
            selected.append(reminder.message)
            tokens_used += reminder.token_estimate
            reminder.last_fired_turn = turn_number
            reminder.fire_count += 1

        return selected

    def _current_interval(self) -> int:
        if self.turn_count >= self.config.accelerated_after:
            return self.config.accelerated_interval
        return self.config.periodic_interval

    def stats(self) -> dict[str, Any]:
        return {
            name: {
                "fire_count": r.fire_count,
                "last_fired": r.last_fired_turn,
                "enabled": r.enabled,
            }
            for name, r in self.reminders.items()
        }
