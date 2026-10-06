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

    current = int(summary["unique_schema_errors"])
    current_max = int(budget["current_max"])
    goal = int(budget.get("goal", 0))
    export_ok = int(summary.get("schema_export_returncode", 1)) == 0
    passed = export_ok and current <= current_max
    production_ready = export_ok and current <= goal

    payload = {
        "metric": "unique_schema_generation_errors",
        "current": current,
        "budget_current_max": current_max,
        "budget_next_target": int(budget.get("next_target", 0)),
        "goal": goal,
        "schema_export_ok": export_ok,
        "passed": passed,
        "production_ready": production_ready,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not passed:
        print(
            f"Schema error ratchet failed: current={current} max={current_max} export_ok={export_ok}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not production_ready:
        print(
            f"Schema production readiness remains blocked: current={current} goal={goal}.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
