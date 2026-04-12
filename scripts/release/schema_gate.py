from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "audit-artifacts" / "release-verify" / "schema_w002_summary.json"
BUDGET = ROOT / "docs" / "release" / "SCHEMA_W002_BUDGET.json"
OUT = ROOT / "audit-artifacts" / "release-verify" / "schema_gate.json"


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))

    current = int(summary["total_w002"])
    current_max = int(budget["current_max"])
    passed = current <= current_max

    payload = {
        "current_w002": current,
        "budget_current_max": current_max,
        "budget_next_target": int(budget.get("next_target", 0)),
        "passed": passed,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not passed:
        print(f"W002 gate failed: current={current} max={current_max}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()