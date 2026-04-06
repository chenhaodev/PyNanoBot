"""Fork agent runner: reminders + lifecycle hooks around core :class:`AgentRunner`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from loguru import logger

from nanobot.agent.hook import AgentHook, AgentHookContext
from nanobot.agent.runner import AgentRunResult, AgentRunSpec, AgentRunner
from nanobot.providers.base import ToolCallRequest
from nanobot.utils.helpers import (
    build_assistant_message,
    estimate_prompt_tokens_chain,
    find_legal_message_start,
    maybe_persist_tool_result,
    truncate_text,
)
from nanobot.utils.prompt_templates import render_template
from nanobot.utils.runtime import (
    EMPTY_FINAL_RESPONSE_MESSAGE,
    build_finalization_retry_message,
    ensure_nonempty_tool_result,
    is_blank_text,
    repeated_external_lookup_error,
)

from pynanobot.ext.lifecycle_hooks import HookPoint

_DEFAULT_ERROR_MESSAGE = "Sorry, I encountered an error calling the AI model."
_SNIP_SAFETY_BUFFER = 1024


@dataclass(slots=True)
class PyNanoAgentRunSpec(AgentRunSpec):
    """Like :class:`AgentRunSpec` with optional reminder engine and lifecycle hooks."""

    reminder_engine: Any | None = None
    lifecycle_hooks: Any | None = None


class PyNanoAgentRunner(AgentRunner):
    """Core runner plus PyNanoBot reminder injection and lifecycle shell hooks."""

    async def run(self, spec: AgentRunSpec) -> AgentRunResult:
        hook = spec.hook or AgentHook()
        messages = list(spec.initial_messages)
        final_content: str | None = None
        tools_used: list[str] = []
        usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}
        error: str | None = None
        stop_reason = "completed"
        tool_events: list[dict[str, str]] = []
        external_lookup_counts: dict[str, int] = {}
        lifecycle = getattr(spec, "lifecycle_hooks", None)
        workspace_str = str(spec.workspace) if spec.workspace else ""

        try:
            for iteration in range(spec.max_iterations):
                try:
                    messages = self._apply_tool_result_budget(spec, messages)
                    messages_for_model = self._snip_history(spec, messages)
                except Exception as exc:
                    logger.warning(
                        "Context governance failed on turn {} for {}: {}; using raw messages",
                        iteration,
                        spec.session_key or "default",
                        exc,
                    )
                    messages_for_model = messages

                if lifecycle and iteration == 0:
                    lifecycle.fire(
                        HookPoint.SESSION_START.value,
                        {
                            "workspace": workspace_str,
                            "session_key": spec.session_key or "",
                        },
                        session_turn=0,
                    )

                if lifecycle:
                    lifecycle.fire(
                        HookPoint.TURN_START.value,
                        {
                            "iteration": iteration,
                            "workspace": workspace_str,
                            "session_key": spec.session_key or "",
                        },
                        session_turn=iteration,
                    )

                request_messages = list(messages_for_model)
                reminder_engine = getattr(spec, "reminder_engine", None)
                if reminder_engine:
                    last_assistant = self._last_assistant_text(messages)
                    budget_util = self._budget_utilization_ratio(
                        spec,
                        messages_for_model,
                    )
                    turn_no = iteration + 1
                    for text in reminder_engine.check(
                        turn_no,
                        last_assistant,
                        "",
                        budget_util,
                    ):
                        request_messages.append({"role": "system", "content": text})
                        if lifecycle:
                            lifecycle.fire(
                                HookPoint.REMINDER_INJECTED.value,
                                {
                                    "text": text,
                                    "iteration": iteration,
                                    "workspace": workspace_str,
                                    "session_key": spec.session_key or "",
                                },
                                session_turn=iteration,
                            )

                context = AgentHookContext(iteration=iteration, messages=messages)
                await hook.before_iteration(context)
                response = await self._request_model(
                    spec,
                    request_messages,
                    hook,
                    context,
                )
                raw_usage = self._usage_dict(response.usage)
                context.response = response
                context.usage = dict(raw_usage)
                context.tool_calls = list(response.tool_calls)
                self._accumulate_usage(usage, raw_usage)

                if response.has_tool_calls:
                    if hook.wants_streaming():
                        await hook.on_stream_end(context, resuming=True)

                    assistant_message = build_assistant_message(
                        response.content or "",
                        tool_calls=[tc.to_openai_tool_call() for tc in response.tool_calls],
                        reasoning_content=response.reasoning_content,
                        thinking_blocks=response.thinking_blocks,
                    )
                    messages.append(assistant_message)
                    tools_used.extend(tc.name for tc in response.tool_calls)
                    await self._emit_checkpoint(
                        spec,
                        {
                            "phase": "awaiting_tools",
                            "iteration": iteration,
                            "model": spec.model,
                            "assistant_message": assistant_message,
                            "completed_tool_results": [],
                            "pending_tool_calls": [tc.to_openai_tool_call() for tc in response.tool_calls],
                        },
                    )

                    await hook.before_execute_tools(context)

                    results, new_events, fatal_error = await self._execute_tools(
                        spec,
                        response.tool_calls,
                        external_lookup_counts,
                    )
                    tool_events.extend(new_events)
                    context.tool_results = list(results)
                    context.tool_events = list(new_events)
                    if fatal_error is not None:
                        error = f"Error: {type(fatal_error).__name__}: {fatal_error}"
                        final_content = error
                        stop_reason = "tool_error"
                        self._append_final_message(messages, final_content)
                        context.final_content = final_content
                        context.error = error
                        context.stop_reason = stop_reason
                        await self._after_iteration(spec, hook, context)
                        break
                    completed_tool_results: list[dict[str, Any]] = []
                    for tool_call, result in zip(response.tool_calls, results):
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.name,
                            "content": self._normalize_tool_result(
                                spec,
                                tool_call.id,
                                tool_call.name,
                                result,
                            ),
                        }
                        messages.append(tool_message)
                        completed_tool_results.append(tool_message)
                    await self._emit_checkpoint(
                        spec,
                        {
                            "phase": "tools_completed",
                            "iteration": iteration,
                            "model": spec.model,
                            "assistant_message": assistant_message,
                            "completed_tool_results": completed_tool_results,
                            "pending_tool_calls": [],
                        },
                    )
                    await self._after_iteration(spec, hook, context)
                    continue

                clean = hook.finalize_content(context, response.content)
                if response.finish_reason != "error" and is_blank_text(clean):
                    logger.warning(
                        "Empty final response on turn {} for {}; retrying with explicit finalization prompt",
                        iteration,
                        spec.session_key or "default",
                    )
                    if hook.wants_streaming():
                        await hook.on_stream_end(context, resuming=False)
                    response = await self._request_finalization_retry(spec, messages_for_model)
                    retry_usage = self._usage_dict(response.usage)
                    self._accumulate_usage(usage, retry_usage)
                    raw_usage = self._merge_usage(raw_usage, retry_usage)
                    context.response = response
                    context.usage = dict(raw_usage)
                    context.tool_calls = list(response.tool_calls)
                    clean = hook.finalize_content(context, response.content)

                if hook.wants_streaming():
                    await hook.on_stream_end(context, resuming=False)

                if response.finish_reason == "error":
                    final_content = clean or spec.error_message or _DEFAULT_ERROR_MESSAGE
                    stop_reason = "error"
                    error = final_content
                    self._append_final_message(messages, final_content)
                    context.final_content = final_content
                    context.error = error
                    context.stop_reason = stop_reason
                    await self._after_iteration(spec, hook, context)
                    break
                if is_blank_text(clean):
                    final_content = EMPTY_FINAL_RESPONSE_MESSAGE
                    stop_reason = "empty_final_response"
                    error = final_content
                    self._append_final_message(messages, final_content)
                    context.final_content = final_content
                    context.error = error
                    context.stop_reason = stop_reason
                    await self._after_iteration(spec, hook, context)
                    break

                messages.append(build_assistant_message(
                    clean,
                    reasoning_content=response.reasoning_content,
                    thinking_blocks=response.thinking_blocks,
                ))
                await self._emit_checkpoint(
                    spec,
                    {
                        "phase": "final_response",
                        "iteration": iteration,
                        "model": spec.model,
                        "assistant_message": messages[-1],
                        "completed_tool_results": [],
                        "pending_tool_calls": [],
                    },
                )
                final_content = clean
                context.final_content = final_content
                context.stop_reason = stop_reason
                await self._after_iteration(spec, hook, context)
                break
            else:
                stop_reason = "max_iterations"
                if spec.max_iterations_message:
                    final_content = spec.max_iterations_message.format(
                        max_iterations=spec.max_iterations,
                    )
                else:
                    final_content = render_template(
                        "agent/max_iterations_message.md",
                        strip=True,
                        max_iterations=spec.max_iterations,
                    )
                self._append_final_message(messages, final_content)

        finally:
            if lifecycle:
                lifecycle.fire(
                    HookPoint.SESSION_END.value,
                    {
                        "workspace": workspace_str,
                        "session_key": spec.session_key or "",
                    },
                )

        return AgentRunResult(
            final_content=final_content,
            messages=messages,
            tools_used=tools_used,
            usage=usage,
            stop_reason=stop_reason,
            error=error,
            tool_events=tool_events,
        )

    async def _after_iteration(
        self,
        spec: AgentRunSpec,
        hook: AgentHook,
        context: AgentHookContext,
    ) -> None:
        lifecycle = getattr(spec, "lifecycle_hooks", None)
        if lifecycle:
            lifecycle.fire(
                HookPoint.TURN_END.value,
                {
                    "iteration": context.iteration,
                    "session_key": spec.session_key or "",
                    "workspace": str(spec.workspace) if spec.workspace else "",
                },
                session_turn=context.iteration,
            )
        await hook.after_iteration(context)

    @staticmethod
    def _last_assistant_text(messages: list[dict[str, Any]]) -> str:
        for msg in reversed(messages):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                text = "".join(parts).strip()
                if text:
                    return text
        return ""

    def _budget_utilization_ratio(
        self,
        spec: AgentRunSpec,
        messages_for_model: list[dict[str, Any]],
    ) -> float:
        if not spec.context_window_tokens:
            return 0.0
        estimate, _ = estimate_prompt_tokens_chain(
            self.provider,
            spec.model,
            messages_for_model,
            spec.tools.get_definitions(),
        )
        cap = float(spec.context_window_tokens)
        if cap <= 0:
            return 0.0
        return min(1.0, estimate / cap)

    async def _run_tool(
        self,
        spec: AgentRunSpec,
        tool_call: ToolCallRequest,
        external_lookup_counts: dict[str, int],
    ) -> tuple[Any, dict[str, str], BaseException | None]:
        _HINT = "\n\n[Analyze the error above and try a different approach.]"
        lookup_error = repeated_external_lookup_error(
            tool_call.name,
            tool_call.arguments,
            external_lookup_counts,
        )
        if lookup_error:
            event = {
                "name": tool_call.name,
                "status": "error",
                "detail": "repeated external lookup blocked",
            }
            if spec.fail_on_tool_error:
                return lookup_error + _HINT, event, RuntimeError(lookup_error)
            return lookup_error + _HINT, event, None
        prepare_call = getattr(spec.tools, "prepare_call", None)
        tool, params, prep_error = None, tool_call.arguments, None
        if callable(prepare_call):
            try:
                prepared = prepare_call(tool_call.name, tool_call.arguments)
                if isinstance(prepared, tuple) and len(prepared) == 3:
                    tool, params, prep_error = prepared
            except Exception:
                pass
        if prep_error:
            event = {
                "name": tool_call.name,
                "status": "error",
                "detail": prep_error.split(": ", 1)[-1][:120],
            }
            return prep_error + _HINT, event, RuntimeError(prep_error) if spec.fail_on_tool_error else None
        ws = str(spec.workspace) if spec.workspace else ""
        sk = spec.session_key or ""
        args_dict = (
            tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
        )
        lifecycle = getattr(spec, "lifecycle_hooks", None)
        if lifecycle:
            lifecycle.fire_tool_pre(
                tool_call.name,
                args_dict,
                workspace=ws,
                session_key=sk,
            )
        try:
            if tool is not None:
                result = await tool.execute(**params)
            else:
                result = await spec.tools.execute(tool_call.name, params)
        except asyncio.CancelledError:
            raise
        except BaseException as exc:
            if lifecycle:
                lifecycle.fire_tool_post(
                    tool_call.name,
                    f"Error: {type(exc).__name__}: {exc}",
                    workspace=ws,
                    session_key=sk,
                )
            event = {
                "name": tool_call.name,
                "status": "error",
                "detail": str(exc),
            }
            if spec.fail_on_tool_error:
                return f"Error: {type(exc).__name__}: {exc}", event, exc
            return f"Error: {type(exc).__name__}: {exc}", event, None

        if lifecycle:
            lifecycle.fire_tool_post(
                tool_call.name,
                result,
                workspace=ws,
                session_key=sk,
            )

        if isinstance(result, str) and result.startswith("Error"):
            event = {
                "name": tool_call.name,
                "status": "error",
                "detail": result.replace("\n", " ").strip()[:120],
            }
            if spec.fail_on_tool_error:
                return result + _HINT, event, RuntimeError(result)
            return result + _HINT, event, None

        detail = "" if result is None else str(result)
        detail = detail.replace("\n", " ").strip()
        if not detail:
            detail = "(empty)"
        elif len(detail) > 120:
            detail = detail[:120] + "..."
        return result, {"name": tool_call.name, "status": "ok", "detail": detail}, None
