"""生成器与校验器共用的应用边界和相对路径规则。"""

import re


ABSENT = {"无", "无需", "不需要", "none", "no", "not needed", "n/a", "无agent"}
KINDS = ("split", "web", "api", "agent", "cli")


def needed(value: str) -> bool:
    return value.strip().casefold() not in ABSENT


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", value):
        raise ValueError("源码及迁移路径须为安全相对路径，如 src/my_app、alembic/versions")
    if value.split("/")[0] in {"docs", "specs", "tests", "apps", "packages", "infra", "evals", "public"}:
        raise ValueError("源码及迁移路径不能占用文档、测试或应用容器目录")
    return value


def join(base: str, path: str) -> str:
    return path if base == "." else f"{base}/{path}"


def build_layout(stack: dict, *, kind: str, agent_mode: str = "embedded",
                 source_dir: str = "src", database_owner: str | None = None,
                 migration_path: str = "migrations", evals: bool = False) -> dict:
    if kind not in KINDS or agent_mode not in {"embedded", "standalone"} or type(evals) is not bool:
        raise ValueError("未知的布局、Agent 模式或评估设置")
    source_dir, migration_path = relative_path(source_dir), relative_path(migration_path)
    front, back, agent, database = (needed(stack[k]) for k in ("frontend", "backend", "agent", "database"))
    if agent_mode == "standalone" and not agent:
        raise ValueError("未选择 Agent，不能指定独立 Agent 模式")
    if kind == "split":
        apps = {key: f"apps/{key}" for key, present in (("web", front), ("api", back)) if present}
        if agent and agent_mode == "standalone":
            apps["agent"] = "apps/agent"
        if len(apps) < 2:
            raise ValueError("split 至少需要两个独立应用；单应用请选择 web、api、agent 或 cli")
    else:
        if kind == "web" and not front:
            raise ValueError("web 布局需要前端；同应用服务端能力可记录在 backend")
        if kind == "api" and (front or not back):
            raise ValueError("api 布局需要后端且不包含前端")
        if kind in {"agent", "cli"} and (front or back):
            raise ValueError("agent/cli 布局不包含独立前端或后端")
        if kind == "agent" and not agent:
            raise ValueError("agent 布局需要选择 Agent 框架或 Harness")
        if agent_mode == "standalone" and kind != "agent":
            raise ValueError("单应用中的 Agent 应内嵌；独立运行请选择 agent 或 split 布局")
        apps = {kind: "."}
        if kind == "agent":
            agent_mode = "standalone"
    primary = next(key for key in ("api", "web", "agent", "cli") if key in apps)
    mode = "none" if not agent else ("standalone" if "agent" in apps else "embedded")
    agent_owner = "agent" if "agent" in apps else primary
    agent_path = None if not agent else join(apps[agent_owner], source_dir if mode == "standalone" else f"{source_dir}/agents")
    if database_owner is not None and (not database or database_owner not in apps):
        raise ValueError("数据库归属必须是已存在的应用，且需选择数据库")
    owner = (database_owner or primary) if database else None
    db_path = join(apps[owner], migration_path) if owner else None
    if db_path:
        source_path = join(apps[owner], source_dir)
        if source_path == db_path or source_path.startswith(db_path + "/"):
            raise ValueError("迁移目录不能覆盖应用源码目录")
    if db_path and agent_path and (db_path == agent_path or agent_path.startswith(db_path + "/")):
        raise ValueError("迁移目录不能覆盖 Agent 源码目录")
    directories = []
    test_paths = []
    for base in apps.values():
        directories.append(join(base, source_dir))
        for level in ("unit", "integration"):
            test_paths.append(join(base, f"tests/{level}"))
    test_paths.append("tests/e2e")
    directories.extend(test_paths)
    if front:
        directories.append(join(apps["web"], "public"))
    if agent_path:
        directories.append(agent_path)
    if db_path:
        directories.append(db_path)
    eval_path = join(apps[agent_owner if agent else primary], "evals") if evals else None
    if eval_path:
        directories.append(eval_path)
    return {"kind": kind, "agent_mode": agent_mode, "source_dir": source_dir,
            "database_owner": owner, "migration_path": migration_path, "evals": evals,
            "applications": apps, "agent_path": agent_path, "agent_runtime": mode,
            "database_path": db_path, "eval_path": eval_path,
            "test_paths": test_paths, "directories": sorted(set(directories))}
