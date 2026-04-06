<div align="center">

# PyNanoBot

**在 [nanobot](https://github.com/HKUDS/nanobot)（OpenClaw 精简线）之上，搭建发行层与扩展：引入高级智能体 / VibeCoding 可落地模式，并优先适配小模型与 GGUF。**

[![PyPI](https://img.shields.io/pypi/v/pynanobot)](https://pypi.org/project/pynanobot/)
[![Python](https://img.shields.io/badge/python-≥3.11-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Upstream](https://img.shields.io/badge/upstream-HKUDS%2Fnanobot-8A2BE2)](https://github.com/HKUDS/nanobot)

</div>

---

## English summary

**PyNanoBot** is a **distribution and extension layer** on top of the **nanobot** agent runtime (PyPI **`nanobot-ai`**): the upstream stays a lean, mergeable core in the **OpenClaw**-style lightweight line; this repo adds versioning, `pynanobot` packaging, and modules under **`pynanobot/ext/`** (reminders, lifecycle hooks, compactor, delegation, etc.). The product focus is bringing **agent / VibeCoding** patterns that work elsewhere (e.g. skills ecosystems, IDE-oriented workflows) into this stack, while **prioritizing small models and GGUF-friendly** setups via providers and docs—not rebuilding an inference engine here.

- **Install:** `pip install pynanobot` (pulls `nanobot-ai`).
- **Imports:** `import pynanobot` for the distribution layer; `nanobot` comes from the dependency.
- **Docs index:** [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md), [PYNANOBOT.md](PYNANOBOT.md), [docs/FORK_IN_EXT.md](docs/FORK_IN_EXT.md).

---

## 本仓库与 nanobot 的关系

**上游** [HKUDS/nanobot](https://github.com/HKUDS/nanobot)（PyPI **`nanobot-ai`**）是轻量、可合并的核心 Agent 运行时，常被放在 **OpenClaw** 一类的精简叙事里。**本仓库**不替代上游引擎，而是在其上叠加：**发行与版本**（`pynanobot`）、**扩展实现**（`pynanobot/ext`），并把 **Oh-my-OpenCode、Claude Code、VibeCoding** 等生态里可复用的产品与工程模式（skills 兼容、钩子与上下文策略等）**接入**这条线，同时把 **小模型 / GGUF / 本地推理** 作为一等目标写进文档与默认策略。若需要向他人类比「引擎 vs 发行层」，仍可参考 **llama.cpp 与 Ollama** 那种分工，但**主定位**见 [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)。

原则要点（详见 [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)）：

- **边界清楚**：上游以同步基线、可合并为主；本仓库独有逻辑放在约定命名空间（如 `pynanobot/ext`）。
- **可追踪**：发版与开发均应对应明确的上游 commit/tag（[upstream.lock](upstream.lock)、[docs/UPSTREAM.md](docs/UPSTREAM.md)）。
- **生态优先**：优先对接本地与 OpenAI-compatible 推理栈（如 Ollama、vLLM 等），而非在仓库内重复造「大模型引擎」。
- **扩展优先**：高级智能体与 VibeCoding 相关能力优先落在扩展层与文档约定，保持 `nanobot/` 可合并。

---

## 安装与入口

**从 PyPI 安装（推荐用户）**

```bash
pip install pynanobot
```

- 依赖会自动安装 **`nanobot-ai`**（提供 `nanobot` 包与 `nanobot` CLI）。
- 本仓库发行层通过 **`import pynanobot`** 使用；CLI 亦提供 **`pynanobot`** 入口（见 `pyproject.toml` 的 `[project.scripts]`）。

**从源码开发（维护者 / 贡献者）**

```bash
git clone https://github.com/chenhaodev/PyNanoBot.git
cd PyNanoBot
# 使用 uv 或 pip 按 pyproject.toml 安装可编辑环境，并跑通 tests/
```

具体可选依赖（API、渠道等）与上游对齐，见 [pyproject.toml](pyproject.toml) 的 `[project.optional-dependencies]`。

---

## 快速体验（与上游一致）

配置与日常使用与 **nanobot** 一致：初始化配置、选择模型、启动网关或 CLI 等。若你只使用上游 CLI，可直接参考 **`nanobot-ai`** / [上游文档](https://github.com/HKUDS/nanobot)。

典型流程示例：

```bash
nanobot onboard
# 编辑 ~/.nanobot/config.json 填入 API Key 与模型
nanobot agent
# 或 nanobot gateway，视渠道而定
```

PyNanoBot 在**默认产品路径**上使用 `PyNanoAgentLoop` / `PyNanoAgentRunner` 接入提醒与生命周期等扩展（见下文文档）；上游核心 `AgentLoop` / `AgentRunner` 保持精简，便于合并。

---

## 仓库里有什么

| 路径 | 含义 |
|------|------|
| **`nanobot/`** | 与上游同构的核心包，便于 `git` 与上游 diff/merge；PyPI 用户通过 **`nanobot-ai`** 获得该层。 |
| **`pynanobot/`** | 发行层：包名 **`pynanobot`**，对外 API 与 CLI；`pynanobot.agent` 等可转发/聚合上游与扩展。 |
| **`pynanobot/ext/`** | **本发行版专有实现**（提醒、生命周期钩子、compactor、delegation 等）；`nanobot/agent/` 下部分模块为兼容重导出，见 [docs/FORK_IN_EXT.md](docs/FORK_IN_EXT.md)。 |
| **`docs/`** | 哲学、上游同步、版本策略、路线图、阶段说明等。 |
| **`upstream.lock`** | 机器可读的上游基线，发版时与版本号一并维护。 |
| **`scripts/`** | 如 `check_upstream_lock.py`、`report_fork_diff.py` 等维护脚本。 |

更细的目录约定见 **[PYNANOBOT.md](PYNANOBOT.md)**。

---

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | 定位、扩展层与 OpenClaw 精简线、小模型/GGUF、原则 |
| [PYNANOBOT.md](PYNANOBOT.md) | 仓库目录与包边界 |
| [docs/UPSTREAM.md](docs/UPSTREAM.md) | 上游地址、同步流程 |
| [docs/VERSIONING.md](docs/VERSIONING.md) | 版本与基线策略 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 路线图 |
| [docs/FORK_IN_EXT.md](docs/FORK_IN_EXT.md) | `pynanobot/ext` 与兼容层 |
| [docs/EVOLUTION_MODEL_A.md](docs/EVOLUTION_MODEL_A.md) | 依赖上游 wheel、减少 fork 的演进 |
| [docs/PHASE3_NOTES.md](docs/PHASE3_NOTES.md) | 阶段 3：wheel / pip 与本地开发关系 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献说明 |

---

## 上游同步与版本

- 根目录 **[upstream.lock](upstream.lock)** 记录与 **`pyproject.toml`** 中版本的一致性；可运行：  
  `python scripts/check_upstream_lock.py`
- 若已配置 `git remote add upstream …`，可用 **`scripts/report_fork_diff.py`** 查看 `nanobot/` 相对上游的变更统计。

---

## 许可证与致谢

- 许可证以仓库 **[LICENSE](LICENSE)** 为准；衍生与上游文件请遵守各自文件头说明。
- 核心能力与设计理念来自 **[HKUDS/nanobot](https://github.com/HKUDS/nanobot)** 社区；PyNanoBot 在其上提供发行层与扩展，**不**替代上游作为「唯一上游」——欢迎同时关注上游发布与 Issue。

---

<div align="center">

**PyNanoBot** — 发行层与扩展，筑于 nanobot 之上。

</div>
