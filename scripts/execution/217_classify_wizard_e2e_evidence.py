from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "tests" / "e2e"
OUT_DIR = ROOT / "audit-artifacts" / "wizard-e2e-evidence" / "latest"

# Canonical production wizard scope: backend/crown_api/wizard_registry.py and
# frontend/dashboards/src/routes/wizard-manifest.js currently define 28 routes.
# The historic 50-row assessment is a broader concept inventory and must not
# force duplicate/alias/non-registered workflows to masquerade as production
# wizard certification debt.
CANONICAL_SPECS = {
    "onboarding": "onboarding_wizard_spec.ts",
    "reenrollment": "reenrollment_wizard_spec.ts",
    "billing-wizard": "billing-setup_wizard_spec.ts",
    "aid-wizard": "financial-aid_wizard_spec.ts",
    "scheduling-wizard": "scheduling_wizard_spec.ts",
    "comms-wizard": "communication_wizard_spec.ts",
    "section-assign-wizard": "section-assign_wizard_spec.ts",
    "bell-schedule-wizard": "bell-schedule_wizard_spec.ts",
    "gradebook-setup-wizard": "gradebook-setup_wizard_spec.ts",
    "attendance-rules-wizard": "attendance-rules_wizard_spec.ts",
    "enrollment-conversion-wizard": "enrollment-conversion_wizard_spec.ts",
    "invoice-run-wizard": "invoice-run_wizard_spec.ts",
    "staff-onboarding-wizard": "staff-onboarding_wizard_spec.ts",
    "fee-schedule-wizard": "fee-schedule_wizard_spec.ts",
    "academic-year-wizard": "academic-year-rollover_wizard_spec.ts",
    "enrollment-period-wizard": "enrollment-period_wizard_spec.ts",
    "grade-scale-wizard": "grade-scale_wizard_spec.ts",
    "term-structure-wizard": "term-structure_wizard_spec.ts",
    "section-scheduler-wizard": "section-scheduler_wizard_spec.ts",
    "staff-setup-wizard": "staff-roles_wizard_spec.ts",
    "course-catalog-wizard": "course-catalog_wizard_spec.ts",
    "room-setup-wizard": "rooms-setup_wizard_spec.ts",
    "promotion-wizard": "promotion-map_wizard_spec.ts",
    "student-import-wizard": "student-import_wizard_spec.ts",
    "guardian-household-wizard": "guardian-household_wizard_spec.ts",
    "section-staffing-wizard": "section-staffing_wizard_spec.ts",
    "attendance-codes-wizard": "attendance-codes_wizard_spec.ts",
    "grade-weights-wizard": "grade-weights_wizard_spec.ts",
}

TRIVIAL_PATTERNS = [
    re.compile(r"expect\(\s*true\s*\)\.toBeTruthy\(\s*\)", re.I),
    re.compile(r"expect\(\s*1\s*\)\.toBe\(\s*1\s*\)", re.I),
    re.compile(r"expect\(\s*['\"]?ok['\"]?\s*\)\.toBeTruthy\(\s*\)", re.I),
]


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def classify_text(text: str, relative_path: str) -> dict:
    compact = re.sub(r"\s+", " ", text).strip()
    uses_page = has_any(text, ("page.goto(", "page.getby", "page.locator(", "page.click(", "page.fill("))
    uses_request = has_any(text, ("request.get(", "request.post(", "request.patch(", "request.put(", "request.delete("))
    uses_api_response = has_any(text, ("waitforresponse(", "response.status(", "/api/"))
    route_mocking = has_any(text, ("page.route(", "route.fulfill(", "route.continue("))
    persistence_signal = has_any(text, ("commit", "save", "submit", "persist", "reread", "verify", "created", "updated", "delete", "post(", "patch(", "put("))
    rbac_tenant_signal = has_any(text, ("unauthorized", "forbidden", "403", "401", "tenant", "school-id", "x-school-id", "cross-school", "foreign school", "wrong school", "denied"))
    validation_signal = has_any(text, ("validation", "invalid", "required", "error", "400"))
    constant_assertion = any(pattern.search(text) for pattern in TRIVIAL_PATTERNS)
    tiny = len(compact) < 220
    no_app_interaction = not (uses_page or uses_request or uses_api_response)

    if constant_assertion and tiny and no_app_interaction:
        classification = "PLACEHOLDER"
    elif uses_page and not persistence_signal:
        classification = "ROUTE_ONLY"
    elif uses_page or uses_request or uses_api_response:
        classification = "REAL_FUNCTIONAL_CANDIDATE"
    else:
        classification = "NON_EVIDENTIARY"

    scaffold_ui = uses_page
    live_ui_api = bool((uses_page or uses_request or uses_api_response) and not route_mocking)
    backend_persistence = bool(live_ui_api and persistence_signal)
    rbac_tenant = bool(live_ui_api and rbac_tenant_signal)
    proof_backed = bool(classification == "REAL_FUNCTIONAL_CANDIDATE" and live_ui_api and backend_persistence and rbac_tenant)

    return {
        "path": relative_path,
        "classification": classification,
        "SCAFFOLD_UI": scaffold_ui,
        "LIVE_UI_API": live_ui_api,
        "BACKEND_PERSISTENCE": backend_persistence,
        "RBAC_TENANT": rbac_tenant,
        "VALIDATION": validation_signal,
        "route_mocking": route_mocking,
        "constant_assertion": constant_assertion,
        "proof_backed": proof_backed,
    }


def classify(path: Path) -> dict:
    relative = str(path.relative_to(ROOT)).replace("\\", "/")
    return classify_text(path.read_text(encoding="utf-8", errors="replace"), relative)


def canonical_rows() -> list[dict]:
    rows: list[dict] = []
    for slug, filename in CANONICAL_SPECS.items():
        path = SPEC_ROOT / filename
        if path.exists():
            row = classify(path)
        else:
            row = {
                "path": f"tests/e2e/{filename}",
                "classification": "MISSING_CANONICAL_SPEC",
                "SCAFFOLD_UI": False,
                "LIVE_UI_API": False,
                "BACKEND_PERSISTENCE": False,
                "RBAC_TENANT": False,
                "VALIDATION": False,
                "route_mocking": False,
                "constant_assertion": False,
                "proof_backed": False,
            }
        row["wizard_slug"] = slug
        row["scope"] = "CANONICAL_REQUIRED"
        rows.append(row)
    return rows


def noncanonical_rows() -> list[dict]:
    canonical_names = set(CANONICAL_SPECS.values())
    rows = []
    for path in sorted(SPEC_ROOT.glob("*_wizard_spec.ts")):
        if path.name in canonical_names:
            continue
        row = classify(path)
        row["scope"] = "NON_CANONICAL_SCOPE"
        row["proof_backed"] = False
        rows.append(row)
    return rows


def baseline_debt_count(ref: str) -> int:
    debt = 0
    for filename in CANONICAL_SPECS.values():
        relative = f"tests/e2e/{filename}"
        try:
            text = subprocess.check_output(["git", "show", f"{ref}:{relative}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            debt += 1
            continue
        row = classify_text(text, relative)
        if not row["proof_backed"]:
            debt += 1
    return debt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-placeholder", action="store_true")
    parser.add_argument("--fail-on-unverified", action="store_true")
    parser.add_argument("--baseline-ref", default="", help="fail only if canonical certification debt increases relative to this git ref")
    args = parser.parse_args()

    rows = canonical_rows()
    extras = noncanonical_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    placeholders = [row for row in rows if row["classification"] == "PLACEHOLDER"]
    missing = [row for row in rows if row["classification"] == "MISSING_CANONICAL_SPEC"]
    unverified = [row for row in rows if not row["proof_backed"]]
    baseline_count = baseline_debt_count(args.baseline_ref) if args.baseline_ref else None

    status = {
        "schema_version": 2,
        "canonical_registry_count": len(CANONICAL_SPECS),
        "canonical_spec_count": len(rows) - len(missing),
        "noncanonical_concept_spec_count": len(extras),
        "classification_counts": counts,
        "placeholder_count": len(placeholders),
        "missing_canonical_spec_count": len(missing),
        "canonical_debt_count": len(unverified),
        "baseline_canonical_debt_count": baseline_count,
        "canonical_debt_delta": None if baseline_count is None else len(unverified) - baseline_count,
        "proof_backed_count": len(rows) - len(unverified),
        "unverified_count": len(unverified),
        "all_specs_proof_backed": len(rows) == len(CANONICAL_SPECS) and not unverified,
        "evidence_classes": ["SCAFFOLD_UI", "LIVE_UI_API", "BACKEND_PERSISTENCE", "RBAC_TENANT"],
        "rows": rows,
        "noncanonical_scope_rows": extras,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "99_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Canonical Wizard E2E Evidence Classification", "",
        f"- Canonical registered wizards: {len(CANONICAL_SPECS)}",
        f"- Canonical spec files present: {status['canonical_spec_count']}",
        f"- Non-canonical/concept wizard specs dispositioned outside release gate: {len(extras)}",
        f"- Canonical placeholders: {len(placeholders)}",
        f"- Missing canonical specs: {len(missing)}",
        f"- Baseline canonical debt: {baseline_count if baseline_count is not None else 'n/a'}",
        f"- Proof-backed canonical wizards: {status['proof_backed_count']}/{len(CANONICAL_SPECS)}",
        f"- Canonical not verified: {len(unverified)}", "",
        "| Wizard | Spec | Classification | Live UI/API | Persistence | RBAC/Tenant | Proof-backed |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        summary.append(f"| `{row['wizard_slug']}` | `{row['path']}` | {row['classification']} | {str(row['LIVE_UI_API']).upper()} | {str(row['BACKEND_PERSISTENCE']).upper()} | {str(row['RBAC_TENANT']).upper()} | {str(row['proof_backed']).upper()} |")
    summary.extend(["", "## Non-canonical concept specs", "", "These files remain repository evidence for broader product concepts but are not registered production wizard routes and therefore do not create canonical wizard certification debt."])
    for row in extras:
        summary.append(f"- `{row['path']}` — NON_CANONICAL_SCOPE")
    (OUT_DIR / "00_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in status.items() if k not in {"rows", "noncanonical_scope_rows"}}, indent=2))

    if baseline_count is not None and len(unverified) > baseline_count:
        print(f"ERROR: canonical wizard debt regressed from {baseline_count} to {len(unverified)}")
        return 4
    if args.fail_on_placeholder and (placeholders or missing):
        print("ERROR: canonical wizard placeholder/missing specs remain:")
        for row in placeholders + missing:
            print(f" - {row['path']}: {row['classification']}")
        return 2
    if args.fail_on_unverified and unverified:
        print("ERROR: canonical wizards remain without required live functional evidence")
        for row in unverified:
            print(f" - {row['path']}: {row['classification']}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
