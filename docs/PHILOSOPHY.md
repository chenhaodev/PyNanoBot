# PyNanoBot 的定位与哲学

## 与上游的关系：类比 Ollama 与 llama.cpp

| 角色 | 类比 | 职责 |
|------|------|------|
| **llama.cpp** | 上游 **[nanobot](https://github.com/HKUDS/nanobot)** | 精炼、可复用的核心引擎：轻量 Agent 运行时、通道、Provider、工具链。追求代码少、行为清晰、可研究。 |
| **Ollama** | **PyNanoBot（本仓库）** | 在**明确基线版本**的上游之上，搭建更易用的发行层：版本管理、本地与中小模型、GGUF/端侧路径、预设与模板、与本仓库一致的路线图。 |

原则：

1. **不混淆边界**：上游合入以「同步基线」为主；本仓库特有功能放在清晰命名空间或 `docs/` 约定的扩展点，避免 silent fork。
2. **可追踪**：任意发行版都能说明「基于上游哪一 tag/commit」，见 `upstream.lock` 与 [UPSTREAM.md](./UPSTREAM.md)。
3. **本地优先友好**：在同等 API 抽象下，优先为 **小模型、量化、本地推理、资源受限环境** 优化默认与文档（路线图见 [ROADMAP.md](./ROADMAP.md)）。
4. **生态而非重写**：优先适配（Ollama、llama.cpp、vLLM、OpenAI-compatible 端点等），而不是在核心层重复实现推理引擎。

## 本仓库额外承担的内容（示例）

- 上游同步策略、合并纪律与冲突处理（见 UPSTREAM.md）。
- 面向 GGUF / 本地小模型的配置范例与约束说明（路线图与后续文档）。
- 与 Cursor/IDE 协作的 `plans/` 设计稿与实现落点对照。

## 许可证与归属

上游与衍生代码均须遵守各自文件头与 `LICENSE`；对外说明时区分 **PyNanoBot 发行版** 与 **nanobot 上游** 的贡献者。

## 减少 fork 的落地路线

依赖上游 PyPI wheel、本仓库以 `pynanobot` 为主命名空间的演进步骤见 **[EVOLUTION_MODEL_A.md](./EVOLUTION_MODEL_A.md)**。
