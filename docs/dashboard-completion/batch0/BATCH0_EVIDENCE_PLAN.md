# Batch 0 Dashboard Evidence Plan

Status: preparation only, not certification.

This plan starts the first real dashboard completion lane for the three control dashboards:

- `dashboard-certification-center`
- `release-reliability`
- `compliance-audit`

## Non-claims

This lane does not certify any dashboard, does not update the certification matrix, does not mark sandbox ready, and does not approve pilot, production, or release GO.

## Completion standard

Each dashboard remains incomplete until every required proof item exists and an independent reviewer records approval.

Required proof packet files for each dashboard:

1. `01_contract.md`
2. `02_backend_summary_service_reference.txt`
3. `03_api_route_reference.txt`
4. `04_permission_tests.txt`
5. `05_tenant_tests.txt`
6. `06_frontend_render_test.txt`
7. `07_playwright_runtime_proof.txt`
8. `08_screenshot_or_trace_artifact.txt`
9. `09_payload_sample_redacted.json`
10. `10_independent_review.md`
11. `11_matrix_update.diff`

## Batch 0 dashboard intent

### dashboard-certification-center

Purpose: show dashboard certification state, blocked requirements, and evidence status without promoting any dashboard by implication.

Minimum evidence required:

- Reads certification state from the canonical dashboard state register or API-backed equivalent.
- Displays dashboard totals, certified count, blocked count, and per-dashboard missing evidence.
- Does not display CERTIFIED unless the canonical matrix/state says CERTIFIED.
- Permission proof covers platform certification roles and denial for unauthorized roles.
- Tenant proof confirms cross-tenant state leakage is denied.
- Runtime proof includes browser render, core metrics visible, and no console/runtime errors.

### release-reliability

Purpose: show release gate reliability, current NO-GO posture, validation status, and unresolved blockers.

Minimum evidence required:

- Reads current release status from canonical source or API-backed equivalent.
- Displays release decision, blocker counts, validation recency, and gate status.
- Does not present GO unless the canonical release authority says GO.
- Permission proof covers platform/release roles and denial for unauthorized roles.
- Tenant proof confirms release metadata exposure is correctly scoped.
- Runtime proof includes browser render, key gate cards visible, and no console/runtime errors.

### compliance-audit

Purpose: show audit posture, compliance checks, evidence freshness, and unresolved audit gaps.

Minimum evidence required:

- Reads audit/compliance data from canonical source or API-backed equivalent.
- Displays evidence freshness, open audit gaps, policy/gate status, and compliance tasks.
- Does not imply compliance completion without explicit reviewed evidence.
- Permission proof covers compliance roles and denial for unauthorized roles.
- Tenant proof confirms audit data isolation across tenants.
- Runtime proof includes browser render, compliance summary visible, and no console/runtime errors.

## VS Code execution sequence

Run the scaffold generator from a clean worktree for this branch:

```powershell
$ErrorActionPreference = 'Stop'
$WT = 'C:\Users\JMega\OneDrive\Desktop\Crown2026_worktrees\pr1121_dashboard_batch0_evidence_prep_20260619'
Set-Location $WT
python scripts/dashboard_batch0_evidence_scaffold.py --output-root audit-artifacts/dashboard-completion/batch0-evidence
```

Then inspect generated packet directories. Do not commit generated proof packets until the files contain real evidence.

## First implementation target

Start with `dashboard-certification-center` because it is the evidence-control dashboard. It should make later certification work easier by exposing what is missing and what is already proven.
