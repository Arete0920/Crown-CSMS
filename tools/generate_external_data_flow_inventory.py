from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    "backend/crown_api/settings.py",
    "backend/governance/microsoft_graph.py",
    "backend/integrations/graph_client.py",
    "backend/comms/email_service.py",
    "backend/comms/teams_service.py",
    "backend/msauth/views.py",
    "docs/architecture/DATA_FLOW.md",
    ".env.example",
)

FLOW_RULES = (
    {
        "name": "Microsoft Graph",
        "patterns": (r"Microsoft Graph", r"graph\.microsoft\.com", r"MICROSOFT_TENANT_ID"),
        "purpose": "Microsoft 365 identity, email, Teams, and collaboration integration",
        "data_categories": ["identity", "authentication metadata", "communications", "documents as configured"],
        "status": "source_reference_present",
    },
    {
        "name": "Azure App Service",
        "patterns": (r"Azure App Service", r"WEBSITE_HOSTNAME", r"WEBSITE_INSTANCE_ID"),
        "purpose": "application hosting",
        "data_categories": ["application requests", "tenant context", "operational logs"],
        "status": "source_reference_present",
    },
    {
        "name": "PostgreSQL",
        "patterns": (r"PostgreSQL", r"DATABASE_URL"),
        "purpose": "primary application data storage",
        "data_categories": ["student records", "family records", "academic", "financial", "operational"],
        "status": "source_reference_present",
    },
    {
        "name": "Redis/Celery",
        "patterns": (r"Celery", r"Redis"),
        "purpose": "background task dispatch and transient queueing",
        "data_categories": ["task metadata", "application identifiers", "communications payload references"],
        "status": "source_reference_present",
    },
    {
        "name": "Sentry",
        "patterns": (r"Sentry", r"SENTRY_DSN"),
        "purpose": "error telemetry",
        "data_categories": ["error events", "request metadata", "operational diagnostics"],
        "status": "source_reference_present_unverified_runtime",
    },
    {
        "name": "Azure Key Vault",
        "patterns": (r"Azure Key Vault", r"KEY_VAULT", r"managed identity"),
        "purpose": "external secret storage and retrieval",
        "data_categories": ["secrets", "workload identity metadata", "audit events"],
        "status": "architecture_reference_present_operational_evidence_required",
    },
)

STALE_OR_DEFERRED_RULES = (
    {
        "name": "Stripe",
        "patterns": (r"Stripe", r"STRIPE_", r"stripe\.com"),
        "reason": "payment provider is not selected or authorized; references require review and must not be treated as active production flow",
    },
)


def read_sources(repo_root: Path) -> tuple[dict[str, str], list[str]]:
    sources: dict[str, str] = {}
    missing: list[str] = []
    for relative in SOURCE_PATHS:
        path = repo_root / relative
        if not path.exists():
            missing.append(relative)
            continue
        sources[relative] = path.read_text(encoding="utf-8-sig", errors="strict")
    return sources, sorted(missing)


def matching_sources(patterns: tuple[str, ...], sources: dict[str, str]) -> list[str]:
    matches = []
    for path, text in sources.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            matches.append(path)
    return sorted(matches)


def build_inventory(repo_root: Path = REPO_ROOT) -> dict:
    sources, missing_sources = read_sources(repo_root)
    records = []
    for rule in FLOW_RULES:
        evidence = matching_sources(rule["patterns"], sources)
        if evidence:
            records.append(
                {
                    "name": rule["name"],
                    "purpose": rule["purpose"],
                    "data_categories": rule["data_categories"],
                    "status": rule["status"],
                    "evidence_sources": evidence,
                    "production_active": None,
                    "contract_or_dpa_status": "not_verified",
                    "processing_location": "not_verified",
                }
            )

    stale_or_deferred = []
    for rule in STALE_OR_DEFERRED_RULES:
        evidence = matching_sources(rule["patterns"], sources)
        if evidence:
            stale_or_deferred.append(
                {
                    "name": rule["name"],
                    "reason": rule["reason"],
                    "evidence_sources": evidence,
                    "production_active": False,
                }
            )

    records.sort(key=lambda item: item["name"])
    stale_or_deferred.sort(key=lambda item: item["name"])
    failures = [f"missing source: {path}" for path in missing_sources]
    return {
        "schema_version": 1,
        "mode": "read_only_static_external_data_flow_inventory",
        "legal_determination": False,
        "production_configuration_verified": False,
        "record_count": len(records),
        "records": records,
        "stale_or_deferred_references": stale_or_deferred,
        "missing_sources": missing_sources,
        "failures": failures,
    }


def main() -> int:
    inventory = build_inventory()
    print(json.dumps(inventory, indent=2, sort_keys=True))
    return 1 if inventory["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
