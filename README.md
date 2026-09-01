# FarmLynk Git Integration Delivery

一个用于 Codex 的 FarmLynk Git 交付 Skill。它将功能开发、环境集成、release、生产标签与 `main` 回灌分开，并在每一步保留明确的授权和验证边界。

```text
feat/<requirement-id> -> integration/dev  -> dev
feat/<requirement-id> -> integration/test -> test
approved source branch -> rX.Y.Z -> tag vX.Y.Z-N -> deployment-repository MR -> production
rX.Y.Z -> main
```

`dev`、`test` 与 release 彼此独立：不能把整条环境分支提升到 production 或 `main`。

## 解决什么问题

- 功能分支允许积累多次连贯提交和 push；默认在形成可独立验证的小批次后，才合入一次 integration，不让 integration 跟随每次中间 push。
- 日常需求分支统一使用 `feat/<需求ID>`，例如 `feat/7048051759` 或 `feat/vv1002`；直接使用需求 ID，不追加英文标题或描述。
- 防止功能分支直接合并到 `dev`、`test` 或 `main`；`integration/dev`、`integration/test` 也不能相互合并。
- 在本地独立 worktree 中保留冲突现场，分析业务、契约、迁移和部署影响，返回审阅并等待使用者处理。
- 每次 commit 前审阅完整拟提交 diff，按严重度报告高风险；`Critical` 或 `High` 发现必须返回使用者处理。
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
使用 $git-integration-delivery 将当前 feat/7048051759 按流程交付到 dev 和 test。
```

Skill 会先核对分支、工作区、远端引用、已有 MR、待交付批次 SHA，以及项目自己的聚焦验证命令。准备环境交付时，它会在相应 integration worktree 中同步环境基线，并用 `--no-commit` 准备合并结果，确保 commit 前可以审阅完整 diff。

只有在当前请求明确授权时，Skill 才会执行相应的远端动作：

| 动作 | 需要单独授权 |
| --- | --- |
| 提交或推送功能分支 | 是 |
| 推送 `integration/test` 或 `integration/dev` | 是 |
| 创建或更新 MR | 是 |
| 创建 release 或推送生产标签 | 是 |
| 合并 MR 或部署 | 是 |

## 交付检查点

1. 确认当前来源分支符合 `feat/<需求ID>`，并且本次是完整、可独立验证的批次；中间 push 默认仍留在来源分支。
2. `integration/<environment>` 存在，且先在独立 worktree 中与远端和对应环境基线同步；基线分叉时先完成一次独立的审阅与 merge commit，再开始功能合并。
3. 合并出现冲突时保留现场，只读分析各方意图、业务与下游影响、解决选项和验证要求，返回使用者审阅并等待处理。
4. 每个普通或 merge commit 前检查完整 staged diff、未纳入改动、契约兼容性和高风险面，并在干净 worktree 或隔离快照中验证精确 staged 版本；`Critical` 或 `High` 发现阻断提交，没有阻断项时仍需当前请求已明确授权提交。
5. commit 后对比 `origin/<environment>...HEAD`，检查提交、预期 diff、空白错误与聚焦测试；有迁移时执行迁移门禁。
6. 推送后，MR 必须回读并确认源分支、目标分支、标题、开放状态和描述格式。
7. 生产标签必须指向确认的 release SHA；流水线成功、部署 MR 合并、预期镜像运行、Pod Ready、迁移和关键验收都完成后，才能称为生产完成。

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
    ├── agents/openai.yaml
    └── references/conflict-and-pre-commit-review.md
```

根目录文件服务于 GitHub 使用者；真正安装到 Codex 的目录是 `git-integration-delivery/`。

## 许可

[MIT](LICENSE)
