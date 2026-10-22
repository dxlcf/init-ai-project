# init-ai-project

通过与大模型多轮交流，理清一个新 AI 应用的产品需求、用户流程、AI 行为和技术设计，并在确认后生成设计文档、项目骨架及开发规范。

适合已有产品想法、希望在编码前梳理方案的开发者，也适合需要选型解释和设计引导的技术初学者。

## 能做什么

- 梳理首版目标、核心用户路径、范围及验收标准。
- 讨论模型与普通代码的分工，以及按需检索、工具调用、状态管理和人工确认。
- 整理数据、权限、应用边界与数据流，推荐并解释技术方案。
- 确认后创建项目骨架，将讨论结论写入对应设计文档。
- 配套轻量规格驱动开发（SDD）、Git 协作和测试约定。

交付到设计与初始化阶段为止：不安装应用依赖、不实现业务代码或测试、不启动容器、不配置 CI/CD。用户确认前不写入项目文件；目标位置已有内容时不会直接覆盖。

## 安装到 Codex

需要支持本地 Skills 的 Codex 环境。初始化脚本使用 Python 3.10 或更新版本，脚本本身仅依赖 Python 标准库。通过 Git 安装时还需安装 Git。

仓库地址：[dxlcf/init-ai-project](https://github.com/dxlcf/init-ai-project)。

### 方式一：使用 skill-installer

在 Codex 中发送下面的提示词，将仓库地址换成实际地址：

```text
使用 $skill-installer 从 GitHub 仓库 dxlcf/init-ai-project 安装 skill。
skill 位于仓库根目录（--path .），请显式命名为 init-ai-project（--name init-ai-project）。
```

根目录安装时显式指定名称，避免安装器把 `.` 当成 skill 名称。安装器决定目标安装目录；不要再通过其他方式重复安装同名 skill。

### 方式二：通过 Git 安装到用户目录

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path "$HOME/.agents/skills" | Out-Null
git clone https://github.com/dxlcf/init-ai-project.git "$HOME/.agents/skills/init-ai-project"
```

macOS / Linux：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/dxlcf/init-ai-project.git "$HOME/.agents/skills/init-ai-project"
```

如果目标目录已存在，先检查是否已经安装，避免重复克隆。也可以下载仓库 ZIP，解压后将整个 skill 文件夹放到相同位置，保证目录结构为：

```text
~/.agents/skills/init-ai-project/
├── SKILL.md
├── agents/
├── references/
├── assets/
└── scripts/
```

应复制整个文件夹，脚本依赖其中的模板与辅助模块，不能只复制 `SKILL.md`。

安装完成后在新一轮对话中使用；若尚未出现在技能列表，重启 Codex。用户级目录、显式调用和安装器的说明参见 [OpenAI Skills 官方文档](https://learn.chatgpt.com/docs/build-skills)。当前项目是可直接安装的独立 skill，未提供插件目录安装包。

## 使用示例

在希望创建新项目的父目录打开 Codex，显式调用：

```text
$init-ai-project

我想做一个给小团队使用的知识库问答应用，用户可以上传文档并通过对话查询。
我希望先本地运行，目前还没有确定技术栈。
请通过多轮讨论帮我理清首版设计，确认后再生成设计文档和项目骨架。
```

如果已有需求或技术方案，可以直接提供材料，并说明目标目录。skill 会沿用已确认内容，围绕影响设计的缺口继续讨论。

典型过程：

1. 分轮梳理需求、用户流程、AI 行为、数据与运行约束。
2. 汇总设计、选型、实际目录和未决项，等待生成授权。
3. 先预览文件清单，再生成骨架并补全文档。
4. 检查文档内容与结构，报告未决项和后续验证需求。

本 skill 设置为**仅手动调用**，需要使用 `$init-ai-project` 明确触发。允许在用户知情并授权的情况下保留未知项、交付设计初稿；不会把推测写成已确认需求。

## 会生成哪些文档

| 文档 | 内容 |
| --- | --- |
| `docs/product/brief.md` | 用户与目标、首版范围、关键流程、成功标准、假设与未决项 |
| `docs/architecture/overview.md` | 应用和模块职责、数据流、AI 执行边界、权限与运行约束 |
| `docs/adr/0001-technology-stack.md` | 技术选择、理由、真实讨论过的替代方案和风险 |
| `docs/api/contracts.md` | 有后端时生成，记录已确定的接口与交互契约 |
| `docs/database/data-model.md` | 有数据库时生成，记录实体关系、关键字段与数据生命周期 |
| `docs/testing/strategy.md` | 产品验收路径、测试分层和按需模型质量评估 |
| `docs/development/sdd.md` | 后续功能规格、计划、实施及文档同步规则 |
| `specs/_templates/{spec,plan,tasks}.md` | 供未来开发任务复制使用的模板 |

另外生成 `README.md`、`AGENTS.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、配置示意和目录占位。支持多应用、单网页/全栈应用、纯 API、独立 Agent 和命令行工具等形态；最终结构按已确认的运行边界确定。

脚本负责生成文档底稿，模型随后依据对话补全设计。单独运行初始化脚本不会自动得到完整的产品设计文档。

## 更新

通过 Git 安装且没有本地修改时，可以在安装目录执行：

```bash
git pull --ff-only
```

ZIP 或安装器安装的版本应使用相应方式更新，先保留自己的修改。Codex 通常会自动检测 skill 变化；若未生效，重启 Codex。

## 项目结构与开发

```text
init-ai-project/
├── SKILL.md                 # skill 入口与阶段流程
├── agents/openai.yaml       # 展示信息及手动调用策略
├── references/              # 设计对话、选型、骨架和文档规则
├── assets/templates/        # 目标项目文档与配置模板
├── scripts/                 # 骨架生成、布局、校验与测试
└── README.md                # 安装与使用说明
```

在仓库根目录运行现有测试：

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

macOS / Linux 若没有 `python` 命令，使用 `python3`。这些测试检查骨架生成和规则约束，不能证明多轮设计对话或生成文档的语义质量。

反馈问题或提交改进时，请提供复现提示、预期行为和实际结果；提交示例前移除真实密钥与个人数据。

## 许可证

当前尚未添加 `LICENSE`。发布者应在发布前选择并添加许可证，具体授权以仓库中的许可证文件为准。
