# Fork 逻辑在 `pynanobot/ext` 中的位置

以下模块的**实现**已迁出 `nanobot/agent/*.py`，置于 **`pynanobot/ext/`**（单一起源）；`nanobot/agent/` 下同名文件仅为 **兼容重导出**，便于旧 `import` 路径继续工作：

| 实现位置 | 兼容路径 |
|----------|----------|
| `pynanobot/ext/reminders.py` | `nanobot.agent.reminders` |
| `pynanobot/ext/lifecycle_hooks.py` | `nanobot.agent.lifecycle_hooks` |
| `pynanobot/ext/compactor.py` | `nanobot.agent.compactor` |
| `pynanobot/ext/delegation.py` | `nanobot.agent.delegation` |
| `pynanobot/ext/runner.py` | （核心 `AgentRunner` 仍在上游 `nanobot/agent/runner.py`；fork 行为在 `PyNanoAgentRunner`） |
| `pynanobot/ext/loop.py` | （核心 `AgentLoop` 仍在上游 `nanobot/agent/loop.py`；CLI/SDK 使用 `PyNanoAgentLoop`） |

`nanobot.agent` 包的 `__init__.py` 对上述符号改为 **直接从 `pynanobot.ext.*` 导入**，减少对重导出的二次跳转。

## 循环导入说明

`pynanobot/__init__.py` 对 `Nanobot` / `RunResult` 等使用 **延迟加载**（`__getattr__`），避免在导入 `pynanobot.ext` 时提前执行 `from nanobot import …` 而与 `nanobot.agent` 初始化形成环。

## 尚未迁出的 fork 逻辑

- **`nanobot/config/schema.py`** 中 `reminders_enabled` / `lifecycle_hooks_enabled`（配置字段；可与上游协调或保留在 fork 直至上游支持插件配置）。

提醒注入、生命周期 shell 钩子在 **`PyNanoAgentRunner`** / **`PyNanoAgentLoop`**（`pynanobot/ext/runner.py`、`pynanobot/ext/loop.py`）；上游 **`AgentRunner`** / **`AgentLoop`** 保持无此接线，便于与 `nanobot-ai` 合并对比。
