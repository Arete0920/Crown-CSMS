from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    "docs/compliance/RETENTION_POLICY.md",
    "backend/core/models_retention.py",
    "backend/core/services/retention_service.py",
    "backend/core/tasks.py",
    "backend/apps/compliance/management/commands/compliance_retention_review.py",
)


def read_sources(repo_root: Path) -> tuple[dict[str, str], list[str]]:
    sources = {}
    missing = []
    for relative in SOURCE_PATHS:
        path = repo_root / relative
        if not path.exists():
            missing.append(relative)
            continue
        sources[relative] = path.read_text(encoding="utf-8-sig", errors="strict")
    return sources, sorted(missing)


def contains(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is not None


def build_inventory(repo_root: Path = REPO_ROOT) -> dict:
    sources, missing_sources = read_sources(repo_root)
    claims_doc = sources.get("docs/compliance/RETENTION_POLICY.md", "")
    service = sources.get("backend/core/services/retention_service.py", "")
    model = sources.get("backend/core/models_retention.py", "")

    observations = {
        "enforcement_claim_present": contains(r"retention enforcement is executed", claims_doc),
        "soft_delete_policy_claim_present": contains(r"soft-delete first", claims_doc),
        "direct_queryset_delete_present": contains(r"\.filter\([^\n]+\)\.delete\(\)", service),
        "legal_hold_field_present": contains(r"legal_hold\s*=\s*models\.BooleanField", model),
        "purge_audit_model_present": contains(r"class\s+RetentionPurgeAudit", model),
        "dry_run_control_present": contains(r"dry[_ -]?run", service),
        "approval_gate_present": contains(r"approv|authoriz", service),
        "tenant_scope_guard_present": contains(r"school_id|tenant", service),
        "batch_limit_present": contains(r"batch|limit|chunk", service),
    }

    contradictions = []
    if observations["soft_delete_policy_claim_present"] and observations["direct_queryset_delete_present"]:
        contradictions.append("policy claims soft-delete first while service performs direct queryset deletion")

    missing_safeguards = []
    for key, label in (
        ("dry_run_control_present", "dry-run control not evidenced in retention service"),
        ("approval_gate_present", "explicit approval or authorization gate not evidenced in retention service"),
        ("tenant_scope_guard_present", "tenant-scoping guard not evidenced in retention service"),
        ("batch_limit_present", "bounded batch or chunk control not evidenced in retention service"),
    ):
        if not observations[key]:
            missing_safeguards.append(label)

    failures = [f"missing source: {path}" for path in missing_sources]
    return {
        "schema_version": 1,
        "mode": "read_only_static_retention_control_inventory",
        "legal_determination": False,
        "runtime_configuration_verified": False,
        "purge_execution_performed": False,
        "production_mutation_performed": False,
        "observations": observations,
        "contradictions": sorted(contradictions),
        "missing_safeguards": sorted(missing_safeguards),
        "missing_sources": missing_sources,
        "failures": failures,
    }


def main() -> int:
    inventory = build_inventory()
    print(json.dumps(inventory, indent=2, sort_keys=True))
    return 1 if inventory["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
