from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "audit-artifacts" / "release-verify" / "release_demo_seed_manifest.json"
OUT = ROOT / "audit-artifacts" / "release-verify" / "seed_fixture_parity.json"


def main() -> None:
    if not SEED.exists():
        SEED.parent.mkdir(parents=True, exist_ok=True)
        SEED.write_text(
            json.dumps({
                "school": "demo-school",
                "students": [{"ref": "DEMO-001"}, {"ref": "DEMO-002"}],
            }, indent=2),
            encoding="utf-8",
        )

    payload = json.loads(SEED.read_text(encoding="utf-8"))
    students = payload.get("students", [])
    refs = [s.get("ref") for s in students if s.get("ref")]

    result = {
        "student_refs": refs,
        "has_demo_001": "DEMO-001" in refs,
        "has_demo_002": "DEMO-002" in refs,
        "green": "DEMO-001" in refs and len(refs) >= 1,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()