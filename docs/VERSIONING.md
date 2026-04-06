# 版本策略

## PyNanoBot 发行版（本仓库）

- 采用 **语义化版本** `MAJOR.MINOR.PATCH[.postN]`，与 `pyproject.toml` 中 `[project].version` **保持一致**。
- **MAJOR**：不兼容的对外行为或配置；或与上游对齐策略发生重大变化。
- **MINOR**：新功能、新扩展点、向后兼容的配置项。
- **PATCH**：修复与文档。
- **post**：可选，用于同一逻辑版本上的文档/元数据/打包修正（与上游 PyPI 习惯可并存）。

## PyPI 包名

- 发行包名为 **`pynanobot`**（`pip install pynanobot`）。
- 核心 **`nanobot`** 模块由依赖 **`nanobot-ai`** 提供，勿与上游 PyPI 包名混淆。

## 上游基线版本

- **不作为** PyNanoBot 的 `version` 数字的一部分混写，而是单独记录在 **`upstream.lock`**：
  - `upstream.baseline_tag`（可选）
  - `upstream.baseline_commit`（推荐必填）
- 发版检查清单：
  - [ ] `pyproject.toml` → `version` 已更新
  - [ ] `upstream.lock` → `pynanobot.version` 与 `upstream.baseline_commit` 已更新
  - [ ] `git tag` 与 Release 说明包含两端信息

## 与上游版本号并存

可能出现：**上游** 为 `v0.1.4.post6`，**PyNanoBot** 为 `0.2.0`（示例），只要 Release 说明写清「基于上游 commit/tag」即可。不要在用户可见路径里把两个项目的版本号合成一个字符串，除非有明确文档定义。
