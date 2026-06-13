#!/usr/bin/env python3
"""Generate wizard frontend/backend parity evidence for CI.

This script is intentionally read-only. It compares:
- frontend/dashboards/src/routes/wizards.js RAW_WIZARD_ROUTE_DEFINITIONS
- backend/crown_api/wizard_registry.py WIZARDS

It writes the same evidence shape expected by the Sandbox Ready Evidence Gate:
- audit-artifacts/wizard-parity/<stamp>/20_wizard_frontend_backend_parity.csv
- audit-artifacts/wizard-parity/<stamp>/21_wizard_frontend_rows.csv
- audit-artifacts/wizard-parity/<stamp>/22_wizard_backend_rows.csv
- audit-artifacts/wizard-parity/<stamp>/99_STATUS.json
- audit-artifacts/wizard-parity/<stamp>/00_SUMMARY.md
- audit-artifacts/wizard-parity/latest/*
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class FrontendWizard:
    Name: str
    Path: str
    ApiPrefix: str
    Component: str
    ReleaseState: str
    Roles: str


@dataclass
class BackendWizard:
    Name: str
    AppConfig: str
    UrlPrefix: str
    UrlsModule: str


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def git_value(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def normalize_api_prefix(value: str) -> str:
    value = (value or "").strip().strip("\"'")
    if value.startswith("/"):
        value = value[1:]
    if value and not value.endswith("/"):
        value += "/"
    return value


def normalize_path(value: str) -> str:
    value = (value or "").strip().strip("\"'")
    if value and not value.startswith("/"):
        value = "/" + value
    return value


def extract_balanced(text: str, start_index: int, open_char: str, close_char: str) -> str:
    depth = 0
    in_string = False
    quote = ""
    escape = False
    start = -1
    for index in range(start_index, len(text)):
        ch = text[index]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == quote:
                in_string = False
            continue
        if ch in {"'", '"', "`"}:
            in_string = True
            quote = ch
            continue
        if ch == open_char:
            if depth == 0:
                start = index
            depth += 1
            continue
        if ch == close_char and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                return text[start : index + 1]
    raise ValueError(f"Unable to find balanced {open_char}{close_char} block")


def object_blocks(array_text: str) -> list[str]:
    blocks: list[str] = []
    depth = 0
    in_string = False
    quote = ""
    escape = False
    start = -1
    for index, ch in enumerate(array_text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == quote:
                in_string = False
            continue
        if ch in {"'", '"', "`"}:
            in_string = True
            quote = ch
            continue
        if ch == "{":
            if depth == 0:
                start = index
            depth += 1
            continue
        if ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                blocks.append(array_text[start : index + 1])
                start = -1
    return blocks


def string_property(block: str, name: str) -> str:
    pattern = re.compile(rf"(?m)[\"']?{re.escape(name)}[\"']?\s*:\s*[\"']([^\"']+)[\"']")
    match = pattern.search(block)
    return match.group(1) if match else ""


def identifier_property(block: str, name: str) -> str:
    pattern = re.compile(rf"(?m)[\"']?{re.escape(name)}[\"']?\s*:\s*([A-Za-z0-9_]+)")
    match = pattern.search(block)
    return match.group(1) if match else ""


def array_string_property(block: str, name: str) -> list[str]:
    pattern = re.compile(rf"(?s)[\"']?{re.escape(name)}[\"']?\s*:\s*\[(?P<body>.*?)\]")
    match = pattern.search(block)
    if not match:
        return []
    return re.findall(r"[\"']([^\"']+)[\"']", match.group("body"))


def parse_frontend(path: Path) -> list[FrontendWizard]:
    text = path.read_text(encoding="utf-8")
    assignment = re.search(r"RAW_WIZARD_ROUTE_DEFINITIONS\s*=\s*\[", text)
    if not assignment:
        raise ValueError("Missing RAW_WIZARD_ROUTE_DEFINITIONS assignment")
    array = extract_balanced(text, assignment.end() - 1, "[", "]")
    rows: list[FrontendWizard] = []
    for block in object_blocks(array):
        route_path = normalize_path(string_property(block, "path"))
        if not route_path:
            continue
        rows.append(
            FrontendWizard(
                Name=string_property(block, "name"),
                Path=route_path,
                ApiPrefix=normalize_api_prefix(string_property(block, "apiPrefix")),
                Component=identifier_property(block, "component"),
                ReleaseState=string_property(block, "releaseState") or "draft",
                Roles=";".join(array_string_property(block, "roles")),
            )
        )
    return rows


def literal_string(node: ast.AST) -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ""


def parse_backend(path: Path) -> list[BackendWizard]:
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    wizard_list: ast.List | None = None
    for node in tree.body:
        value = None
        targets: Iterable[ast.AST] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets = [node.target]
        if value is not None and any(isinstance(t, ast.Name) and t.id == "WIZARDS" for t in targets):
            if isinstance(value, ast.List):
                wizard_list = value
                break
    if wizard_list is None:
        raise ValueError("Missing WIZARDS list assignment")

    rows: list[BackendWizard] = []
    for element in wizard_list.elts:
        if not isinstance(element, ast.Dict):
            continue
        values: dict[str, str] = {}
        for key_node, value_node in zip(element.keys, element.values):
            key = literal_string(key_node) if key_node else ""
            values[key] = literal_string(value_node)
        url_prefix = normalize_api_prefix(values.get("url_prefix", ""))
        if not url_prefix:
            continue
        rows.append(
            BackendWizard(
                Name=values.get("name", ""),
                AppConfig=values.get("app_config", ""),
                UrlPrefix=url_prefix,
                UrlsModule=values.get("urls_module", ""),
            )
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"Notice": "none"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="audit-artifacts/wizard-parity")
    parser.add_argument("--fail-on-incomplete", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    frontend_path = root / "frontend/dashboards/src/routes/wizards.js"
    backend_path = root / "backend/crown_api/wizard_registry.py"
    pages_root = root / "frontend/dashboards/src/pages"

    frontend_rows = parse_frontend(frontend_path)
    backend_rows = parse_backend(backend_path)
    backend_by_prefix = {row.UrlPrefix: row for row in backend_rows}
    frontend_by_prefix = {row.ApiPrefix: row for row in frontend_rows if row.ApiPrefix}

    matrix: list[dict[str, object]] = []
    for frontend in frontend_rows:
        backend = backend_by_prefix.get(frontend.ApiPrefix)
        component_path = ""
        if frontend.Component:
            for ext in (".jsx", ".tsx", ".js", ".ts"):
                candidate = pages_root / f"{frontend.Component}{ext}"
                if candidate.exists():
                    component_path = str(candidate.relative_to(root)).replace("\\", "/")
                    break
        backend_found = backend is not None
        component_found = bool(component_path)
        roles_declared = bool(frontend.Roles)
        decision = "PASS" if backend_found and component_found and roles_declared else "REVIEW_REQUIRED"
        matrix.append(
            {
                "FrontendName": frontend.Name,
                "FrontendPath": frontend.Path,
                "FrontendApiPrefix": frontend.ApiPrefix,
                "FrontendComponent": frontend.Component,
                "FrontendReleaseState": frontend.ReleaseState,
                "FrontendRoles": frontend.Roles,
                "BackendFound": backend_found,
                "BackendName": backend.Name if backend else "",
                "BackendUrlPrefix": backend.UrlPrefix if backend else "",
                "BackendAppConfig": backend.AppConfig if backend else "",
                "BackendUrlsModule": backend.UrlsModule if backend else "",
                "ComponentFound": component_found,
                "ComponentPath": component_path,
                "RolesDeclared": roles_declared,
                "Decision": decision,
            }
        )

    for backend in backend_rows:
        if backend.UrlPrefix not in frontend_by_prefix:
            matrix.append(
                {
                    "FrontendName": "",
                    "FrontendPath": "",
                    "FrontendApiPrefix": "",
                    "FrontendComponent": "",
                    "FrontendReleaseState": "",
                    "FrontendRoles": "",
                    "BackendFound": True,
                    "BackendName": backend.Name,
                    "BackendUrlPrefix": backend.UrlPrefix,
                    "BackendAppConfig": backend.AppConfig,
                    "BackendUrlsModule": backend.UrlsModule,
                    "ComponentFound": False,
                    "ComponentPath": "",
                    "RolesDeclared": False,
                    "Decision": "BACKEND_ONLY_REVIEW_REQUIRED",
                }
            )

    review_rows = [row for row in matrix if row["Decision"] != "PASS"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = root / args.output_root
    output_dir = output_root / stamp
    latest_dir = output_root / "latest"
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    write_csv(output_dir / "20_wizard_frontend_backend_parity.csv", matrix)
    write_csv(output_dir / "21_wizard_frontend_rows.csv", [asdict(row) for row in frontend_rows])
    write_csv(output_dir / "22_wizard_backend_rows.csv", [asdict(row) for row in backend_rows])

    status = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(root),
        "branch": git_value("branch", "--show-current"),
        "head": git_value("rev-parse", "HEAD"),
        "frontend_count": len(frontend_rows),
        "backend_count": len(backend_rows),
        "matrix_count": len(matrix),
        "review_required_count": len(review_rows),
        "pass": len(review_rows) == 0,
    }
    (output_dir / "99_STATUS.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    summary_lines = [
        "# Wizard Frontend/Backend Parity Summary",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Frontend wizard routes: {len(frontend_rows)}",
        f"- Backend wizard entries: {len(backend_rows)}",
        f"- Matrix rows: {len(matrix)}",
        f"- Review required rows: {len(review_rows)}",
        "",
        "## Verdict",
        "",
        "PASS" if not review_rows else "REVIEW REQUIRED",
    ]
    if review_rows:
        summary_lines.extend(["", "## Rows requiring review"])
        for row in review_rows:
            label = row.get("FrontendPath") or row.get("BackendUrlPrefix") or "UNKNOWN"
            summary_lines.append(f"- {label} :: {row['Decision']}")
    (output_dir / "00_SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    for item in latest_dir.glob("*"):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    for item in output_dir.glob("*"):
        shutil.copy2(item, latest_dir / item.name)

    print(f"WIZARD_PARITY_EVIDENCE={output_dir}")
    print(f"WIZARD_PARITY_SUMMARY={output_dir / '00_SUMMARY.md'}")
    print(f"WIZARD_PARITY_MATRIX={output_dir / '20_wizard_frontend_backend_parity.csv'}")
    print(json.dumps(status, indent=2))
    if review_rows:
        print("WIZARD_PARITY_REVIEW_ROWS_BEGIN")
        for row in review_rows:
            print(f"{row.get('FrontendPath') or row.get('BackendUrlPrefix')} :: {row['Decision']}")
        print("WIZARD_PARITY_REVIEW_ROWS_END")
    if args.fail_on_incomplete and review_rows:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - CI diagnostic script must print all failure detail.
        print(f"WIZARD_PARITY_EXCEPTION={exc.__class__.__name__}: {exc}", file=sys.stderr)
        raise
