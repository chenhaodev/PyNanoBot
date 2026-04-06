# 阶段 3 落地说明（wheel 与依赖）

## 行为

- **PyPI / `pip install pynanobot`**：wheel **仅**包含 `pynanobot/`；`nanobot` 来自依赖 **`nanobot-ai`**（与 `upstream.lock` 对齐的版本范围）。
- **`nanobot` / `pynanobot` 命令**：`nanobot` 由 **`nanobot-ai`** 提供；`pynanobot` 由本包提供（等价入口，见 `pynanobot.cli`）。
- **Git 克隆开发**：仓库内仍保留 **`nanobot/`** 目录；在仓库根目录运行 `pytest` / `python` 时，若当前目录在 `sys.path` 首位，**会优先加载工作区内的 `nanobot/`**，便于继续维护 fork，与「仅 wheel 依赖上游」不矛盾。

## 与上游 PyPI 的差异

若本仓库的 `nanobot/` 仍比 PyPI `nanobot-ai` 同版本 **多提交**，则：

- **仅安装 wheel 的用户**得到的是 **PyPI 上的上游行为**；
- **从源码运行的开发者**仍使用 **克隆下来的 `nanobot/`**。

缩小差异的方式：向上游合并、或把独有逻辑迁到 `pynanobot/ext/`。

## 旧安装方式迁移

曾使用 `pip install nanobot-ai` 且从本仓库安装的用户，请改为：

```bash
pip install pynanobot
```

`import nanobot` 仍由 `nanobot-ai` 提供；`import pynanobot` 为发行层。
