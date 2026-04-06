"""Tests for LifecycleHookManager."""

import json
from pathlib import Path

import pytest

from nanobot.agent.lifecycle_hooks import (
    HookEvent,
    HookPoint,
    HookType,
    LifecycleHookManager,
    ShellHookConfig,
)


def test_fire_observer_runs() -> None:
    mgr = LifecycleHookManager()
    seen: list[str] = []

    @mgr.on(HookPoint.TURN_START.value, name="t1")
    def _h(ev: HookEvent) -> None:
        seen.append(ev.data.get("x", ""))

    ev = mgr.fire(HookPoint.TURN_START.value, {"x": "1"})
    assert not ev.cancelled
    assert seen == ["1"]


def test_filter_cancels() -> None:
    mgr = LifecycleHookManager()

    @mgr.on(
        HookPoint.TOOL_PRE.value,
        name="block",
        hook_type=HookType.FILTER,
        priority=10,
    )
    def _block(ev: HookEvent) -> dict | None:
        if ev.data.get("args", {}).get("cmd") == "bad":
            return None
        return ev.data

    ev = mgr.fire(
        HookPoint.TOOL_PRE.value,
        {"tool": "exec", "args": {"cmd": "bad"}},
    )
    assert ev.cancelled


def test_load_shell_hooks_path_glob(tmp_path: Path) -> None:
    nb = tmp_path / ".nanobot"
    nb.mkdir()
    hooks_file = nb / "hooks.json"
    hooks_file.write_text(
        json.dumps(
            {
                "hooks": [
                    {
                        "name": "touch_py",
                        "on": "on_file_write",
                        "command": "touch {path}.done",
                        "path_glob": "*.py",
                        "timeout": 5,
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    mgr = LifecycleHookManager()
    n = mgr.load_shell_hooks(tmp_path)
    assert n == 1
    assert "shell:touch_py" in mgr.list_hooks()


def test_shell_hook_config_dataclass() -> None:
    c = ShellHookConfig(
        name="x",
        on="on_file_write",
        command="echo {path}",
        path_glob="*.md",
    )
    assert c.path_glob == "*.md"
