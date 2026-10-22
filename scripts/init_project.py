#!/usr/bin/env python3
"""按用户确认的选型生成最小 AI 产品项目骨架，不安装依赖或业务代码。"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

from scaffold_layout import KINDS, build_layout, join, needed


TEMPLATES = Path(__file__).resolve().parent.parent / "assets" / "templates"
COMMON_FILES = {
    "AGENTS.md": "AGENTS.md.tmpl",
    "CHANGELOG.md": "CHANGELOG.md.tmpl",
    "CONTRIBUTING.md": "CONTRIBUTING.md.tmpl",
    "README.md": "README.md.tmpl",
    ".env.example": "env.example.tmpl",
    ".gitignore": "gitignore.tmpl",
    "compose.yaml": "compose.yaml.tmpl",
    "docs/product/brief.md": "product.md.tmpl",
    "docs/architecture/overview.md": "architecture.md.tmpl",
    "docs/adr/0001-technology-stack.md": "adr.md.tmpl",
    "docs/development/sdd.md": "sdd-guide.md.tmpl",
    "docs/testing/strategy.md": "test-strategy.md.tmpl",
    "specs/_templates/spec.md": "spec.md.tmpl",
    "specs/_templates/plan.md": "plan.md.tmpl",
    "specs/_templates/tasks.md": "tasks.md.tmpl",
}


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", required=True, help="项目目录名称，例如 knowledge-assistant")
    p.add_argument("--target", type=Path, help="目标目录；默认在当前目录下创建与项目同名的文件夹")
    p.add_argument("--product-summary", required=True, help="用户确认的简短产品描述")
    p.add_argument("--frontend", required=True, help="已确认的前端技术，或填写 无")
    p.add_argument("--backend", required=True, help="已确认的后端技术，或填写 无")
    p.add_argument("--database", required=True, help="已确认的数据库，或填写 无")
    p.add_argument("--agent", required=True, help="已确认的 Agent 框架/Harness，或填写 无")
    p.add_argument("--layout", required=True, choices=KINDS, help="已确认的应用形态：多应用、单网页、API、Agent 或 CLI")
    p.add_argument("--agent-mode", choices=("embedded", "standalone"), default="embedded", help="默认内嵌；独立运行时显式选择 standalone")
    p.add_argument("--source-dir", default="src", help="各应用内部源码路径，如 src/my_app；默认 src")
    p.add_argument("--database-owner", choices=("web", "api", "agent", "cli"), help="数据库所属应用；默认主应用")
    p.add_argument("--migration-path", default="migrations", help="相对于数据库所属应用的迁移路径，按 ORM 约定指定")
    p.add_argument("--evals", action="store_true", help="有明确模型输出评估需求时才创建 evals 空目录")
    p.add_argument("--model-provider", default="待定", help="模型来源，与 Agent 方案分开记录")
    p.add_argument("--rationale", default="用户已确认以上技术选型；详细原因可在实现前补充。", help="选型理由")
    p.add_argument("--dry-run", action="store_true", help="只预览将创建的文件，不做任何写入")
    p.add_argument("--confirmed", action="store_true", help="仅在用户明确确认完整方案后才可设置")
    return p.parse_args()


def fill(template: str, choices: dict[str, str]) -> str:
    content = (TEMPLATES / template).read_text(encoding="utf-8")
    unresolved = set(re.findall(r"\{\{([A-Z_]+)\}\}", content)) - choices.keys()
    if unresolved:
        raise ValueError(f"模板有未替换变量：{template}: {sorted(unresolved)}")
    # 单次替换，保留用户文本中恰好与模板变量同名的字面内容。
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: choices[match[1]], content)


def is_empty_target(target: Path) -> bool:
    return not target.is_symlink() and (
        not target.exists() or (target.is_dir() and not any(target.iterdir()))
    )


def main() -> int:
    opts = arguments()
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", opts.name) or opts.name in {".", ".."}:
            raise ValueError("项目名称请使用字母、数字、短横线或下划线（最长 80 字符）")
        if not opts.product_summary.strip():
            raise ValueError("请先确认产品简介")
        choices = {
            "PROJECT_NAME": opts.name,
            "COMPOSE_PROJECT_NAME": re.sub(r"[^a-z0-9_-]", "-", opts.name.lower()),
            "PRODUCT_SUMMARY": opts.product_summary.strip(),
            "FRONTEND": opts.frontend.strip(),
            "BACKEND": opts.backend.strip(),
            "DATABASE": opts.database.strip(),
            "AGENT": opts.agent.strip(),
            "MODEL_PROVIDER": opts.model_provider.strip() or "待定",
            "RATIONALE": opts.rationale.strip(),
            "DATE": date.today().isoformat(),
        }
        for key in ("FRONTEND", "BACKEND", "DATABASE", "AGENT"):
            if not choices[key]:
                raise ValueError(f"技术方案 {key} 不能为空；不需要时明确填写 无")
        target = (opts.target or Path.cwd() / opts.name).expanduser().absolute()
        if not is_empty_target(target):
            raise ValueError("目标目录已存在内容或为符号链接，禁止覆盖")
        stack = {key.lower(): choices[key] for key in ("FRONTEND", "BACKEND", "DATABASE", "AGENT", "MODEL_PROVIDER")}
        layout = build_layout(stack, kind=opts.layout, agent_mode=opts.agent_mode,
                              source_dir=opts.source_dir, database_owner=opts.database_owner,
                              migration_path=opts.migration_path, evals=opts.evals)
        agent_label = {"none": "不使用", "embedded": "内嵌模块", "standalone": "独立应用"}[layout["agent_runtime"]]
        choices["LAYOUT_SUMMARY"] = "\n".join([
            f"- 应用形态：`{layout['kind']}`。",
            *[f"- {app} 应用目录：`{path}`；源码：`{join(path, layout['source_dir'])}`。"
              for app, path in layout["applications"].items()],
            f"- Agent：`{layout['agent_path'] or '无'}`（{agent_label}）。",
            f"- 数据库归属：`{layout['database_owner'] or '无'}`；迁移目录：`{layout['database_path'] or '无'}`。",
        ])
        choices["TEST_PATHS"] = "\n".join(f"- `{path}`" for path in layout["test_paths"])
        choices["EVAL_PATH"] = layout["eval_path"] or "未创建；有明确质量目标后再按需建立"
        files = {path: fill(src, choices) for path, src in COMMON_FILES.items()}
        if needed(opts.backend):
            files["docs/api/contracts.md"] = fill("api-contracts.md.tmpl", choices)
        if needed(opts.database):
            files["docs/database/data-model.md"] = fill("data-model.md.tmpl", choices)
        files.update({path + "/.gitkeep": "" for path in layout["directories"]})
        config = {
            "project_name": opts.name,
            "product_summary": choices["PRODUCT_SUMMARY"],
            "status": "仅目录与必要文件，尚无应用实现",
            "source": "用户明确确认的技术方案",
            "user_confirmed": bool(opts.confirmed),
            "stack": stack,
            "layout": layout,
            "project_policy": {
                "spec_driven": "lightweight_custom",
                "simple_change_docs_optional": True,
                "new_feature_spec_required": True,
                "major_refactor_spec_required": True,
                "complex_plan_required": True,
                "tasks_doc_only_when_needed": True,
                "git_commit_convention": "conventional_commits",
                "docker_placeholder_only": True,
                "unit_integration_e2e_required_when_implemented": True,
                "ci": False,
                "cd": False,
            },
        }
        files["project.config.json"] = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        print(f"目标目录：{target}")
        print("将创建以下最小文件：")
        for relative in sorted(files):
            print("  + " + relative)
        if opts.dry_run:
            print("预览结束：未创建任何文件。")
            return 0
        if not opts.confirmed:
            raise ValueError("尚未取得用户明确确认：先展示技术方案，确认后才可使用 --confirmed")
        target.mkdir(parents=True, exist_ok=True)
        for relative, content in files.items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(content)
        print("创建完成：项目骨架及开发规范已生成；未安装依赖、未编写业务代码。")
        return 0
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
