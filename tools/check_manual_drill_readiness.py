from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "recovery": REPO_ROOT / ".github" / "workflows" / "recovery-control-drill.yml",
    "secrets": REPO_ROOT / ".github" / "workflows" / "secrets-control-drill.yml",
}
REQUIRED_TOKENS = (
    "workflow_dispatch:",
    "actions/upload-artifact@v4",
    "if-no-files-found: error",
    "production_mutation_performed",
)


def check_workflow(name: str, path: Path) -> dict:
    failures = []
    if not path.exists():
        failures.append("workflow file missing")
        return {"name": name, "path": path.as_posix(), "ready": False, "failures": failures}
    text = path.read_text(encoding="utf-8-sig")
    for token in REQUIRED_TOKENS:
        if token not in text:
            failures.append(f"missing required token: {token}")
    if "pull_request:" in text or "push:" in text:
        failures.append("drill must remain manual-only")
    return {
        "name": name,
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "ready": not failures,
        "failures": failures,
    }


def build_report() -> dict:
    records = [check_workflow(name, path) for name, path in sorted(WORKFLOWS.items())]
    failures = [f"{record['name']}: {failure}" for record in records for failure in record["failures"]]
    return {
        "schema_version": 1,
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
