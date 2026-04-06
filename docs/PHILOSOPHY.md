# PyNanoBot 的定位与哲学

## 与上游的关系：扩展层，而不是第二套引擎

**上游** [nanobot](https://github.com/HKUDS/nanobot)（常被视作 **OpenClaw** 思路下的精简、可合并 Agent 运行时）提供轻量核心：通道、Provider、工具链与可研究的行为。**本仓库（PyNanoBot）** 在其上扮演 **发行与扩展层**：把 **Oh-my-OpenCode、Claude Code、VibeCoding** 等生态里可产品化的模式（skills 兼容、工作流钩子、上下文与委托等）**接到**这条精简线上，并**优先适配小模型与 GGUF/本地推理**（文档、预设、约束，而非在仓库内重写推理引擎）。

| 层级 | 角色 | 职责 |
|------|------|------|
| **上游 nanobot** | 可合并的核心 | 精炼 Agent 运行时、通道、Provider、工具链；追求与上游同步、diff 可控。 |
| **PyNanoBot** | 发行与扩展 | 版本与 `pynanobot` 命名空间、`pynanobot/ext` 专有逻辑、路线图与面向本地/中小模型的落地说明。 |

原则：

1. **不混淆边界**：上游合入以「同步基线」为主；本仓库特有功能放在清晰命名空间或 `docs/` 约定的扩展点，避免 silent fork。
2. **可追踪**：任意发行版都能说明「基于上游哪一 tag/commit」，见 `upstream.lock` 与 [UPSTREAM.md](./UPSTREAM.md)。
3. **本地与小模型优先**：在同等 API 抽象下，优先为 **小模型、量化、本地推理、资源受限环境** 优化默认与文档（路线图见 [ROADMAP.md](./ROADMAP.md)）。
4. **生态而非重写**：优先适配常见推理栈（**Ollama**、**llama.cpp** 系服务、**vLLM**、OpenAI-compatible 端点等），而不是在核心层重复实现推理引擎。

### 类比（可选）

若需要一句话向他人说明「引擎 vs 发行层」，仍可借用 **llama.cpp 与 Ollama** 那种「精炼引擎 + 其上打包与体验」的关系来类比——但 **PyNanoBot 的主叙事** 是上面的「扩展 + OpenClaw 精简线 + 小模型/GGUF」，不必把 Ollama 绑定为唯一本地路径。

## 本仓库额外承担的内容（示例）

- 上游同步策略、合并纪律与冲突处理（见 UPSTREAM.md）。
- 面向 GGUF / 本地小模型的配置范例与约束说明（路线图与后续文档）。
- 与 Cursor/IDE 协作的 `plans/` 设计稿与实现落点对照。

## 许可证与归属

上游与衍生代码均须遵守各自文件头与 `LICENSE`；对外说明时区分 **PyNanoBot 发行版** 与 **nanobot 上游** 的贡献者。

## 减少 fork 的落地路线

依赖上游 PyPI wheel、本仓库以 `pynanobot` 为主命名空间的演进步骤见 **[EVOLUTION_MODEL_A.md](./EVOLUTION_MODEL_A.md)**。
