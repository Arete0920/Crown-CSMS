from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "recovery": REPO_ROOT / ".github" / "workflows" / "recovery-control-drill.yml",
    "secrets": REPO_ROOT / ".github" / "workflows" / "secrets-control-drill.yml",
}
REQUIRED_TOKENS = (
    "workflow_dispatch:",
    "uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "if-no-files-found: error",
    "production_mutation_performed",
)


def top_level_mapping_children(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    in_mapping = False
    children: list[str] = []
    for line in lines:
        if re.match(rf"^{re.escape(key)}:\s*(?:#.*)?$", line):
            in_mapping = True
            continue
        if in_mapping and line and not line.startswith(" "):
            break
        if in_mapping:
            match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(?:#.*)?$", line)
            if match:
                children.append(match.group(1))
    return sorted(set(children))


def check_workflow(name: str, path: Path) -> dict:
    failures = []
    if not path.exists():
        failures.append("workflow file missing")
        return {"name": name, "path": path.as_posix(), "ready": False, "failures": failures}
    text = path.read_text(encoding="utf-8-sig")
    for token in REQUIRED_TOKENS:
        if token not in text:
            failures.append(f"missing required token: {token}")
    triggers = top_level_mapping_children(text, "on")
    if triggers != ["workflow_dispatch"]:
        failures.append(f"drill must remain manual-only; observed triggers: {triggers}")
    return {
        "name": name,
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "ready": not failures,
        "triggers": triggers,
        "failures": failures,
    }


def build_report() -> dict:
    records = [check_workflow(name, path) for name, path in sorted(WORKFLOWS.items())]
    failures = [f"{record['name']}: {failure}" for record in records for failure in record["failures"]]
    return {
        "schema_version": 2,
        "mode": "manual_drill_static_readiness",
        "execution_performed": False,
        "production_mutation_performed": False,
        "failures": failures,
        "records": records,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
