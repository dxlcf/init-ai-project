# 确认后的最小项目骨架

## 基本规则

- 创建设计文档、空目录、配置占位和开发规范；不安装依赖、运行框架生成器、编写业务代码/测试实现或配置 CI/CD。
- 用户确认的设计优先；先预览，后写入，不覆盖非空目录或现有文件。既有项目的增量改造不属于本技能范围。
- 文档使用简体中文。将已确认的用户、场景、范围、架构及接口/数据设计填入对应文档；只有缺失部分保留“待确认”。选型确认不代表运行验证完成，不猜测安装/启动命令。
- 脚本生成的是底稿，随后按 [设计文档撰写与验收](design-workflow.md#文档撰写与验收) 补全本轮新建文档；禁止覆盖既有文件的限制不阻止这一步必要编辑。

## 结构选择

先确定运行边界，再选择 `--layout`，不能仅凭技术名称或组件数量决定目录：

| 形态 | 参数 | 适用边界 | 代码位置 |
| --- | --- | --- | --- |
| 多应用 | `split` | 至少两个独立应用，如前端＋API、前端＋独立 Agent | `apps/web/`、`apps/api/`、按需 `apps/agent/` |
| 单个网页/全栈应用 | `web` | 前端与服务端能力由同一应用承载 | 项目根目录，内部遵循框架约定 |
| 纯 API | `api` | 无前端，独立后端应用 | 项目根目录 |
| 独立 Agent | `agent` | Agent 本身就是运行应用 | 项目根目录 |
| 命令行工具 | `cli` | 无独立前后端；可内嵌 Agent | 项目根目录 |

`web` 中的 `--backend` 只记录同一应用的服务端能力；若需另起 FastAPI 等独立后端，使用 `split`。纯前端也可选择 `web`，不需要的组件填 `无`。`api` 需要后端；`agent` 需要 Agent；`agent/cli` 不包含独立前后端。

### 目录归属

- **源码**：默认各应用 `src/`；`--source-dir` 可改为 `src/my_app` 等框架/语言约定路径。该参数作用于所有应用；若各应用需要不同的非默认源码路径，按自定义结构处理。
- **Agent**：默认内嵌在主应用源码下的 `agents/`，提示词、工具和工作流随模块维护。主应用优先为 API，其次为 web。只有明确独立依赖环境、权限隔离或部署/扩缩容需求时，选择 `--agent-mode standalone`；多应用新增 `apps/agent/`，独立 Agent 项目直接使用根目录源码。
- **数据库**：迁移归属使用它的应用。默认主应用拥有，可用 `--database-owner` 指定；`--migration-path` 相对于该应用，如 `alembic/versions`、`prisma/migrations` 或 `src/lib/db/migrations`。不默认创建根目录 `database/` 或重复的 schema 定义，模型位置由 ORM 决定。
- **测试**：各应用分别有 `tests/unit/`、`tests/integration/`；根目录 `tests/e2e/` 验证完整用户路径，单应用时这些目录自然合并在根目录。需要跨应用集成测试时再创建根目录 `tests/integration/`。
- **评估**：明确需要模型输出质量评估时才加 `--evals`，在 Agent 所属应用（无 Agent 则主应用）下创建 `evals/`。不生成样例或运行模型。
- **共享与部署**：不因组件数量创建 `packages/shared/`。有实际复用需求后建立具名包，如 `contracts/`、`api-client/`、`ui/`；跨语言优先共享契约。根目录保留 Compose 占位，额外部署文件出现后再建 `infra/`；各应用 Dockerfile 在实现阶段补齐。

### 多应用示例

以下示例选择前端、API、内嵌 Agent 和数据库；仅表示空目录，不包含实现：

```text
项目/
├── apps/
│   ├── web/
│   │   ├── src/
│   │   ├── public/
│   │   └── tests/{unit,integration}/
│   └── api/
│       ├── src/agents/
│       ├── migrations/              # 可按 ORM 更改
│       └── tests/{unit,integration}/
├── tests/e2e/
├── docs/                            # 所有形态共用下列文档
├── specs/_templates/{spec,plan,tasks}.md
└── compose.yaml                     # services 为空，不可启动
```

单应用省去 `apps/<名称>/` 包装层；不自动生成多应用工程依赖配置。实现阶段再细分路由、组件、业务模块和 ORM 模型。

## 必要文档与配置

所有形态保留以下交付物；`.gitkeep` 仅用于追踪空目录：

| 文件 | 职责 |
| --- | --- |
| `AGENTS.md` | 代理开发规则、实际结构导航，引用专项规范 |
| `README.md` | 产品、已确认选型、结构及当前状态；实现后补已验证命令 |
| `CONTRIBUTING.md` | Git 提交格式、提交前检查与协作规则；不自动初始化 Git |
| `CHANGELOG.md` | 初始只有 `[Unreleased]`；实际发布才记录版本和日期 |
| `.env.example`、`.gitignore` | 无密钥的配置示意与忽略规则 |
| `project.config.json` | 选型、确认标记和 `layout` 中的应用/Agent/数据库/测试路径 |
| `compose.yaml` | 明确不可启动的 Docker 配置占位 |
| `docs/product/brief.md` | 已确认产品需求与待明确事项 |
| `docs/architecture/overview.md` | 应用边界与数据流，保留已确认设计 |
| `docs/adr/0001-technology-stack.md` | 选型、理由、取舍和状态；后续用新 ADR 保留替代历史 |
| `docs/development/sdd.md` | 轻量 SDD：简单局部改动免文档，新增功能/较大重构写规格，复杂任务加计划 |
| `docs/testing/strategy.md` | 本次实际测试路径、后续测试和按需质量评估约定 |
| `specs/_templates/{spec,plan,tasks}.md` | 未来复制使用，不代表现在开启开发任务 |

选择后端时另生成 `docs/api/contracts.md`；选择数据库时生成 `docs/database/data-model.md`。已有设计直接填入，未明确时仅保留记录方式，不虚构接口、表或架构比较。

## 生成与验证

脚本路径相对于技能目录，从其他工作目录执行时使用绝对路径；选择当前环境可用的 Python 3 解释器。将示例技术和路径替换为已确认值：

```bash
python scripts/init_project.py --name knowledge-assistant --layout split --frontend Next.js --backend FastAPI --database PostgreSQL --agent LangGraph --product-summary '为团队提供文档问答功能' --dry-run
```

- `--target` 指定目标目录；省略则在当前工作目录创建与 `--name` 同名的目录。
- `--model-provider` 默认“待定”；`--rationale` 记录已确认的选型原因。
- 结构参数默认值也是方案的一部分，应在确认前展示实际路径。需要时通过 `--agent-mode`、`--database-owner`、`--source-dir`、`--migration-path` 和 `--evals` 细化，不猜测独立部署需求。
- 预览与已确认方案一致后，将 `--dry-run` 替换为 `--confirmed`，其余参数不变。参数只记录已有授权，不能代替确认。
- 执行 `python scripts/validate_project.py <目标目录>`，校验必要文件、配置、实际布局和部分规范；它不能证明实际用户授权、应用可运行或文档语义正确，仍须检查交付清单及内容。

脚本不迁移旧版生成目录。超出支持范围的自定义结构，以 `assets/templates/` 为输入在目标项目生成文件并更新引用，不修改技能自身模板；按已确认设计人工核对并报告验证方式，不强套自动校验器的路径规则。
