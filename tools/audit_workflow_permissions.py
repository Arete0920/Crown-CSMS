#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

PERM_BLOCK_RE = re.compile(r"(?ms)^permissions:\s*$([\s\S]*?)(?:^\S|\Z)")
WRITE_RE = re.compile(r"(?m)^\s{2,}[a-zA-Z-]+:\s*write\s*$")


def parse_permissions(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    block_match = PERM_BLOCK_RE.search(text)
    block = block_match.group(1).strip().splitlines() if block_match else []
    writes = [line.strip() for line in block if WRITE_RE.match(line)]
    return {
        "file": str(path.relative_to(ROOT)).replace('\\', '/'),
        "has_permissions": bool(block_match),
        "write_scopes": writes,
        "write_scope_count": len(writes),
    }


def main() -> int:
    records = [parse_permissions(p) for p in sorted(WF_DIR.glob("*.yml"))]
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_count": len(records),
        "with_write_scopes": sum(1 for r in records if r["write_scope_count"] > 0),
        "records": records,
    }

    out_file = ROOT / "workflow-permissions-audit.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
