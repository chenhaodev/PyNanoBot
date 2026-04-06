"""Agent core module."""

from nanobot.agent.context import ContextBuilder
from nanobot.agent.hook import AgentHook, AgentHookContext, CompositeHook
from nanobot.agent.loop import AgentLoop
from nanobot.agent.compactor import ContextCompactor, estimate_tokens
from nanobot.agent.memory import Consolidator, Dream, MemoryEntry, MemoryStore
from nanobot.agent.skills import SkillsLoader
from nanobot.agent.subagent import SubagentManager

__all__ = [
    "AgentHook",
    "AgentHookContext",
    "AgentLoop",
    "CompositeHook",
    "ContextBuilder",
    "ContextCompactor",
    "Dream",
    "estimate_tokens",
    "MemoryEntry",
    "MemoryStore",
    "SkillsLoader",
    "SubagentManager",
]
