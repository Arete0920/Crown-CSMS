from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
TRIGGERS = ("pull_request", "push", "workflow_dispatch", "schedule", "workflow_call")


def extract_jobs(text: str) -> list[str]:
    lines = text.splitlines()
    in_jobs = False
    jobs = []
    for line in lines:
        if re.match(r"^jobs:\s*(?:#.*)?$", line):
            in_jobs = True
            continue
        if in_jobs and line and not line.startswith(" "):
            break
        if in_jobs:
            match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(?:#.*)?$", line)
            if match:
                jobs.append(match.group(1))
    return sorted(set(jobs))


def inspect_workflow(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    triggers = sorted(
        trigger
        for trigger in TRIGGERS
        if re.search(rf"^\s*{re.escape(trigger)}\s*:", text, re.MULTILINE)
    )
    jobs = extract_jobs(text)
    artifact_uploads = len(re.findall(r"actions/upload-artifact@", text))
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "triggers": triggers,
        "job_count": len(jobs),
        "jobs": jobs,
        "artifact_upload_count": artifact_uploads,
        "uses_reusable_workflow": "uses: ./.github/workflows/" in text,
    }


def build_inventory() -> dict:
    paths = sorted({*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")})
    records = [inspect_workflow(path) for path in paths]
    records.sort(key=lambda record: record["path"])
    duplicate_job_names = {}
    for record in records:
        for job in record["jobs"]:
            duplicate_job_names.setdefault(job, []).append(record["path"])
    duplicate_job_names = {
        job: paths for job, paths in sorted(duplicate_job_names.items()) if len(paths) > 1
    }
    return {
        "schema_version": 1,
        "mode": "read_only_static_workflow_inventory",
        "workflow_count": len(records),
        "duplicate_job_names": duplicate_job_names,
        "records": records,
    }


def main() -> int:
    inventory = build_inventory()
    print(json.dumps(inventory, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
