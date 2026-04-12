from __future__ import annotations

import csv
import json
import re
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


def run_deploy_check() -> str:
    manage = ROOT / "backend" / "manage.py"
    cmd = [
        sys.executable,
        str(manage if manage.exists() else ROOT / "manage.py"),
        "check",
        "--deploy",
    ]
    env = {
        "DJANGO_DEBUG": "0",
        "DJANGO_ENV": "production",
        "CROWN_ENV": "prod",
        "DJANGO_SECRET_KEY": "schema-local-check-only",
    }
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**env, **dict()},
    )
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    CHECK_OUTPUT.write_text(output, encoding="utf-8")
    return output


def parse_output(output: str) -> tuple[int, list[dict]]:
    lines = output.splitlines()
    root_pattern = re.escape(str(ROOT)).replace("\\\\", r"[\\/]")
    file_pattern = re.compile(root_pattern + r"[\\/](backend[\\/][^ :]+)")

    total = 0
    per_file: dict[str, int] = {}

    for i, line in enumerate(lines):
        if "drf_spectacular.W002" not in line:
            continue
        total += 1
        chunk = " ".join(lines[i:i + 4])
        match = file_pattern.search(chunk)
        if match:
            rel = match.group(1).replace("\\", "/")
        else:
            rel = "unknown"
        per_file[rel] = per_file.get(rel, 0) + 1

    ranked = [{"file": k, "count": v} for k, v in sorted(per_file.items(), key=lambda x: (-x[1], x[0]))]
    return total, ranked


def load_budget() -> dict:
    if not BUDGET_FILE.exists():
        return {"current_max": 999999, "next_target": 0, "goal": 0}
    return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))


def main() -> None:
    output = run_deploy_check()
    total, ranked = parse_output(output)
    budget = load_budget()

    summary = {
        "total_w002": total,
        "budget_current_max": budget.get("current_max", 999999),
        "budget_next_target": budget.get("next_target", 0),
        "budget_pass": total <= int(budget.get("current_max", 999999)),
        "top_files": ranked[:25],
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    DETAIL_JSON.write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    with DETAIL_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "count"])
        writer.writeheader()
        writer.writerows(ranked)

    md = [
        "# W002 Inventory",
        "",
        f"Total W002: {total}",
        f"Budget Current Max: {budget.get('current_max', 999999)}",
        f"Budget Pass: {summary['budget_pass']}",
        "",
        "| File | Count |",
        "|---|---:|",
    ]
    for item in ranked[:50]:
        md.append(f"| `{item['file']}` | {item['count']} |")
    DETAIL_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()