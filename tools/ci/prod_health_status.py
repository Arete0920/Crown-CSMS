#!/usr/bin/env python3
"""Parse a CROWN health response into a safe, single-token Actions status.

Do not echo remote JSON text directly into GITHUB_OUTPUT or action source code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def classify_health(payload: Any) -> str:
    """Only explicit successful health contracts may report healthy.

    Supported API contract includes {"status": "ok", "ok": true}. Conflicting
    fields, unknown statuses, wrong types and malformed input fail closed.
    """
    if not isinstance(payload, dict):
        return "unhealthy"
    raw_status = payload.get("status")
    status = raw_status.strip().lower() if isinstance(raw_status, str) else None
    ok = payload.get("ok")
    if status in {"degraded", "warning", "warn"}:
        return "degraded"
    if status in {"healthy", "ok"} and (ok is True or ok is None):
        return "healthy"
    if status is None and ok is True and raw_status is None:
        return "healthy"
    return "unhealthy"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("unhealthy")
        return 0
    try:
        payload = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        print("unhealthy")
        return 0
    print(classify_health(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
