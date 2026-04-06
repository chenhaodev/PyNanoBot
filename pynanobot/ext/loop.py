"""Fork agent loop: reminders, lifecycle shell hooks, :class:`PyNanoAgentRunner`."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from loguru import logger

from nanobot.agent.hook import AgentHook
from nanobot.agent.loop import (
    AgentLoop,
    _LoopHook,
    _LoopHookChain,
)
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import AgentDefaults
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import Session, SessionManager

from pynanobot.ext.reminders import ReminderEngine
from pynanobot.ext.runner import PyNanoAgentRunSpec, PyNanoAgentRunner

if TYPE_CHECKING:
    from nanobot.config.schema import ChannelsConfig, ExecToolConfig, WebToolsConfig
    from nanobot.cron.service import CronService


class PyNanoAgentLoop(AgentLoop):
    """Like :class:`AgentLoop` with reminder injection and optional lifecycle shell hooks."""

    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int | None = None,
        context_window_tokens: int | None = None,
        context_block_limit: int | None = None,
        max_tool_result_chars: int | None = None,
        provider_retry_mode: str = "standard",
        web_config: WebToolsConfig | None = None,
        exec_config: ExecToolConfig | None = None,
        cron_service: CronService | None = None,
        restrict_to_workspace: bool = False,
        session_manager: SessionManager | None = None,
        mcp_servers: dict | None = None,
        channels_config: ChannelsConfig | None = None,
        timezone: str | None = None,
        hooks: list[AgentHook] | None = None,
        reminders_enabled: bool | None = None,
        lifecycle_hooks_enabled: bool | None = None,
    ):
        super().__init__(
            bus=bus,
            provider=provider,
            workspace=workspace,
            model=model,
            max_iterations=max_iterations,
            context_window_tokens=context_window_tokens,
            context_block_limit=context_block_limit,
            max_tool_result_chars=max_tool_result_chars,
            provider_retry_mode=provider_retry_mode,
            web_config=web_config,
            exec_config=exec_config,
            cron_service=cron_service,
            restrict_to_workspace=restrict_to_workspace,
            session_manager=session_manager,
            mcp_servers=mcp_servers,
            channels_config=channels_config,
            timezone=timezone,
            hooks=hooks,
        )
        defaults = AgentDefaults()
        self._reminders_enabled = (
            reminders_enabled
            if reminders_enabled is not None
            else defaults.reminders_enabled
        )
        self._lifecycle_hooks_enabled = (
            lifecycle_hooks_enabled
            if lifecycle_hooks_enabled is not None
            else defaults.lifecycle_hooks_enabled
        )
        self.lifecycle_hooks = None
        if self._lifecycle_hooks_enabled:
            from pynanobot.ext.lifecycle_hooks import LifecycleHookManager

            self.lifecycle_hooks = LifecycleHookManager()
            n_hooks = self.lifecycle_hooks.load_shell_hooks(workspace)
            if n_hooks:
                logger.info(
                    "Loaded {} lifecycle shell hook(s) from .nanobot/hooks.json",
                    n_hooks,
                )
        self.runner = PyNanoAgentRunner(self.provider)

    async def _run_agent_loop(
        self,
        initial_messages: list[dict],
        on_progress: Callable[..., Awaitable[None]] | None = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_stream_end: Callable[..., Awaitable[None]] | None = None,
        *,
        session: Session | None = None,
        channel: str = "cli",
        chat_id: str = "direct",
        message_id: str | None = None,
    ) -> tuple[str | None, list[str], list[dict]]:
        loop_hook = _LoopHook(
            self,
            on_progress=on_progress,
            on_stream=on_stream,
            on_stream_end=on_stream_end,
            channel=channel,
            chat_id=chat_id,
            message_id=message_id,
        )
        hook: AgentHook = (
            _LoopHookChain(loop_hook, self._extra_hooks)
            if self._extra_hooks
            else loop_hook
        )

        async def _checkpoint(payload: dict[str, Any]) -> None:
            if session is None:
                return
            self._set_runtime_checkpoint(session, payload)

        reminder_engine = None
        if self._reminders_enabled:
            reminder_engine = ReminderEngine()

        result = await self.runner.run(PyNanoAgentRunSpec(
            initial_messages=initial_messages,
            tools=self.tools,
            model=self.model,
            max_iterations=self.max_iterations,
            max_tool_result_chars=self.max_tool_result_chars,
            hook=hook,
            error_message="Sorry, I encountered an error calling the AI model.",
            concurrent_tools=True,
            workspace=self.workspace,
            session_key=session.key if session else None,
            context_window_tokens=self.context_window_tokens,
            context_block_limit=self.context_block_limit,
            provider_retry_mode=self.provider_retry_mode,
            progress_callback=on_progress,
            checkpoint_callback=_checkpoint,
            reminder_engine=reminder_engine,
            lifecycle_hooks=self.lifecycle_hooks,
        ))
        self._last_usage = result.usage
        if result.stop_reason == "max_iterations":
            logger.warning("Max iterations ({}) reached", self.max_iterations)
        elif result.stop_reason == "error":
            logger.error("LLM returned error: {}", (result.final_content or "")[:200])
        return result.final_content, result.tools_used, result.messages
