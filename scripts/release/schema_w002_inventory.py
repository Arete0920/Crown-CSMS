from __future__ import annotations

import csv
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "audit-artifacts" / "release-verify"
VERIFY_DIR.mkdir(parents=True, exist_ok=True)

BUDGET_FILE = ROOT / "docs" / "release" / "SCHEMA_W002_BUDGET.json"
CHECK_OUTPUT = VERIFY_DIR / "schema_w002_check.txt"
SUMMARY_JSON = VERIFY_DIR / "schema_w002_summary.json"
DETAIL_JSON = VERIFY_DIR / "schema_w002_inventory.json"
DETAIL_CSV = VERIFY_DIR / "schema_w002_inventory.csv"
DETAIL_MD = VERIFY_DIR / "schema_w002_inventory.md"
SCHEMA_OUTPUT = ROOT / "docs" / "openapi" / "crown-openapi.yaml"


def run_schema_export() -> tuple[str, int]:
    manage = ROOT / "backend" / "manage.py"
    SCHEMA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(manage if manage.exists() else ROOT / "manage.py"),
        "spectacular",
        "--file",
        str(SCHEMA_OUTPUT),
    ]
    env = {
        "DJANGO_DEBUG": "0",
        "DJANGO_ENV": "ci",
        "CROWN_ENV": "ci",
        "DJANGO_SECRET_KEY": os.getenv("DJANGO_SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or secrets.token_urlsafe(32),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./ci.sqlite3"),
    }
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, **env},
    )
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    CHECK_OUTPUT.write_text(output, encoding="utf-8")
    return output, result.returncode


def parse_output(output: str) -> tuple[int, int, int, list[dict]]:
    lines = output.splitlines()
    root_pattern = re.escape(str(ROOT)).replace("\\\\", r"[\\/]")
    file_pattern = re.compile(root_pattern + r"[\\/](backend[\\/][^ :]+)")

    error_summary = re.search(r"Errors:\s+(\d+)\s+\((\d+) unique\)", output)
    warning_summary = re.search(r"Warnings:\s+(\d+)\s+\((\d+) unique\)", output)

    unique_error_lines = sorted({line.strip() for line in lines if " Error [" in line})
    total_errors = int(error_summary.group(1)) if error_summary else len(unique_error_lines)
    unique_errors = int(error_summary.group(2)) if error_summary else len(unique_error_lines)
    unique_warnings = int(warning_summary.group(2)) if warning_summary else 0

    per_file: dict[str, int] = {}
    for line in unique_error_lines:
        match = file_pattern.search(line)
        rel = match.group(1).replace("\\", "/") if match else "unknown"
        per_file[rel] = per_file.get(rel, 0) + 1

    ranked = [
        {"file": file_name, "count": count}
        for file_name, count in sorted(per_file.items(), key=lambda item: (-item[1], item[0]))
    ]
    return total_errors, unique_errors, unique_warnings, ranked


def load_budget() -> dict:
    if not BUDGET_FILE.exists():
        return {"current_max": 999999, "next_target": 0, "goal": 0}
    return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))


def main() -> None:
    output, returncode = run_schema_export()
    total_errors, unique_errors, unique_warnings, ranked = parse_output(output)
    budget = load_budget()
    current_max = int(budget.get("current_max", 999999))
    goal = int(budget.get("goal", 0))

    summary = {
        "metric": "unique_schema_generation_errors",
        "total_w002": unique_errors,
        "total_schema_errors": total_errors,
        "unique_schema_errors": unique_errors,
        "unique_schema_warnings": unique_warnings,
        "schema_export_returncode": returncode,
        "budget_current_max": current_max,
        "budget_next_target": int(budget.get("next_target", 0)),
        "budget_goal": goal,
        "budget_pass": returncode == 0 and unique_errors <= current_max,
        "production_ready": returncode == 0 and unique_errors <= goal,
        "top_files": ranked[:25],
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    DETAIL_JSON.write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    with DETAIL_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "count"])
        writer.writeheader()
        writer.writerows(ranked)

    md = [
        "# OpenAPI Schema Error Inventory",
        "",
        f"Total schema errors: {total_errors}",
        f"Unique schema errors: {unique_errors}",
        f"Unique schema warnings: {unique_warnings}",
        f"Budget Current Max: {current_max}",
        f"Budget Pass: {summary['budget_pass']}",
        f"Zero-error schema goal met (NOT_VERIFIED release authority; goal={goal}): {summary['production_ready']}",
        "",
        "| File | Unique Error Count |",
        "|---|---:|",
    ]
    for item in ranked[:50]:
        md.append(f"| `{item['file']}` | {item['count']} |")
    DETAIL_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    if returncode != 0:
        print(output, file=sys.stderr)
        print(f"Schema export failed with exit code {returncode}.", file=sys.stderr)
        sys.exit(returncode)


if __name__ == "__main__":
    main()
