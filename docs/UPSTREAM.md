# 上游 nanobot 同步说明

## 上游仓库

- **默认上游**：<https://github.com/HKUDS/nanobot>
- **本仓库（发行版）**：以 `upstream.lock` 中记录的 **基线提交或标签** 为合并起点。

## 机器可读基线

仓库根目录的 **`upstream.lock`**（YAML）为单一事实来源，建议包含：

- `upstream.repo`：上游 Git URL
- `upstream.baseline_tag`：可选，上游发布标签（如 `v0.1.4.post6`）
- `upstream.baseline_commit`：必填，**完整 40 位或当前采用的短 SHA**，表示最后一次「对齐上游」所基于的提交
- `pynanobot.version`：本发行版语义化版本（与 `pyproject.toml` 的 `version` 一致）

发布或打 tag 前请更新 `upstream.baseline_*`，便于排查「与上游差异」。

## 推荐工作流（git）

1. 添加上游远程（一次性）：
   ```bash
   git remote add upstream https://github.com/HKUDS/nanobot.git
   git fetch upstream
   ```
2. 从上游拉取基线分支（通常为 `main`）：
   ```bash
   git fetch upstream main
   ```
3. 在本分支合并或 rebase：
   - **合并**：`git merge upstream/main`（保留历史清晰时可用）
   - **变基**：`git rebase upstream/main`（线性历史，需处理冲突）
4. 解决冲突后跑测试：`pytest`（或 CI 等价命令）。
5. 更新 `upstream.lock` 中的 `baseline_commit`（以及 `baseline_tag` 若存在）。
6. 在 CHANGELOG 或 Release 说明中写明：**上游基线** + **本发行版特有变更**。

## 合并策略建议

| 场景 | 建议 |
|------|------|
| 上游小版本修复 | 优先合并上游，再在本分支上验证本地/小模型相关配置。 |
| 本仓库独有大功能 | 保持模块边界；大段复制上游文件时加注释标明来源 commit。 |
| 上游 API 破坏性变更 | 在 [VERSIONING.md](./VERSIONING.md) 记一笔；必要时提供迁移小节。 |

## 与 PyPI `nanobot-ai` 的关系

上游发布的包名可能仍为 `nanobot-ai`。本仓库若单独发版，应在 Release 页写清：**包名、版本、对应上游 commit**，避免用户混淆「官方 nanobot」与「PyNanoBot 发行版」。
