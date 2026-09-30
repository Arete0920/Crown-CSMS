#!/usr/bin/env python3
"""Repository maturity gate: verify the 25 hardening controls and critical truth boundaries."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MATRIX = ROOT / "docs/engineering/REPOSITORY_MATURITY_CONTROL_MATRIX.json"
ENDPOINTS = ROOT / "docs/security/ENDPOINT_SECURITY_MANIFEST.json"
JOURNEYS = ROOT / "docs/engineering/CRITICAL_BUSINESS_JOURNEYS.json"
INTEGRATIONS = ROOT / "docs/engineering/INTEGRATION_CAPABILITY_REGISTRY.json"
RETIREMENT = ROOT / "docs/engineering/COMPATIBILITY_RETIREMENT_LEDGER.json"


def fail(message: str) -> None:
    raise SystemExit(f"Repository maturity gate: FAIL: {message}")


def load_json(path: Path):
    if not path.exists():
        fail(f"missing required control artifact: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def require_text(path: str, *needles: str) -> None:
    target = ROOT / path
    if not target.exists():
        fail(f"missing implementation evidence: {path}")
    text = target.read_text(encoding="utf-8", errors="replace")
    for needle in needles:
        if needle not in text:
            fail(f"{path} missing required truth boundary: {needle}")


def main() -> int:
    matrix = load_json(MATRIX)
    controls = matrix.get("controls") or []
    ids = [item.get("id") for item in controls]
    if ids != list(range(1, 26)):
        fail(f"control ids must be exactly 1..25, found {ids}")

    allowed_statuses = {"enforced", "existing", "strengthened", "scheduled"}
    for item in controls:
        if item.get("status") not in allowed_statuses:
            fail(f"control {item.get('id')} has unsupported status {item.get('status')!r}")
        evidence = item.get("evidence") or []
        if not evidence:
            fail(f"control {item.get('id')} has no evidence")
        for rel in evidence:
            if not (ROOT / rel).exists():
                fail(f"control {item.get('id')} evidence missing: {rel}")

    endpoint_doc = load_json(ENDPOINTS)
    prefixes = [row.get("prefix") for row in endpoint_doc.get("classes", [])]
    if not prefixes or len(prefixes) != len(set(prefixes)):
        fail("endpoint security manifest must contain unique classified prefixes")
    if not any(row.get("classification") == "privileged_mutation" for row in endpoint_doc.get("classes", [])):
        fail("endpoint security manifest lacks privileged mutation classification")
    if not any(row.get("classification") == "public_token_bound" for row in endpoint_doc.get("classes", [])):
        fail("endpoint security manifest lacks token-bound public classification")

    journey_doc = load_json(JOURNEYS)
    journeys = journey_doc.get("journeys") or []
    if len(journeys) < 10:
        fail("critical business journey matrix is too small")
    for journey in journeys:
        if journey.get("criticality") == "P0" and not journey.get("proof"):
            fail(f"P0 journey {journey.get('id')} has no proof owner")
        if not journey.get("outcome"):
            fail(f"journey {journey.get('id')} has no business outcome")

    integration_doc = load_json(INTEGRATIONS)
    states = set(integration_doc.get("states") or [])
    if states != {"configured", "healthy", "degraded", "disabled", "unsupported"}:
        fail("integration capability states must preserve the five-state truth model")
    for capability in integration_doc.get("capabilities", []):
        if not capability.get("runtime_contract"):
            fail(f"integration capability {capability.get('capability')} lacks runtime contract")

    retirement_doc = load_json(RETIREMENT)
    for entry in retirement_doc.get("entries", []):
        for key in ("owner", "replacement", "deletion_condition", "status"):
            if not str(entry.get(key) or "").strip():
                fail(f"compatibility entry {entry.get('surface')} missing {key}")

    # Concrete truth boundaries. These are intentionally narrow and fail closed.
    require_text(
        "backend/crown_api/metrics_views.py",
        "def _is_production_runtime",
        "def _sample_metrics_allowed",
        "Live metrics are not configured for this dashboard.",
    )
    require_text(
        "backend/crown_api/tenant.py",
        "def principal_can_select_tenant",
        "principal_can_override_tenant",
    )
    require_text(
        "backend/market_intelligence/services.py",
        'missing.append("source_provenance")',
    )
    require_text(
        "backend/survey_sentiment/views.py",
        "PUBLIC_SURVEY_RATE_LIMIT",
        "public_expires_at__gt=timezone.now()",
        "Too many submissions.",
    )
    require_text(
        "backend/comms/tasks.py",
        "UnsupportedOutboxChannel",
        "STATUS_DEAD",
        "send_sms_to_number",
    )
    require_text(
        "scripts/ci/external_reference_hygiene.py",
        "PROHIBITED_FINGERPRINTS",
        "EXCLUDED_FILENAMES",
    )

    # Do not permit a silent catch in the strategic evidence builder.
    market_text = (ROOT / "backend/market_intelligence/services.py").read_text(encoding="utf-8")
    if re.search(r"except\s+Exception\s*:\s*(?:#.*\n\s*)?pass\b", market_text):
        fail("market intelligence contains a silent broad exception fallback")

    print("Repository maturity gate: PASS (25 controls + truth boundaries verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
