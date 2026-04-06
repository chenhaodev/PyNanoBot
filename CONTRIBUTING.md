# 参与贡献（PyNanoBot）

## 与上游 nanobot 的关系

请先阅读 [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) 与 [docs/UPSTREAM.md](docs/UPSTREAM.md)。本仓库的变更应尽量：

- 可合并回上游的改进 → 考虑同时向上游提 PR，或先在本分支保持与上游 diff 最小化。
- 仅发行版需要的逻辑 → 明确文档与命名空间，避免污染 `nanobot/` 核心语义。

## 发版前检查

- `pyproject.toml` 中 `version` 与 `upstream.lock` 中 `pynanobot.version` 一致：  
  `python scripts/check_upstream_lock.py`
- 若已合并上游新提交：更新 `upstream.baseline_commit`（及 `baseline_tag` 如有）。

## 模型 A（减少 fork）

- **新功能** 优先落在 **`pynanobot/ext/`**，避免继续增大 `nanobot/` 与上游的 diff。
- 配置 `git remote upstream` 后可用 **`python scripts/report_fork_diff.py`** 查看 `nanobot/` 相对上游的变更统计。详见 `docs/EVOLUTION_MODEL_A.md`。

## 安装与开发依赖

```bash
pip install -e ".[dev]"
```

（`pynanobot` 会拉取 `nanobot-ai`；在仓库根目录跑测试时通常仍使用工作区内的 `nanobot/` 源码。）

## 测试

```bash
pytest
```

（环境原因导致个别与 Git 相关的测试失败时，以 CI/本地说明为准。）
