from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out = root / "audit-artifacts" / "release-verify"
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "school": "demo-school",
        "students": [
            {"ref": "DEMO-001", "name": "Abigail Carter", "grade": "5"},
            {"ref": "DEMO-002", "name": "Samuel Reed", "grade": "8"},
        ],
        "billing_accounts": [
            {"household_ref": "HH-001", "balance": 0},
            {"household_ref": "HH-002", "balance": 125.00},
        ],
        "attendance": [
            {"student_ref": "DEMO-001", "present": True},
            {"student_ref": "DEMO-002", "present": True},
        ],
    }
    (out / "release_demo_seed_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()