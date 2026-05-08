#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

SECRET_REF_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*}}")


def collect(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    refs = sorted(set(SECRET_REF_RE.findall(text)))
    return {
        "file": str(path.relative_to(ROOT)).replace('\\', '/'),
        "secret_refs": refs,
        "secret_ref_count": len(refs),
    }


def main() -> int:
    records = [collect(p) for p in sorted(WF_DIR.glob("*.yml"))]
    secret_to_files: dict[str, list[str]] = {}
    for rec in records:
        for ref in rec["secret_refs"]:
            secret_to_files.setdefault(ref, []).append(rec["file"])

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_count": len(records),
        "unique_secret_refs": sorted(secret_to_files.keys()),
        "secret_reference_map": secret_to_files,
        "records": records,
    }

    out_file = ROOT / "workflow-secrets-inventory.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
