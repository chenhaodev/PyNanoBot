"""Lifecycle hook registry (user callbacks + optional shell hooks from config).

Distinct from :mod:`nanobot.agent.hook` (runner :class:`AgentHook` protocol).

Shell hook filters use *path_glob* (``fnmatch``) instead of arbitrary Python
expressions, so user config stays safe to load.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger


class HookType(Enum):
    OBSERVER = auto()
    FILTER = auto()
    ASYNC_BG = auto()


class HookPoint(str, Enum):
    SESSION_START = "on_session_start"
    SESSION_END = "on_session_end"
    TURN_START = "on_turn_start"
    TURN_END = "on_turn_end"
    TOOL_PRE = "on_tool_pre"
    TOOL_POST = "on_tool_post"
    FILE_WRITE = "on_file_write"
    FILE_READ = "on_file_read"
    COMPACT = "on_compact"
    ERROR = "on_error"
    REMINDER_INJECTED = "on_reminder_injected"
    MEMORY_WRITE = "on_memory_write"


@dataclass
class HookEvent:
    hook_point: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    session_turn: int = 0
    cancelled: bool = False
    result_data: Optional[dict[str, Any]] = None


@dataclass
class RegisteredHook:
    name: str
    hook_point: str
    callback: Callable[[HookEvent], Any]
    hook_type: HookType = HookType.OBSERVER
    priority: int = 5
    enabled: bool = True
    condition: Optional[Callable[[HookEvent], bool]] = None
    invocation_count: int = 0
    total_time_ms: float = 0.0
    last_error: Optional[str] = None


@dataclass
class ShellHookConfig:
    """Entry in ``.nanobot/hooks.json``."""

    name: str
    on: str
    command: str
    path_glob: str = ""
    timeout: int = 10
    enabled: bool = True


class LifecycleHookManager:
    """Register and fire lifecycle callbacks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[RegisteredHook]] = {
            hp.value: [] for hp in HookPoint
        }
        self._shell_configs: list[ShellHookConfig] = []
        self._event_log: list[dict[str, Any]] = []
        self._max_log_size = 200

    def on(
        self,
        hook_point: str,
        name: Optional[str] = None,
        hook_type: HookType = HookType.OBSERVER,
        priority: int = 5,
        condition: Optional[Callable[[HookEvent], bool]] = None,
    ) -> Callable[[Callable[[HookEvent], Any]], Callable[[HookEvent], Any]]:
        def decorator(fn: Callable[[HookEvent], Any]) -> Callable[[HookEvent], Any]:
            hook_name = name or fn.__name__
            self.register(
                RegisteredHook(
                    name=hook_name,
                    hook_point=hook_point,
                    callback=fn,
                    hook_type=hook_type,
                    priority=priority,
                    condition=condition,
                ),
            )
            return fn

        return decorator

    def register(self, hook: RegisteredHook) -> None:
        point = hook.hook_point
        if point not in self._hooks:
            self._hooks[point] = []
        self._hooks[point].append(hook)
        self._hooks[point].sort(key=lambda h: h.priority, reverse=True)

    def unregister(self, name: str) -> None:
        for point in self._hooks:
            self._hooks[point] = [h for h in self._hooks[point] if h.name != name]

    def enable(self, name: str) -> None:
        for hooks in self._hooks.values():
            for h in hooks:
                if h.name == name:
                    h.enabled = True

    def disable(self, name: str) -> None:
        for hooks in self._hooks.values():
            for h in hooks:
                if h.name == name:
                    h.enabled = False

    def load_shell_hooks(self, workspace_path: str | Path) -> int:
        hooks_file = Path(workspace_path) / ".nanobot" / "hooks.json"
        if not hooks_file.exists():
            return 0

        try:
            raw = json.loads(hooks_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            self._log_event("shell_hook_load_error", {"error": str(exc)})
            return 0

        loaded = 0
        for entry in raw.get("hooks", []):
            try:
                name = entry["name"]
                on = entry["on"]
                command = entry["command"]
                path_glob = entry.get("path_glob", "")
                timeout = int(entry.get("timeout", 10))
                enabled = bool(entry.get("enabled", True))
                shell_config = ShellHookConfig(
                    name=name,
                    on=on,
                    command=command,
                    path_glob=path_glob,
                    timeout=timeout,
                    enabled=enabled,
                )
                self._shell_configs.append(shell_config)
                self.register(
                    RegisteredHook(
                        name=f"shell:{shell_config.name}",
                        hook_point=shell_config.on,
                        callback=self._make_shell_callback(shell_config),
                        hook_type=HookType.OBSERVER,
                        priority=3,
                        enabled=shell_config.enabled,
                    ),
                )
                loaded += 1
            except (KeyError, TypeError, ValueError) as exc:
                self._log_event(
                    "shell_hook_parse_error",
                    {"entry": entry, "error": str(exc)},
                )

        return loaded

    def _path_matches_shell_filter(
        self,
        config: ShellHookConfig,
        event: HookEvent,
    ) -> bool:
        if not config.path_glob.strip():
            return True
        path = event.data.get("path")
        if not isinstance(path, str):
            return False
        return fnmatch.fnmatch(path.replace("\\", "/"), config.path_glob)

    def _make_shell_callback(
        self,
        config: ShellHookConfig,
    ) -> Callable[[HookEvent], None]:
        def callback(event: HookEvent) -> None:
            if not self._path_matches_shell_filter(config, event):
                return

            try:
                cmd = config.command.format(**event.data)
            except KeyError:
                return

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                    cwd=event.data.get("workspace"),
                )
                if result.returncode != 0:
                    self._log_event(
                        "shell_hook_failed",
                        {
                            "hook": config.name,
                            "command": cmd,
                            "returncode": result.returncode,
                            "stderr": result.stderr[:500],
                        },
                    )
            except subprocess.TimeoutExpired:
                self._log_event(
                    "shell_hook_timeout",
                    {
                        "hook": config.name,
                        "command": cmd,
                        "timeout": config.timeout,
                    },
                )
            except OSError as exc:
                self._log_event(
                    "shell_hook_error",
                    {"hook": config.name, "error": str(exc)},
                )

        return callback

    def fire(
        self,
        hook_point: str,
        data: dict[str, Any],
        session_turn: int = 0,
    ) -> HookEvent:
        event = HookEvent(
            hook_point=hook_point,
            data=data.copy(),
            session_turn=session_turn,
        )
        event.result_data = data.copy()

        hooks = self._hooks.get(hook_point, [])
        if not hooks:
            return event

        for hook in hooks:
            if not hook.enabled:
                continue
            if hook.condition and not hook.condition(event):
                continue

            start = time.time()
            try:
                result = hook.callback(event)

                if hook.hook_type == HookType.FILTER:
                    if result is None:
                        event.cancelled = True
                        self._log_event(
                            "hook_cancelled_event",
                            {
                                "hook": hook.name,
                                "hook_point": hook_point,
                            },
                        )
                        break
                    if isinstance(result, dict):
                        event.data = result
                        event.result_data = result

            except Exception as exc:
                hook.last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "Lifecycle hook {} failed: {}",
                    hook.name,
                    hook.last_error,
                )
                self._log_event(
                    "hook_error",
                    {
                        "hook": hook.name,
                        "hook_point": hook_point,
                        "error": hook.last_error,
                        "traceback": traceback.format_exc()[:500],
                    },
                )
            finally:
                elapsed = (time.time() - start) * 1000
                hook.invocation_count += 1
                hook.total_time_ms += elapsed

        self._log_event(
            "hook_fired",
            {
                "hook_point": hook_point,
                "cancelled": event.cancelled,
            },
        )

        return event

    def fire_tool_pre(self, tool_name: str, tool_args: dict, **extra: Any) -> HookEvent:
        return self.fire(
            HookPoint.TOOL_PRE.value,
            {"tool": tool_name, "args": tool_args, **extra},
        )

    def fire_tool_post(
        self,
        tool_name: str,
        tool_result: Any,
        **extra: Any,
    ) -> HookEvent:
        return self.fire(
            HookPoint.TOOL_POST.value,
            {"tool": tool_name, "result": tool_result, **extra},
        )

    def fire_file_write(self, path: str, content: str, **extra: Any) -> HookEvent:
        return self.fire(
            HookPoint.FILE_WRITE.value,
            {"path": path, "content": content, **extra},
        )

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        entry = {"type": event_type, "time": time.time(), **data}
        self._event_log.append(entry)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size :]

    def stats(self) -> dict[str, Any]:
        all_hooks: list[dict[str, Any]] = []
        for hooks in self._hooks.values():
            for h in hooks:
                all_hooks.append(
                    {
                        "name": h.name,
                        "hook_point": h.hook_point,
                        "type": h.hook_type.name,
                        "enabled": h.enabled,
                        "invocations": h.invocation_count,
                        "avg_ms": (
                            round(h.total_time_ms / h.invocation_count, 2)
                            if h.invocation_count > 0
                            else 0
                        ),
                        "last_error": h.last_error,
                    },
                )
        return {
            "registered_hooks": len(all_hooks),
            "hooks": all_hooks,
            "recent_events": self._event_log[-10:],
        }

    def list_hooks(self, hook_point: Optional[str] = None) -> list[str]:
        if hook_point:
            return [h.name for h in self._hooks.get(hook_point, [])]
        return [h.name for hooks in self._hooks.values() for h in hooks]
