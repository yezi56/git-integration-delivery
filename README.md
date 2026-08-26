# FarmLynk Git Integration Delivery

一个用于 Codex 的 FarmLynk Git 交付 Skill。它将功能开发、环境集成、release、生产标签与 `main` 回灌分开，并在每一步保留明确的授权和验证边界。

```text
feature/fix -> integration/dev  -> dev
feature/fix -> integration/test -> test
approved feature/fix -> rX.Y.Z -> tag vX.Y.Z-N -> deployment-repository MR -> production
rX.Y.Z -> main
```

`dev`、`test` 与 release 彼此独立：不能把整条环境分支提升到 production 或 `main`。

## 解决什么问题

- 功能分支允许积累多次连贯提交和 push；默认在形成可独立验证的小批次后，才合入一次 integration，不让 integration 跟随每次中间 push。
- 防止功能分支直接合并到 `dev`、`test` 或 `main`；`integration/dev`、`integration/test` 也不能相互合并。
- 在本地独立 worktree 中解决交付冲突，保留功能工作区不受影响。
- 将提交、功能分支推送、integration 推送、MR 创建、MR 合并、release 标签和部署视为独立授权动作。
- 用精确的 Git SHA、MR、流水线、部署和运行态证据区分“代码已合入”与“生产已完成”。

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
使用 $git-integration-delivery 将当前功能分支按流程交付到 dev 和 test。
```

Skill 会先核对分支、工作区、远端引用、已有 MR、待交付批次 SHA，以及项目自己的聚焦验证命令。准备环境交付时，它会在相应 integration worktree 中同步环境基线、合并该批次、检查 diff 并运行验证。

只有在当前请求明确授权时，Skill 才会执行相应的远端动作：

| 动作 | 需要单独授权 |
| --- | --- |
| 提交或推送功能分支 | 是 |
| 推送 `integration/test` 或 `integration/dev` | 是 |
| 创建或更新 MR | 是 |
| 创建 release 或推送生产标签 | 是 |
| 合并 MR 或部署 | 是 |

## 交付检查点

1. 确认本次是完整、可独立验证的功能分支批次；中间 push 默认仍留在功能分支。
2. `integration/<environment>` 存在，且先与远端和对应环境基线同步。
3. 功能分支通过显式 merge commit 合入 integration worktree；冲突只在该 worktree 解决。
4. 对比 `origin/<environment>...HEAD`，检查提交、预期 diff、空白错误与聚焦测试；有迁移时执行迁移门禁。
5. 推送后，MR 必须回读并确认源分支、目标分支、标题、开放状态和描述格式。
6. 生产标签必须指向确认的 release SHA；流水线成功、部署 MR 合并、预期镜像运行、Pod Ready、迁移和关键验收都完成后，才能称为生产完成。

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
