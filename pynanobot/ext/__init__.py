"""PyNanoBot-only extensions (fork logic; depends on ``nanobot`` core).

Implemented modules:

- ``reminders`` — anti-drift reminder engine
- ``lifecycle_hooks`` — workspace lifecycle + optional ``hooks.json`` shell hooks
- ``runner`` — :class:`PyNanoAgentRunner` / :class:`PyNanoAgentRunSpec` (reminders + hooks)
- ``loop`` — :class:`PyNanoAgentLoop` (CLI / gateway / SDK wiring)
- ``compactor`` — tiered context compactor
- ``delegation`` — scoped subagent orchestration

See ``docs/FORK_IN_EXT.md``.
"""

from __future__ import annotations

__all__: list[str] = []
