"""Agent core module."""

from nanobot.agent.context import ContextBuilder
from nanobot.agent.hook import AgentHook, AgentHookContext, CompositeHook
from nanobot.agent.loop import AgentLoop
from nanobot.agent.compactor import ContextCompactor, estimate_tokens
from nanobot.agent.delegation import (
    DelegationPlan,
    FileScope,
    MergeReport,
    MergeStrategy,
    ScopedDelegationRunner,
    SubagentOrchestrator,
    SubagentResult,
    SubagentStatus,
    SubagentTask,
)
from nanobot.agent.lifecycle_hooks import (
    HookEvent,
    HookPoint,
    HookType,
    LifecycleHookManager,
    RegisteredHook,
    ShellHookConfig,
)
from nanobot.agent.memory import Consolidator, Dream, MemoryEntry, MemoryStore
from nanobot.agent.reminders import (
    DriftDetectors,
    Reminder,
    ReminderConfig,
    ReminderEngine,
    TriggerType,
)
from nanobot.agent.skills import SkillsLoader
from nanobot.agent.subagent import SubagentManager

__all__ = [
    "AgentHook",
    "AgentHookContext",
    "AgentLoop",
    "CompositeHook",
    "ContextBuilder",
    "ContextCompactor",
    "DelegationPlan",
    "DriftDetectors",
    "Dream",
    "estimate_tokens",
    "FileScope",
    "HookEvent",
    "HookPoint",
    "HookType",
    "LifecycleHookManager",
    "MergeReport",
    "MergeStrategy",
    "MemoryEntry",
    "MemoryStore",
    "RegisteredHook",
    "Reminder",
    "ReminderConfig",
    "ReminderEngine",
    "ScopedDelegationRunner",
    "ShellHookConfig",
    "SkillsLoader",
    "SubagentManager",
    "SubagentOrchestrator",
    "SubagentResult",
    "SubagentStatus",
    "SubagentTask",
    "TriggerType",
]
