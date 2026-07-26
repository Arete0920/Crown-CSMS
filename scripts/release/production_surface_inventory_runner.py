#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

BASE_PATH = Path(__file__).with_name("production_surface_inventory.py")
SPEC = importlib.util.spec_from_file_location("production_surface_inventory_base", BASE_PATH)
if not SPEC or not SPEC.loader:
    raise RuntimeError(f"Unable to load {BASE_PATH}")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BASE
SPEC.loader.exec_module(BASE)

DASHBOARD_CALL_RE = re.compile(r"(?<!function )\bcreateDashboard\(\s*\{")
STEP_FILE_RE = re.compile(r"^Step\d+[A-Za-z0-9_-]*$", re.I)
TASK_DECORATORS = {"shared_task", "task", "celery.task", "app.task"}
WORKFLOW_NAME_RE = re.compile(
    r'''^name:\s*(?:"([^"\r\n]+)"|'([^'\r\n]+)'|([^#\r\n]+?))\s*(?:#.*)?$''',
    re.M,
)
HIGH_RISK_COMMAND_RE = re.compile(
    r"(?:purge|delete|reset|fix|repair|migrate|seed|bootstrap|enforce|rotate|sync|import|export|reconcile)",
    re.I,
)


def dashboards(root: Path, paths: dict[str, str]):
    path = root / "frontend/dashboards/src/config/dashboardRegistry.js"
    source = BASE.text(path)
    rows = []
    for match in DASHBOARD_CALL_RE.finditer(source):
        brace = source.find("{", match.start())
        block, _ = BASE.region(source, brace, "{", "}")
        fields = {key: value.strip() for key, value in BASE.FIELD_RE.findall(block)}
        key = BASE.literal(fields.get("key", "")) or f"unresolved-line-{BASE.line(source, match.start())}"
        raw_path = fields.get("path", "")
        route = BASE.literal(raw_path)
        if route is None and raw_path.startswith("PATHS."):
            route = paths.get(raw_path.split(".", 1)[1], "")
        label = BASE.literal(fields.get("label", "")) or BASE.literal(fields.get("title", "")) or key
        rows.append(
            BASE.Surface(
                f"dashboard:{BASE.slug(key)}",
                "dashboard",
                label,
                route or "",
                path.relative_to(root).as_posix(),
                BASE.line(source, match.start()),
            )
        )
    if not rows:
        raise ValueError("no dashboard registry entries")
    return rows


def wizard_steps(root: Path):
    source_root = root / "frontend/dashboards/src"
    pages_root = source_root / "pages"
    files = sorted(
        {
            path
            for pattern in ("*.js", "*.jsx", "*.ts", "*.tsx")
            for path in source_root.rglob(pattern)
            if path.is_file()
        }
    )
    rows = {}
    for path in files:
        source = BASE.text(path)
        normalized = path.as_posix().lower()
        if "wizard" in normalized or path.stem.lower().endswith("wizard"):
            for array_match in BASE.STEP_ARRAY_RE.finditer(source):
                bracket = source.find("[", array_match.start())
                try:
                    array_source, _ = BASE.region(source, bracket, "[", "]")
                except ValueError:
                    continue
                for block, offset in BASE.object_literals(array_source):
                    step_id = BASE.STEP_ID_RE.search(block)
                    step_label = BASE.STEP_LABEL_RE.search(block)
                    if not step_id or not step_label:
                        continue
                    surface_id = f"wizard_step:{BASE.slug(path.stem)}:{BASE.slug(step_id.group(1))}"
                    rows.setdefault(
                        surface_id,
                        BASE.Surface(
                            surface_id,
                            "wizard_step",
                            f"{path.stem}: {step_label.group(1)}",
                            "",
                            path.relative_to(root).as_posix(),
                            BASE.line(source, bracket + 1 + offset),
                        ),
                    )
        if path.is_relative_to(pages_root) and STEP_FILE_RE.fullmatch(path.stem):
            parent = path.parent.relative_to(pages_root).as_posix()
            owner = parent if parent != "." else "pages"
            surface_id = f"wizard_step:{BASE.slug(owner)}:{BASE.slug(path.stem)}"
            rows.setdefault(
                surface_id,
                BASE.Surface(
                    surface_id,
                    "wizard_step",
                    f"{owner}: {path.stem}",
                    "",
                    path.relative_to(root).as_posix(),
                    1,
                ),
            )
    return sorted(rows.values(), key=lambda row: row.surface_id)


def decorator_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return decorator_name(node.value) + "." + node.attr
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    return ""


def tasks(root: Path):
    rows = []
    for path in sorted((root / "backend").rglob("tasks.py")):
        if any(part in {"migrations", "tests", "test"} for part in path.parts):
            continue
        tree = ast.parse(BASE.text(path), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name.startswith("_"):
                continue
            decorators = {decorator_name(item) for item in node.decorator_list}
            if not any(name in TASK_DECORATORS or name.endswith(".shared_task") for name in decorators):
                continue
            module = path.parent.name
            rows.append(
                BASE.Surface(
                    f"task:{BASE.slug(module)}:{BASE.slug(node.name)}",
                    "task",
                    f"{module}.{node.name}",
                    "",
                    path.relative_to(root).as_posix(),
                    node.lineno,
                )
            )
    return rows


def management_commands(root: Path):
    rows = []
    for path in sorted((root / "backend").rglob("management/commands/*.py")):
        if path.name == "__init__.py" or any(part in {"tests", "test", "migrations"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        command = path.stem
        owner = path.parts[path.parts.index("backend") + 1] if "backend" in path.parts else path.parent.parent.parent.name
        rows.append(
            BASE.Surface(
                f"command:{BASE.slug(command)}:{BASE.slug(relative)}",
                "command",
                f"{owner}.{command}",
                command,
                relative,
                1,
            )
        )
    return rows


def workflow_name(source: str, fallback: str) -> tuple[str, re.Match[str] | None]:
    match = WORKFLOW_NAME_RE.search(source)
    if not match:
        return fallback, None
    name = next((value for value in match.groups() if value is not None), fallback).strip()
    return name or fallback, match


def workflows(root: Path):
    rows = []
    workflow_root = root / ".github/workflows"
    for path in sorted(list(workflow_root.glob("*.yml")) + list(workflow_root.glob("*.yaml"))):
        source = BASE.text(path)
        name, match = workflow_name(source, path.stem)
        relative = path.relative_to(root).as_posix()
        rows.append(
            BASE.Surface(
                f"workflow:{BASE.slug(path.stem)}",
                "workflow",
                name,
                relative,
                relative,
                BASE.line(source, match.start()) if match else 1,
            )
        )
    return rows


ORIGINAL_CLASSIFY = BASE.classify
ORIGINAL_BUILD = BASE.build


def classify(row):
    if row.domain == "command":
        if HIGH_RISK_COMMAND_RE.search(row.name):
            return BASE.mapped(
                row,
                "OPERATIONAL_DRILL",
                "management-command-operational-proof",
                "Mutating or environment-sensitive management commands require an operational drill.",
            )
        return BASE.mapped(
            row,
            "BACKEND_TEST",
            "management-command-test",
            "Deterministic management commands require focused backend tests.",
        )
    if row.domain == "workflow":
        return BASE.mapped(
            row,
            "MANUAL_REVIEW",
            "workflow-authority-review",
            "Workflow triggers, permissions, jobs, artifacts, and authority require controlled review.",
        )
    return ORIGINAL_CLASSIFY(row)


def build(root: Path):
    rows = ORIGINAL_BUILD(root)
    rows += [classify(row) for row in management_commands(root)]
    rows += [classify(row) for row in workflows(root)]
    return rows


BASE.dashboards = dashboards
BASE.parse_dashboards = dashboards
BASE.wizard_steps = wizard_steps
BASE.parse_wizard_steps = wizard_steps
BASE.tasks = tasks
BASE.parse_tasks = tasks
BASE.management_commands = management_commands
BASE.parse_management_commands = management_commands
BASE.workflows = workflows
BASE.parse_workflows = workflows
BASE.classify = classify
BASE.build = build
BASE.REQUIRED.update({"command", "workflow"})

if __name__ == "__main__":
    raise SystemExit(BASE.main())
