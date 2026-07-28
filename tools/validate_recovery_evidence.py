#!/usr/bin/env python3
"""Validate sanitized rollback and restore operational evidence metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "release_sha",
    "environment",
    "rollback_drill",
    "restore_drill",
    "integrity_validation",
    "rto_rpo",
    "operators",
    "approvals",
}

FORBIDDEN_KEY_FRAGMENTS = {
    "password",
    "secret",
    "token",
    "private_key",
    "connection_string",
    "database_url",
    "backup_key",
    "credential",
}

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path, str(key), child
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _require_dict(payload: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def _require_utc(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        errors.append(f"{field} must be UTC YYYY-MM-DDTHH:MM:SSZ")


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - payload.keys())
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")

    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must equal 1.0")

    release_sha = payload.get("release_sha")
    if not isinstance(release_sha, str) or not SHA_RE.fullmatch(release_sha):
        errors.append("release_sha must be a lowercase 40-character Git SHA")

    if payload.get("environment") not in {"sandbox", "staging", "production"}:
        errors.append("environment must be sandbox, staging, or production")

    rollback = _require_dict(payload, "rollback_drill", errors)
    for field in (
        "drill_id",
        "started_at_utc",
        "completed_at_utc",
        "from_sha",
        "to_sha",
        "trigger",
        "result",
        "health_validation",
        "tenant_validation",
        "evidence_reference",
    ):
        if field not in rollback:
            errors.append(f"rollback_drill.{field} is required")
    _require_utc(rollback.get("started_at_utc"), "rollback_drill.started_at_utc", errors)
    _require_utc(rollback.get("completed_at_utc"), "rollback_drill.completed_at_utc", errors)
    for field in ("from_sha", "to_sha"):
        value = rollback.get(field)
        if not isinstance(value, str) or not SHA_RE.fullmatch(value):
            errors.append(f"rollback_drill.{field} must be a lowercase 40-character Git SHA")
    if rollback.get("result") != "pass":
        errors.append("rollback_drill.result must be pass")
    if rollback.get("health_validation") is not True:
        errors.append("rollback_drill.health_validation must be true")
    if rollback.get("tenant_validation") is not True:
        errors.append("rollback_drill.tenant_validation must be true")

    restore = _require_dict(payload, "restore_drill", errors)
    for field in (
        "drill_id",
        "started_at_utc",
        "completed_at_utc",
        "backup_reference_redacted",
        "restore_target_redacted",
        "isolated_environment",
        "result",
        "evidence_reference",
    ):
        if field not in restore:
            errors.append(f"restore_drill.{field} is required")
    _require_utc(restore.get("started_at_utc"), "restore_drill.started_at_utc", errors)
    _require_utc(restore.get("completed_at_utc"), "restore_drill.completed_at_utc", errors)
    if restore.get("isolated_environment") is not True:
        errors.append("restore_drill.isolated_environment must be true")
    if restore.get("result") != "pass":
        errors.append("restore_drill.result must be pass")

    integrity = _require_dict(payload, "integrity_validation", errors)
    for field in (
        "tenant_count_checked",
        "record_count_checked",
        "cross_tenant_anomalies",
        "missing_records",
        "unexpected_records",
        "result",
    ):
        if field not in integrity:
            errors.append(f"integrity_validation.{field} is required")
    for field in ("tenant_count_checked", "record_count_checked"):
        value = integrity.get(field)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"integrity_validation.{field} must be a positive integer")
    for field in ("cross_tenant_anomalies", "missing_records", "unexpected_records"):
        if integrity.get(field) != 0:
            errors.append(f"integrity_validation.{field} must equal 0")
    if integrity.get("result") != "pass":
        errors.append("integrity_validation.result must be pass")

    objectives = _require_dict(payload, "rto_rpo", errors)
    for field in (
        "measured_rto_minutes",
        "accepted_rto_minutes",
        "measured_rpo_minutes",
        "accepted_rpo_minutes",
        "accepted_by",
    ):
        if field not in objectives:
            errors.append(f"rto_rpo.{field} is required")
    for measured, accepted, label in (
        (objectives.get("measured_rto_minutes"), objectives.get("accepted_rto_minutes"), "RTO"),
        (objectives.get("measured_rpo_minutes"), objectives.get("accepted_rpo_minutes"), "RPO"),
    ):
        if not isinstance(measured, (int, float)) or measured < 0:
            errors.append(f"rto_rpo measured {label} must be a non-negative number")
        if not isinstance(accepted, (int, float)) or accepted < 0:
            errors.append(f"rto_rpo accepted {label} must be a non-negative number")
        if isinstance(measured, (int, float)) and isinstance(accepted, (int, float)) and measured > accepted:
            errors.append(f"measured {label} exceeds accepted {label}")

    operators = payload.get("operators")
    if not isinstance(operators, list) or not operators:
        errors.append("operators must be a non-empty array")
    else:
        for index, operator in enumerate(operators):
            if not isinstance(operator, dict):
                errors.append(f"operators[{index}] must be an object")
                continue
            for field in ("name", "role"):
                if not operator.get(field):
                    errors.append(f"operators[{index}].{field} is required")

    approvals = payload.get("approvals")
    if not isinstance(approvals, list) or not approvals:
        errors.append("approvals must be a non-empty array")
    else:
        for index, approval in enumerate(approvals):
            if not isinstance(approval, dict):
                errors.append(f"approvals[{index}] must be an object")
                continue
            for field in ("name", "role", "approved_at_utc", "decision"):
                if not approval.get(field):
                    errors.append(f"approvals[{index}].{field} is required")
            _require_utc(approval.get("approved_at_utc"), f"approvals[{index}].approved_at_utc", errors)
            if approval.get("decision") != "approved":
                errors.append(f"approvals[{index}].decision must be approved")

    for path, key, value in _walk(payload):
        normalized = key.lower().replace("-", "_")
        if any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
            errors.append(f"forbidden credential-bearing field at {path}.{key}")
        if isinstance(value, str):
            if "-----BEGIN " in value:
                errors.append(f"private key material detected at {path}.{key}")
            if value.startswith(("sk-", "ghp_", "github_pat_")):
                errors.append(f"credential-like value detected at {path}.{key}")

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

    errors = validate(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Recovery operational evidence metadata is structurally valid and sanitized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
