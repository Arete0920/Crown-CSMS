#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]

REQUIRED_POLICY_WORKFLOWS = [
    ".github/workflows/repository-policy.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/dependency-audit.yml",
    ".github/workflows/dashboards-build-gate.yml",
    ".github/workflows/sbom-generation.yml",
    ".github/workflows/prod-rollback-on-failure.yml",
    ".github/workflows/release-verify.yml",
]


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    policy_cmd = ["python", "tools/verify_workflow_policy.py", *REQUIRED_POLICY_WORKFLOWS]
    code, out = run(policy_cmd)

    score = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_check_passed": code == 0,
        "policy_check_output": out,
        "required_workflows": REQUIRED_POLICY_WORKFLOWS,
        "pass": code == 0,
    }

    out_file = ROOT / "release-scorecard.json"
    out_file.write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")

    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
