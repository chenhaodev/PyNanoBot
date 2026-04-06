# PyNanoBot 仓库布局说明

为避免与上游 **nanobot** 混淆，约定如下：

| 路径 | 含义 |
|------|------|
| `nanobot/` | Python 包，与上游同构，便于 `git merge` / diff；阶段 3 起可只依赖 PyPI `nanobot-ai`，见 `docs/EVOLUTION_MODEL_A.md`。 |
| `pynanobot/` | 发行层命名空间：`import pynanobot`、`import pynanobot.agent` 转发到 `nanobot`；CLI 命令 `pynanobot` 与 `nanobot` 等价入口。 |
| `pynanobot/ext/` | PyNanoBot **专有扩展**：`reminders`、`lifecycle_hooks`、`compactor`、`delegation` 等实现已在此；`nanobot/agent/` 下同名文件多为重导出，见 `docs/FORK_IN_EXT.md`。 |
| `scripts/report_fork_diff.py` | 在配置 `upstream` 远程后，统计 `nanobot/` 相对 `upstream/main` 的差异。 |
| `docs/` | PyNanoBot 发行版文档（哲学、上游同步、版本、路线图）。 |
| `plans/` | 设计与实现对照（偏本仓库演进）。 |
| `upstream.lock` | 上游基线（commit/tag）与发行版版本，发版时更新。 |
| `tests/` | 与上游一致的测试布局；新增用例放在对应子目录。 |

若未来引入 **仅本仓库** 的大型子系统，优先：

- 独立 Python 包名空间（如 `pynanobot_ext.*`），或
- 文档中写清扩展点，避免与 `nanobot.*` 核心混名。
