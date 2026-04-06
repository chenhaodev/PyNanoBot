# 演进：模型 A（依赖上游 wheel，长期减少 fork）

目标：**PyPI 上的 `nanobot-ai` 作为唯一 `nanobot` 模块来源**，本仓库只维护 `pynanobot/` 发行层与扩展，不再长期携带整棵 `nanobot/` 源码。

## 为什么不能一步到位的技术原因

在同一虚拟环境里 **同时**：

- `pip install -e .`（本仓库仍打包 `nanobot/`），且  
- `pip install nanobot-ai`（同样提供顶层包 `nanobot`），

会令 pip 对 **同名顶层包** 产生冲突或不可预期的覆盖顺序。因此在 **删除本仓库 wheel 中的 `nanobot/` 之前**，不要把 `nanobot-ai` 写进 **默认** `dependencies`。

## 分阶段路线

### 阶段 1（已完成）

- **`pynanobot`** 包：`import pynanobot` / `import pynanobot.agent` 转发到 `nanobot`。
- **`pynanobot` CLI**（`pynanobot` 入口）调用 `nanobot.cli`。
- 版本锁检查：`python scripts/check_upstream_lock.py`。

### 阶段 2（进行中）

- **扩展目录**：`pynanobot/ext/` —— 新增 PyNanoBot 专有逻辑优先放此处，而非继续改 `nanobot/*`。
- **差异可见性**：配置 `upstream` 远程后运行 `python scripts/report_fork_diff.py` 查看 `nanobot/` 相对 `upstream/main` 的 diff 统计。
- 将 **仅 PyNanoBot 需要** 的存量逻辑从 `nanobot/*` **逐步** 迁到 `pynanobot/ext/*`，通过上游公开 API、插件点或极少量的薄封装接入。
- 能合并回上游的改动 → 向 [HKUDS/nanobot](https://github.com/HKUDS/nanobot) 提 PR，减少私有 diff。

### 阶段 3（发布形态切换）— 已落地

- **Wheel** 仅包含 **`pynanobot/`**；运行时 **`nanobot`** 来自 PyPI **`nanobot-ai`**（见 `pyproject.toml` 的 `dependencies`）。
- **PyPI 发行名**为 **`pynanobot`**（`pip install pynanobot`）；`nanobot` CLI 由 **`nanobot-ai`** 提供，`pynanobot` CLI 由本包提供。
- **Git 仓库**仍保留 **`nanobot/`** 源码供 fork 开发；本地运行测试时通常优先加载工作区内的 `nanobot/`（见 `docs/PHASE3_NOTES.md`）。
- CI：`check_upstream_lock` + `import pynanobot` / `pynanobot.agent` / `pynanobot.ext`。

## 维护者检查清单（阶段 3 发布前）

- [x] `nanobot/` 不再列入 **wheel** 的 `packages`（sdist 仍含完整源码）。
- [x] `dependencies` 含 `nanobot-ai`（版本范围见 `pyproject.toml`）。
- [x] `upstream.lock` 中 `pynanobot.version` 与 `pyproject` 一致；`python scripts/check_upstream_lock.py` 通过。
- [x] 文档：`README`、`docs/PHASE3_NOTES.md`、`docs/VERSIONING.md`。
- [ ] PyPI 首次发布 **`pynanobot`** 包（需维护者账号与 token）。

## 与 `docs/PHILOSOPHY.md` 的关系

模型 A 是 [PHILOSOPHY.md](./PHILOSOPHY.md) 里「上游核心 + PyNanoBot 发行与扩展」在 **Python 打包层** 的落地：上游 **`nanobot-ai`** wheel = 可合并的核心运行时；**`pynanobot`** = 发行与扩展命名空间（含 `pynanobot/ext`）。
