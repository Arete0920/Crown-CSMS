from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit-artifacts" / "release-manifest" / "workflow_preflight.json"
REQUIRED = {
    "dependency-audit.yml",
    "release-verify.yml",
}


def main() -> None:
    wf_dir = ROOT / ".github" / "workflows"
    files = sorted([p.name for p in wf_dir.glob("*.yml")] + [p.name for p in wf_dir.glob("*.yaml")])

    package_lock = ROOT / "frontend" / "dashboards" / "package-lock.json"

    result = {
        "workflow_files": files,
        "required_present": sorted(REQUIRED.intersection(files)),
        "missing_required": sorted(REQUIRED.difference(files)),
        "frontend_package_lock_exists": package_lock.exists(),
        "green": len(REQUIRED.difference(files)) == 0 and package_lock.exists(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()