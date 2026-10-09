#!/usr/bin/env python3
"""Validate the integrity of CROWN's provisional DevSecOps evidence register.

This checks declared references and claim boundaries. It is NOT an operational
control test, a security attestation, or proof of the referenced control.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "config/security/devsecops_maturity_assessment.json"
EXPECTED_DOMAINS = {
    "culture", "plan_develop", "build_test",
    "release_deploy", "operate", "observe_respond",
}
ALLOWED_LEVELS = {
    "UNASSESSED", "BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT",
}
# No live-runtime or per-control source receipt has yet been independently
# adjudicated for this assessment. Expanding the states requires a reviewed
# evidence-verification implementation, not merely editing the JSON registry.
ALLOWED_SOURCE_STATES = {"DESIGNED", "IMPLEMENTED_SOURCE"}
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")


def _safe_repo_path(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        return False
    resolved_root = root.resolve()
    resolved = (resolved_root / value).resolve()
    return resolved.is_relative_to(resolved_root) and resolved.is_file()


def validate_registry(payload: object, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["register must be a JSON object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if payload.get("repository") != "Arete0920/Crown-CSMS":
        errors.append("repository identity does not match current CROWN")
    if not HEX_SHA.fullmatch(str(payload.get("source_snapshot_sha", ""))):
        errors.append("source_snapshot_sha must be an exact 40-character SHA")
    if payload.get("assessment_scope") != "repository-and-policy-evidence-only":
        errors.append("assessment_scope must retain the repository-only boundary")
    if payload.get("operational_certification") is not False:
        errors.append("operational_certification must remain false until a separately reviewed live-evidence control exists")
    if payload.get("independent_assurance") is not False:
        errors.append("independent_assurance must remain false until independently verifiable assurance exists")
    document = payload.get("document")
    if not _safe_repo_path(document, root):
        errors.append("document must be an existing repository file")

    domains = payload.get("domains")
    if not isinstance(domains, list) or len(domains) != len(EXPECTED_DOMAINS):
        errors.append("domains must contain exactly six competencies")
        return errors
    seen: set[str] = set()
    for index, domain in enumerate(domains, 1):
        prefix = f"domain {index}"
        if not isinstance(domain, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        identity = domain.get("id")
        if not isinstance(identity, str) or identity not in EXPECTED_DOMAINS:
            errors.append(f"{prefix}: unknown competency id {identity!r}")
        elif identity in seen:
            errors.append(f"{prefix}: duplicate competency id {identity!r}")
        else:
            seen.add(identity)
        if domain.get("level") not in ALLOWED_LEVELS:
            errors.append(f"{prefix}: unsupported provisional level")
        if domain.get("assessment_status") != "PROVISIONAL":
            errors.append(f"{prefix}: do not claim a verified assessment without independent assessment evidence")
        if domain.get("source_evidence_state") not in ALLOWED_SOURCE_STATES:
            errors.append(f"{prefix}: source evidence cannot silently be promoted to verified")
        if domain.get("operating_evidence_state") != "NOT_VERIFIED":
            errors.append(f"{prefix}: no live operating evidence has been validated")
        for field in ("name", "owner_role", "observed", "gap", "next_proof"):
            value = domain.get(field)
            if not isinstance(value, str) or len(value.strip()) < 12:
                errors.append(f"{prefix}: missing or insufficient {field}")
        paths = domain.get("evidence_paths")
        if not isinstance(paths, list) or not paths:
            errors.append(f"{prefix}: evidence_paths must be a nonempty list")
        else:
            if len(paths) != len(set(map(str, paths))):
                errors.append(f"{prefix}: duplicate evidence_paths")
            for path in paths:
                if not _safe_repo_path(path, root):
                    errors.append(f"{prefix}: missing/unsafe source evidence path {path!r}")
        issues = domain.get("open_issues")
        if not isinstance(issues, list) or not issues or any(
            type(value) is not int or value <= 0 for value in issues
        ):
            errors.append(f"{prefix}: open_issues must contain positive issue numbers")
    if seen != EXPECTED_DOMAINS:
        errors.append(f"competency set incomplete: {sorted(EXPECTED_DOMAINS - seen)}")
    return errors


def main() -> int:
    try:
        payload = json.loads(REGISTER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load DevSecOps register: {exc}")
        return 1
    failures = validate_registry(payload, ROOT)
    if failures:
        print("FAIL: DevSecOps evidence register integrity")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: six provisional competencies, repository evidence paths and unverified operational boundary")
    print("NOTE: reference integrity is NOT live-control, security or SOC 2 certification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
