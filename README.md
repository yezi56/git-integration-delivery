# Git Integration Delivery

一个用于 Codex 的 Git 交付 Skill。它将功能开发与长期集成分支分开，使受保护的环境分支只接收已经核对、验证过的集成变更。

```text
feature -> integration/dev  -> dev
feature -> integration/test -> test
```

## 解决什么问题

- 防止功能分支直接合并到 `dev` 或 `test`。
- 在本地独立 worktree 中解决交付冲突，保留功能工作区不受影响。
- 将功能分支推送、集成分支推送、创建 MR、合并 MR 视为独立授权动作。
- 在创建或更新 GitLab MR 后回读 Markdown 描述，避免把 `\\n` 原样展示为乱码。

## 安装

使用 Codex 自带的安装器：

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo yezi56/git-integration-delivery \
  --path git-integration-delivery
```

或者手动克隆后复制 Skill 目录：

```bash
git clone git@github.com:yezi56/git-integration-delivery.git
cp -R git-integration-delivery/git-integration-delivery ~/.codex/skills/
```

重新开始一个 Codex 会话后，Skill 会被发现。

## 使用

在请求中明确调用：

```text
使用 $git-integration-delivery 将当前功能分支交付到 test。
```

Skill 会先检查功能分支、工作区、远端引用、已有 MR 和项目的聚焦验证命令。随后在 `integration/test` 或 `integration/dev` 的独立 worktree 中同步环境基线、合入功能分支、检查 diff 并运行验证。

只有在当前请求明确授权时，Skill 才会执行相应的远端动作：

| 动作 | 需要单独授权 |
| --- | --- |
| 推送功能分支 | 是 |
| 推送 `integration/test` 或 `integration/dev` | 是 |
| 创建或更新 MR | 是 |
| 合并 MR 到 `test` 或 `dev` | 是 |

## 交付检查点

1. 功能工作区干净，目标为功能分支而不是环境分支。
2. `integration/<environment>` 存在，且先与远端和对应环境基线同步。
3. 功能分支通过显式 merge commit 合入 integration worktree；冲突只在该 worktree 解决。
4. 对比 `origin/<environment>...HEAD`，检查提交、预期 diff、空白错误与聚焦测试。
5. 推送后，MR 必须回读并确认源分支、目标分支、标题、开放状态和描述格式。

## MR 描述格式

MR 描述需要是真实 Markdown，而不是把 `\\n` 拼入单行 shell 参数。Skill 用带真实换行的变量传给 `glab`，并在写入后回读 `description`。验收条件是标题、列表、空行与命令文本完整，且没有可见的 `\\n` 字面量。

## 仓库结构

```text
.
├── README.md
├── LICENSE
├── .gitignore
└── git-integration-delivery/
    ├── SKILL.md
    └── agents/openai.yaml
```

根目录文件服务于 GitHub 使用者；真正安装到 Codex 的目录是 `git-integration-delivery/`。

## 许可

[MIT](LICENSE)
