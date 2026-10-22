#!/usr/bin/env python3
"""验证由本技能生成的最小项目骨架。"""

import json
from pathlib import Path
import sys

from scaffold_layout import build_layout, needed


REQUIRED = (
    "AGENTS.md", "CHANGELOG.md", "CONTRIBUTING.md", "README.md", ".env.example", ".gitignore",
    "project.config.json", "compose.yaml", "docs/product/brief.md",
    "docs/architecture/overview.md", "docs/adr/0001-technology-stack.md",
    "docs/development/sdd.md",
    "docs/testing/strategy.md", "specs/_templates/spec.md",
    "specs/_templates/plan.md", "specs/_templates/tasks.md",
)


def validate(root: Path) -> list[str]:
    issues = ["缺少：" + item for item in REQUIRED if not (root / item).is_file()]
    if issues:
        return issues
    try:
        config = json.loads((root / "project.config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"配置文件错误：{exc}"]
    if not isinstance(config, dict):
        return ["配置文件错误：顶层必须为 JSON 对象"]
    if config.get("user_confirmed") is not True:
        issues.append("没有记录用户确认")
    policy = config.get("project_policy", {})
    if not isinstance(policy, dict):
        return issues + ["配置文件错误：project_policy 必须为对象"]
    expected_policy = {
        "spec_driven": "lightweight_custom",
        "simple_change_docs_optional": True,
        "new_feature_spec_required": True,
        "major_refactor_spec_required": True,
        "complex_plan_required": True,
        "git_commit_convention": "conventional_commits",
    }
    for key, expected in expected_policy.items():
        if policy.get(key) != expected:
            issues.append(f"开发规范缺失或不符：{key}")
    stack = config.get("stack", {})
    if not isinstance(stack, dict) or any(
        not isinstance(stack.get(key), str) or not stack[key].strip()
        for key in ("frontend", "backend", "database", "agent", "model_provider")
    ):
        return issues + ["配置文件错误：stack 必须包含非空字符串形式的技术选型及模型来源"]
    layout = config.get("layout")
    if not isinstance(layout, dict):
        return issues + ["配置文件错误：缺少 layout；旧版或自定义结构需按已确认方案人工核对"]
    try:
        expected_layout = build_layout(stack, **{
            key: layout[key] for key in ("kind", "agent_mode", "source_dir", "database_owner", "migration_path", "evals")
        })
    except (KeyError, ValueError, TypeError) as exc:
        return issues + [f"布局配置错误：{exc}"]
    if layout != expected_layout:
        return issues + ["布局配置与应用边界不一致；自定义路径需按已确认方案人工核对"]
    for path in expected_layout["directories"]:
        if not (root / path).is_dir():
            issues.append(f"缺少目录：{path}")
    if needed(stack["backend"]) and not (root / "docs/api/contracts.md").is_file():
        issues.append("缺少：docs/api/contracts.md")
    if needed(stack["database"]) and not (root / "docs/database/data-model.md").is_file():
        issues.append("缺少：docs/database/data-model.md")
    rules = (root / "AGENTS.md").read_text(encoding="utf-8")
    for item in ("plan.md", "CHANGELOG.md", "CONTRIBUTING.md", "docs/development/sdd.md",
                 "简单任务", "单元测试", "集成测试", "E2E", "未经验证", "不可信输入"):
        if item not in rules:
            issues.append(f"AGENTS.md 缺少规则：{item}")
    sdd = (root / "docs/development/sdd.md").read_text(encoding="utf-8")
    for item in ("无需 SDD 文档", "spec.md", "plan.md", "新增功能", "复杂任务"):
        if item not in sdd:
            issues.append(f"轻量 SDD 规则缺少：{item}")
    git_guide = (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    for item in ("feat", "fix", "refactor", "BREAKING CHANGE", "CHANGELOG.md"):
        if item not in git_guide:
            issues.append(f"Git 提交规范缺少：{item}")
    for path, expected in (
        ("README.md", "尚无可执行命令"),
        ("docs/adr/0001-technology-stack.md", "备选方案"),
        ("docs/architecture/overview.md", "模块边界和数据流"),
        ("specs/_templates/spec.md", "AC-001"),
        ("specs/_templates/plan.md", "回滚"),
        ("docs/testing/strategy.md", "测试之间尽量隔离"),
    ):
        if expected not in (root / path).read_text(encoding="utf-8"):
            issues.append(f"模板缺少必要说明：{path}: {expected}")
    if "## [Unreleased]" not in (root / "CHANGELOG.md").read_text(encoding="utf-8"):
        issues.append("缺少未发布变更记录")
    for base in layout["applications"].values():
        for name in ("package.json", "requirements.txt", "pyproject.toml", "Dockerfile"):
            if (root / base / name).exists():
                issues.append(f"初始化阶段不应包含框架实现或依赖清单：{base}/{name}")
    if (root / ".github/workflows").exists():
        issues.append("当前不需要 CI/CD")
    compose = (root / "compose.yaml").read_text(encoding="utf-8")
    if "services: {}" not in compose or "不是可启动的 Docker 环境" not in compose:
        issues.append("Docker 占位配置未明确不可启动")
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python3 validate_project.py <项目目录>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    try:
        issues = validate(root)
    except (OSError, UnicodeError) as exc:
        issues = [f"无法读取项目文件：{exc}"]
    if issues:
        for issue in issues:
            print("未通过：" + issue)
        return 1
    print("验证通过：项目骨架、Git 提交约定及轻量 SDD 开发规范齐全；未验证可运行的应用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
