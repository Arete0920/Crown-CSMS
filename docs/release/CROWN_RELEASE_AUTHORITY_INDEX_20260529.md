# CROWN Release Authority Index — 2026-05-29

## Decision

**RELEASE / PILOT / SUPERIORITY STATUS: NO-GO UNTIL CURRENT GREEN EVIDENCE AND SIGNOFF EXIST.**

This index is the release-authority map for the full-completion and core SIS superiority initiative. It identifies the controlling artifacts and the exact work that must be green before CROWN can be marked GO.

## Controlling artifacts

| Artifact | Purpose | Current authority status |
|---|---|---|
| `docs/release/CROWN_FULL_COMPLETION_BLOCKERS_20260529.md` | Full module/dashboard/component/wizard blocker register | CONTROLLING NO-GO BLOCKER FILE |
| `scripts/execution/106_crown_full_completion_truth_gate.ps1` | Full-completion truth gate for preview/sample/fallback and scope signals | MUST RUN GREEN |
| `scripts/execution/120_crown_release_authority_meta_gate.ps1` | Meta-gate that fails on blocking status markers and missing/failed runtime status JSONs | MUST RUN GREEN |
| `scripts/execution/121_crown_dashboard_data_provenance_gate.ps1` | Dashboard widget provenance and hidden sample/fallback detector | MUST RUN GREEN |
| `scripts/execution/130_crown_data_migration_reconciliation_gate.ps1` | Migration/import/reconciliation proof gate | MUST RUN GREEN |
| `scripts/execution/140_crown_financial_controls_gate.ps1` | Finance, billing, payment, aid, ledger, and export control gate | MUST RUN GREEN |
| `scripts/execution/150_crown_performance_load_gate.ps1` | Performance/load scenario gate | MUST RUN GREEN |
| `scripts/execution/160_crown_observability_incident_gate.ps1` | Observability and incident-response evidence gate | MUST RUN GREEN |
| `.github/workflows/crown-release-authority-gates.yml` | CI workflow that runs the release-authority gate stack and uploads `.crown-audit` artifacts | MUST RUN GREEN |
| `docs/release/CROWN_CORE_SIS_SUPERIORITY_GATE_20260529.md` | Core SIS superiority certification standard | CONTROLLING NO-GO SUPERIORITY GATE |
| `docs/release/CROWN_DASHBOARD_DATA_PROVENANCE_CONTRACT_20260529.md` | Required dashboard provenance contract | DOCUMENTED, NOT IMPLEMENTED GREEN |
| `docs/architecture/CROWN_CORE_SIS_DOMAIN_MODEL_CERTIFICATION_20260529.md` | Core SIS domain model certification register | DOCUMENTED, NOT GREEN |
| `docs/release/CROWN_CORE_SIS_COMPETITOR_MATRIX_20260529.csv` | 25-competitor benchmark matrix | ALL ROWS NOT_CERTIFIED UNTIL PROOF EXISTS |
| `docs/release/CROWN_CORE_SIS_MODULE_PROOF_REGISTER_20260529.csv` | Module/capability proof register | MANY ROWS BLOCKED/PROOF_REQUIRED |
| `docs/release/CROWN_CORE_SIS_REMEDIATION_LEDGER_20260529.csv` | P0/P1 remediation ledger | OPEN UNTIL GATE EVIDENCE GREEN |
| `docs/release/CROWN_FINANCIAL_CONTROLS_GATE_20260529.md` | Finance/billing/payment/aid control definition | DOCUMENTED, NOT GREEN |
| `docs/operations/CROWN_OBSERVABILITY_AND_INCIDENT_READINESS_20260529.md` | Monitoring and incident readiness requirements | DOCUMENTED, NOT GREEN |
| `docs/customer/CROWN_GO_LIVE_RUNBOOK_20260529.md` | Customer go-live execution runbook | DOCUMENTED, GO-LIVE NOT APPROVED |
| `docs/compliance/CROWN_COMPLIANCE_CUSTOMER_READINESS_PACKET_20260529.md` | FERPA/COPPA/DPA/retention/support/IR/subprocessor/backup/sandbox/pilot policy packet | DOCUMENTED, NOT LEGAL-SIGNED |
| `docs/compliance/CROWN_DPA_TEMPLATE_20260529.md` | Customer DPA baseline template | TEMPLATE ONLY |
| `docs/compliance/CROWN_SUBPROCESSOR_REGISTER_20260529.csv` | Subprocessor register scaffold | VENDORS UNVERIFIED/TBD |
| `docs/release/CROWN_CONTROLLED_PILOT_ENTRY_EXIT_CHECKLIST_20260529.md` | Pilot entry and exit checklist | PILOT NOT APPROVED |
| `docs/release/CROWN_FINAL_RELEASE_AUTHORITY_SIGNOFF_TEMPLATE_20260529.md` | Final signature control | TEMPLATE ONLY, NOT SIGNED |

## Current non-negotiable blockers

CROWN remains NO-GO until all of the following are resolved with current evidence:

1. Full-completion truth gate passes without `-AllowPreviewData`.
2. Dashboard completion gate passes with deep frontend/backend/runtime checks.
3. Dashboard data provenance gate passes for every ready dashboard/widget.
4. Backend sample/fallback payloads cannot be certified in production/full-completion mode.
5. Current CI/workflow evidence exists for reviewed branch/commit.
6. Backend tests are green.
7. Frontend tests/build/contract tests are green.
8. Playwright/runtime workflow proof is green.
9. Tenant isolation and RBAC/object authorization are green.
10. All 29 wizards are proven end-to-end or explicitly scoped out with approved rationale.
11. Module proof register has no `BLOCKED`, `PROOF_REQUIRED`, `UNKNOWN`, `IN_PROGRESS`, or `NOT_CERTIFIED` rows for in-scope certification.
12. Domain model certification has no unproven required core SIS entities.
13. Migration/import/reconciliation gate passes.
14. Financial-controls gate passes.
15. Performance/load gate passes.
16. Observability/incident-readiness gate passes.
17. Compliance/customer-readiness packet is legally/product-owner approved.
18. Actual subprocessors are confirmed.
19. Backup/restore test is complete.
20. Incident response process is tested.
21. Support access process is active and auditable.
22. Pilot entry is signed before any pilot claim.
23. Pilot exit is signed before any GA claim.
24. Founder/Product Owner final acceptance is signed.
25. Competitor matrix is evidence-backed before any superiority claim.

## Allowed status language today

Use:

> CROWN remains on release-authority integrity hold pending current proof, compliance/customer readiness, pilot-entry proof, and final acceptance.

Do not use:

- CROWN is GA.
- CROWN is pilot-approved.
- CROWN is unrestricted-production ready.
- CROWN is superior to all 25 private-school SIS competitors.
- All CROWN modules, dashboards, components, and wizards are complete.

## Completion command set

From repository root in a runtime environment with required dependencies and secrets/tokens configured:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\execution\106_crown_full_completion_truth_gate.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\execution\121_crown_dashboard_data_provenance_gate.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\execution\130_crown_data_migration_reconciliation_gate.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\execution\140_crown_financial_controls_gate.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\execution\150_crown_performance_load_gate.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\execution\160_crown_observability_incident_gate.ps1

$env:CROWN_105_RUN_95_BASELINE = "1"
$env:CROWN_105_RUN_95_DEEP = "1"
$env:CROWN_105_RUN_HEAVY_FRONTEND = "1"
$env:CROWN_105_RUN_BACKEND_PYTEST = "1"
$env:CROWN_DEMO_TOKEN = "<valid token>"
powershell -ExecutionPolicy Bypass -File .\scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep

powershell -ExecutionPolicy Bypass -File .\scripts\execution\120_crown_release_authority_meta_gate.ps1
```

Required green output locations:

```text
.crown-audit\full-completion-truth\latest\00_SUMMARY.md
.crown-audit\full-completion-truth\latest\99_STATUS.json
.crown-audit\dashboard-provenance\latest\00_SUMMARY.md
.crown-audit\dashboard-provenance\latest\99_STATUS.json
.crown-audit\dashboard-completion\latest\00_SUMMARY.md
.crown-audit\dashboard-completion\latest\99_STATUS.json
.crown-audit\data-migration\latest\00_SUMMARY.md
.crown-audit\data-migration\latest\99_STATUS.json
.crown-audit\financial-controls\latest\00_SUMMARY.md
.crown-audit\financial-controls\latest\99_STATUS.json
.crown-audit\performance\latest\00_SUMMARY.md
.crown-audit\performance\latest\99_STATUS.json
.crown-audit\observability\latest\00_SUMMARY.md
.crown-audit\observability\latest\99_STATUS.json
.crown-audit\release-authority\latest\00_SUMMARY.md
.crown-audit\release-authority\latest\99_STATUS.json
```

## Final release authority rule

A GO decision requires signed approval in `docs/release/CROWN_FINAL_RELEASE_AUTHORITY_SIGNOFF_TEMPLATE_20260529.md` or a later superseding signed release authority document, with all evidence current to the approved branch/commit.
