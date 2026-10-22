#!/usr/bin/env python3
"""验证手动确认、防覆盖、精简目录与自定义技术选择。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


def run(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(HERE / "init_project.py"), *extra],
                          text=True, capture_output=True)


def args(target: Path, agent: str = "LangGraph") -> tuple[str, ...]:
    return ("--name", "demo", "--target", str(target), "--product-summary", "企业文档问答助手",
            "--frontend", "Next.js", "--backend", "FastAPI", "--database", "PostgreSQL",
            "--agent", agent, "--model-provider", "待定", "--layout", "split")


class ProjectInitTests(unittest.TestCase):
    def test_skill_is_explicitly_manual_only(self):
        skill = (HERE.parent / "SKILL.md").read_text(encoding="utf-8")
        metadata = (HERE.parent / "agents" / "openai.yaml").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: init-ai-project$")
        # Codex 的手动调用策略由 agents/openai.yaml 声明。
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            result = run(*args(target), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_no_confirmation_means_no_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            result = run(*args(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())

    def test_confirmed_minimal_scaffold(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            result = run(*args(target), "--confirmed")
            self.assertEqual(result.returncode, 0, result.stderr)
            validation = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                        text=True, capture_output=True)
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            conf = json.loads((target / "project.config.json").read_text(encoding="utf-8"))
            self.assertTrue(conf["user_confirmed"])
            self.assertEqual(conf["stack"]["agent"], "LangGraph")
            self.assertEqual(conf["project_policy"]["spec_driven"], "lightweight_custom")
            self.assertTrue(conf["project_policy"]["simple_change_docs_optional"])
            self.assertEqual(conf["project_policy"]["git_commit_convention"], "conventional_commits")
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            sdd = (target / "docs/development/sdd.md").read_text(encoding="utf-8")
            contributions = (target / "CONTRIBUTING.md").read_text(encoding="utf-8")
            self.assertIn("简单任务不强制写 SDD 文档", agents)
            self.assertIn("新增功能或较大重构", agents)
            self.assertIn("复杂任务必须", agents)
            self.assertIn("增加内部工具函数", sdd)
            self.assertIn("无需 SDD 文档", sdd)
            self.assertIn("feat(agent):", contributions)
            self.assertIn("BREAKING CHANGE", contributions)
            self.assertIn("feat(api)!:", contributions)
            self.assertIn("不可信输入", agents)
            self.assertIn("备选方案", (target / "docs/adr/0001-technology-stack.md").read_text(encoding="utf-8"))
            self.assertIn("不是可启动的 Docker 环境", (target / "compose.yaml").read_text(encoding="utf-8"))
            self.assertFalse((target / "specs/0001-demo/spec.md").exists())
            self.assertTrue((target / "apps/api/tests/unit").is_dir())
            self.assertTrue((target / "apps/api/src/agents").is_dir())
            self.assertTrue((target / "apps/api/migrations").is_dir())
            self.assertTrue((target / "apps/web/tests/unit").is_dir())
            for path in ("services", "database", "packages", "infra", "tests/unit"):
                self.assertFalse((target / path).exists(), path)
            self.assertFalse((target / "apps/web/package.json").exists())
            self.assertFalse((target / "apps/web/Dockerfile").exists())
            self.assertFalse((target / "tests/e2e/package.json").exists())
            self.assertFalse((target / ".github/workflows").exists())
            second = run(*args(target), "--confirmed")
            self.assertNotEqual(second.returncode, 0)

    def test_harness_and_optional_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            result = run(*args(target, "DeepSeek Harness"), "--confirmed")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DeepSeek Harness", (target / "AGENTS.md").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            result = run(*args(target, "无"), "--confirmed")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((target / "apps/agent").exists())
            self.assertFalse((target / "apps/api/src/agents").exists())
            self.assertFalse((target / "apps/api/evals").exists())

    def test_compose_name_safe_for_project_name_with_period(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "My.AI"
            argv = list(args(target))
            argv[1] = "My.AI"
            result = run(*argv, "--confirmed")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("name: my-ai", (target / "compose.yaml").read_text(encoding="utf-8"))

    def test_missing_development_rules_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            created = run(*args(target), "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            (target / "CONTRIBUTING.md").unlink()
            validated = subprocess.run(
                [sys.executable, str(HERE / "validate_project.py"), str(target)],
                text=True, capture_output=True,
            )
            self.assertNotEqual(validated.returncode, 0)
            self.assertIn("缺少：CONTRIBUTING.md", validated.stdout)

    def test_user_text_is_preserved_and_stack_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            argv = list(args(target))
            summary = "解释 {{FRONTEND}} 与 {{UNDEFINED}} 的模板助手"
            argv[argv.index("--product-summary") + 1] = summary
            argv[argv.index("--frontend") + 1] = " Next.js "
            result = run(*argv, "--confirmed")
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads((target / "project.config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["stack"]["frontend"], "Next.js")
            self.assertEqual(config["product_summary"], summary)
            self.assertIn(summary, (target / "docs/product/brief.md").read_text(encoding="utf-8"))

    def test_invalid_config_reports_issue_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            created = run(*args(target), "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            path = target / "project.config.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            invalid_configs = [
                [],
                {**original, "stack": None},
                {**original, "stack": {**original["stack"], "agent": 123}},
                {**original, "project_policy": []},
                {**original, "user_confirmed": "false"},
                {**original, "layout": None},
                {**original, "layout": {**original["layout"], "source_dir": "../outside"}},
                {**original, "layout": {**original["layout"], "kind": []}},
            ]
            for invalid in invalid_configs:
                with self.subTest(config=invalid):
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(HERE / "validate_project.py"), str(target)],
                        text=True, capture_output=True,
                    )
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn("未通过：", result.stdout)
                    self.assertNotIn("Traceback", result.stderr)

    def test_missing_api_contract_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            created = run(*args(target), "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            (target / "docs/api/contracts.md").unlink()
            result = subprocess.run(
                [sys.executable, str(HERE / "validate_project.py"), str(target)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("缺少：docs/api/contracts.md", result.stdout)

    def test_all_optional_components_can_be_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            argv = list(args(target))
            for flag in ("--frontend", "--backend", "--database", "--agent"):
                argv[argv.index(flag) + 1] = "无"
            argv[argv.index("--layout") + 1] = "cli"
            created = run(*argv, "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            for path in ("apps", "services", "database", "packages", "docs/api", "docs/database"):
                self.assertFalse((target / path).exists(), path)
            result = subprocess.run(
                [sys.executable, str(HERE / "validate_project.py"), str(target)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_single_application_layouts(self):
        cases = [
            ("web", "Next.js", "Next.js route handlers", "LangGraph"),
            ("api", "无", "FastAPI", "LangGraph"),
            ("agent", "无", "无", "LangGraph"),
            ("cli", "无", "无", "无"),
        ]
        for kind, front, back, agent in cases:
            with self.subTest(layout=kind), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / "demo"
                argv = list(args(target, agent))
                for flag, value in (("--layout", kind), ("--frontend", front), ("--backend", back)):
                    argv[argv.index(flag) + 1] = value
                created = run(*argv, "--confirmed")
                self.assertEqual(created.returncode, 0, created.stderr)
                for path in ("src", "tests/unit", "tests/integration", "tests/e2e", "migrations"):
                    self.assertTrue((target / path).is_dir(), path)
                self.assertFalse((target / "apps").exists())
                self.assertEqual((target / "public").is_dir(), kind == "web")
                self.assertEqual((target / "src/agents").is_dir(), kind in {"web", "api"})
                if kind == "agent":
                    config = json.loads((target / "project.config.json").read_text(encoding="utf-8"))
                    self.assertEqual(config["layout"]["agent_runtime"], "standalone")
                checked = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                         text=True, capture_output=True)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_independent_agent_with_web_without_api(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            argv = list(args(target))
            argv[argv.index("--backend") + 1] = "无"
            created = run(*argv, "--agent-mode", "standalone", "--database-owner", "agent",
                          "--migration-path", "checkpoints/migrations", "--evals", "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            for path in ("apps/agent/src", "apps/agent/evals", "apps/agent/checkpoints/migrations"):
                self.assertTrue((target / path).is_dir(), path)
            for path in ("apps/api", "apps/web/src/agents", "apps/web/migrations", "docs/api"):
                self.assertFalse((target / path).exists(), path)
            checked = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                     text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_framework_paths_and_optional_evaluation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            created = run(*args(target), "--source-dir", "src/my_app",
                          "--migration-path", "alembic/versions", "--evals", "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            for path in ("apps/api/src/my_app/agents", "apps/api/alembic/versions", "apps/api/evals"):
                self.assertTrue((target / path).is_dir(), path)
            self.assertFalse((target / "apps/api/migrations").exists())
            self.assertFalse((target / "apps/web/evals").exists())
            checked = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                     text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_invalid_boundaries_and_paths_do_not_write(self):
        cases = [
            ("--source-dir", "../escape"),
            ("--migration-path", "C:/escape"),
            ("--migration-path", "tests/unit"),
            ("--migration-path", "src"),
            ("--database-owner", "agent"),
        ]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            for extra in cases:
                with self.subTest(extra=extra):
                    result = run(*args(target), *extra, "--confirmed")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(target.exists())
            argv = list(args(target))
            argv[argv.index("--frontend") + 1] = "无"
            result = run(*argv, "--confirmed")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())

    def test_missing_layout_directory_and_modified_layout_fail_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo"
            created = run(*args(target), "--confirmed")
            self.assertEqual(created.returncode, 0, created.stderr)
            folder = target / "apps/api/src/agents"
            (folder / ".gitkeep").unlink()
            folder.rmdir()
            checked = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                     text=True, capture_output=True)
            self.assertEqual(checked.returncode, 1)
            self.assertIn("apps/api/src/agents", checked.stdout)
            folder.mkdir()
            config_path = target / "project.config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["layout"]["directories"] = ["../escape"]
            config_path.write_text(json.dumps(config), encoding="utf-8")
            checked = subprocess.run([sys.executable, str(HERE / "validate_project.py"), str(target)],
                                     text=True, capture_output=True)
            self.assertEqual(checked.returncode, 1)
            self.assertIn("布局配置", checked.stdout)


if __name__ == "__main__":
    unittest.main()
