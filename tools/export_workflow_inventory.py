#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

NAME_RE = re.compile(r"(?m)^name:\s*(.+?)\s*$")
PERM_RE = re.compile(r"(?m)^permissions:\s*$")
CONC_RE = re.compile(r"(?m)^concurrency:\s*$")
JOBS_RE = re.compile(r"(?ms)^jobs:\s*$([\s\S]+)$")
JOB_RE = re.compile(r"(?m)^\s{2}([A-Za-z0-9_-]+):\s*$")
TIMEOUT_RE = re.compile(r"(?m)^\s{4}timeout-minutes:\s*(\d+)\s*$")
USES_RE = re.compile(r"(?m)^\s*uses:\s*([^\s#]+)")


def _is_sha_pinned(ref: str) -> bool:
    if ref.startswith("./") or ref.startswith("docker://"):
        return True
    if "@" not in ref:
        return False
    return bool(re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref))


def parse_workflow(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    jobs_block = JOBS_RE.search(text)
    jobs = JOB_RE.findall(jobs_block.group(1)) if jobs_block else []
    timeouts = TIMEOUT_RE.findall(jobs_block.group(1)) if jobs_block else []
    uses_refs = USES_RE.findall(text)

    return {
        "file": str(path.relative_to(ROOT)).replace('\\', '/'),
        "name": (NAME_RE.search(text).group(1).strip() if NAME_RE.search(text) else None),
        "has_permissions": bool(PERM_RE.search(text)),
        "has_concurrency": bool(CONC_RE.search(text)),
        "job_count": len(jobs),
        "job_names": jobs,
        "timeout_count": len(timeouts),
        "all_jobs_have_timeouts": len(jobs) == 0 or len(timeouts) >= len(jobs),
        "uses_count": len(uses_refs),
        "unpinned_uses": [u for u in uses_refs if not _is_sha_pinned(u)],
    }


def main() -> int:
    inventory = [parse_workflow(p) for p in sorted(WF_DIR.glob("*.yml"))]
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_count": len(inventory),
        "workflows": inventory,
        "summary": {
            "missing_permissions": sum(1 for w in inventory if not w["has_permissions"]),
            "missing_concurrency": sum(1 for w in inventory if not w["has_concurrency"]),
            "missing_timeouts": sum(1 for w in inventory if not w["all_jobs_have_timeouts"]),
            "unpinned_uses_total": sum(len(w["unpinned_uses"]) for w in inventory),
        },
    }

    out = ROOT / "workflow-inventory-report.json"
    out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
