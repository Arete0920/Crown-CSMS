#!/usr/bin/env python3
"""Validate sanitized external secret-store operational evidence.

This tool validates evidence metadata only. It rejects fields likely to contain
secret values and never contacts Vault, Azure, or production infrastructure.
Templates require ``--allow-placeholders``; closure evidence fails on known
placeholder markers by default.
"""

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
    "secret_store",
    "runtime_identity",
    "deployment_identity",
    "audit_sample",
    "rotation_exercise",
    "break_glass_exercise",
    "approvals",
}

FORBIDDEN_KEY_FRAGMENTS = {
    "secret_value",
    "token",
    "password",
    "private_key",
    "client_secret",
    "connection_string",
    "database_url",
    "recovery_key",
    "unseal_key",
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


def validate(payload: dict[str, Any], *, allow_placeholders: bool = False) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - payload.keys())
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")

    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must equal 1.0")

    release_sha = payload.get("release_sha")
    if not isinstance(release_sha, str) or not SHA_RE.fullmatch(release_sha):
        errors.append("release_sha must be a lowercase 40-character Git SHA")
    elif not allow_placeholders and release_sha == "0" * 40:
        errors.append("release_sha cannot be the template placeholder")

    if payload.get("environment") not in {"sandbox", "staging", "production"}:
        errors.append("environment must be sandbox, staging, or production")

    secret_store = _require_dict(payload, "secret_store", errors)
    if secret_store.get("provider") not in {"azure-key-vault", "hashicorp-vault"}:
        errors.append("secret_store.provider must be azure-key-vault or hashicorp-vault")
    for field in ("resource_id_redacted", "namespace", "audit_enabled"):
        if field not in secret_store:
            errors.append(f"secret_store.{field} is required")
    if secret_store.get("audit_enabled") is not True:
        errors.append("secret_store.audit_enabled must be true")

    for identity_name in ("runtime_identity", "deployment_identity"):
        identity = _require_dict(payload, identity_name, errors)
        for field in ("principal_id_redacted", "authentication", "least_privilege", "validated_at_utc"):
            if field not in identity:
                errors.append(f"{identity_name}.{field} is required")
        if identity.get("authentication") not in {"managed-identity", "workload-identity", "oidc"}:
            errors.append(f"{identity_name}.authentication must be identity-based")
        if identity.get("least_privilege") is not True:
            errors.append(f"{identity_name}.least_privilege must be true")
        timestamp = identity.get("validated_at_utc")
        if not isinstance(timestamp, str) or not UTC_RE.fullmatch(timestamp):
            errors.append(f"{identity_name}.validated_at_utc must be UTC YYYY-MM-DDTHH:MM:SSZ")

    audit = _require_dict(payload, "audit_sample", errors)
    for field in ("timestamp_utc", "principal_redacted", "operation", "resource_redacted", "decision", "correlation_id_redacted"):
        if not audit.get(field):
            errors.append(f"audit_sample.{field} is required")
    if audit.get("decision") not in {"allow", "deny"}:
        errors.append("audit_sample.decision must be allow or deny")

    for exercise_name in ("rotation_exercise", "break_glass_exercise"):
        exercise = _require_dict(payload, exercise_name, errors)
        for field in ("exercise_id", "performed_at_utc", "result", "old_access_revoked", "evidence_reference"):
            if field not in exercise:
                errors.append(f"{exercise_name}.{field} is required")
        if exercise.get("result") not in {"pass", "fail"}:
            errors.append(f"{exercise_name}.result must be pass or fail")
        if exercise.get("old_access_revoked") is not True:
            errors.append(f"{exercise_name}.old_access_revoked must be true")
        if not allow_placeholders and "EXAMPLE" in str(exercise.get("exercise_id", "")).upper():
            errors.append(f"{exercise_name}.exercise_id cannot be a template placeholder")

    approvals = payload.get("approvals")
    if not isinstance(approvals, list) or not approvals:
        errors.append("approvals must be a non-empty array")
    else:
        for index, approval in enumerate(approvals):
            if not isinstance(approval, dict):
                errors.append(f"approvals[{index}] must be an object")
                continue
            for field in ("role", "name", "approved_at_utc", "decision"):
                if not approval.get(field):
                    errors.append(f"approvals[{index}].{field} is required")
            if approval.get("decision") not in {"approved", "rejected"}:
                errors.append(f"approvals[{index}].decision must be approved or rejected")
            if not allow_placeholders and str(approval.get("name", "")).strip().upper() == "REDACTED":
                errors.append(f"approvals[{index}].name must identify the approving person")

    for path, key, value in _walk(payload):
        normalized = key.lower().replace("-", "_")
        if any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
            errors.append(f"forbidden secret-bearing field at {path}.{key}")
        if isinstance(value, str):
            if "-----BEGIN " in value:
                errors.append(f"private key material detected at {path}.{key}")
            if value.startswith(("sk-", "ghp_", "github_pat_")):
                errors.append(f"credential-like value detected at {path}.{key}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Validate a documentation template rather than closure evidence.",
    )
    args = parser.parse_args()

    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read evidence: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("ERROR: evidence root must be an object", file=sys.stderr)
        return 2

    errors = validate(payload, allow_placeholders=args.allow_placeholders)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Secret-store operational evidence metadata is structurally valid and sanitized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
