#!/usr/bin/env python3
"""Validate recovery evidence for closure-grade use.

The base recovery validator checks structure, drill outcomes, integrity, RTO/RPO,
and sanitization. This wrapper additionally rejects documentation/example values
that must never be accepted as operational closure evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.validate_recovery_evidence import validate as validate_base


def validate_closure(payload: dict[str, Any]) -> list[str]:
    errors = list(validate_base(payload))

    release_sha = str(payload.get("release_sha", ""))
    if release_sha in {"0" * 40, "1" * 40, "2" * 40}:
        errors.append("release_sha cannot be a template placeholder")

    rollback = payload.get("rollback_drill")
    if isinstance(rollback, dict):
        if "EXAMPLE" in str(rollback.get("drill_id", "")).upper():
            errors.append("rollback_drill.drill_id cannot be a template placeholder")
        if "example" in str(rollback.get("evidence_reference", "")).lower():
            errors.append("rollback_drill.evidence_reference must identify operational evidence")
        for field in ("from_sha", "to_sha"):
            value = str(rollback.get(field, ""))
            if value in {"0" * 40, "1" * 40, "2" * 40}:
                errors.append(f"rollback_drill.{field} cannot be a template placeholder")

    restore = payload.get("restore_drill")
    if isinstance(restore, dict):
        if "EXAMPLE" in str(restore.get("drill_id", "")).upper():
            errors.append("restore_drill.drill_id cannot be a template placeholder")
        if "example" in str(restore.get("evidence_reference", "")).lower():
            errors.append("restore_drill.evidence_reference must identify operational evidence")

    objectives = payload.get("rto_rpo")
    if isinstance(objectives, dict):
        accepted_by = str(objectives.get("accepted_by", "")).strip().lower()
        if not accepted_by or "example" in accepted_by or accepted_by == "redacted":
            errors.append("rto_rpo.accepted_by must identify the accepting authority")

    operators = payload.get("operators")
    if isinstance(operators, list):
        for index, operator in enumerate(operators):
            if isinstance(operator, dict):
                name = str(operator.get("name", "")).strip().lower()
                if not name or "example" in name or name == "redacted":
                    errors.append(f"operators[{index}].name must identify the operator")

    approvals = payload.get("approvals")
    if isinstance(approvals, list):
        for index, approval in enumerate(approvals):
            if isinstance(approval, dict):
                name = str(approval.get("name", "")).strip().lower()
                if not name or "example" in name or name == "redacted":
                    errors.append(f"approvals[{index}].name must identify the approving person")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read evidence: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("ERROR: evidence root must be an object", file=sys.stderr)
        return 2

    errors = validate_closure(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Recovery closure evidence is structurally valid, sanitized, and non-template.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
