# CROWN Historical Release Authority Index — 2026-05-29

> **Superseded governance record.** This document preserves the May 29, 2026 release-readiness framework and evidence references for historical traceability. It is not the current release authority. GitHub issue #1619 and its eight open lane issues are the sole controlling production-readiness and buyer-handoff framework. Where this document conflicts with #1619, current GitHub state, `docs/CURRENT_RELEASE_STATUS.md`, or later exact-SHA evidence, the newer authority controls.

## Historical decision

**RELEASE / PILOT / SUPERIORITY STATUS AT THIS RECORD: NO-GO UNTIL CURRENT GREEN EVIDENCE AND SIGNOFF EXIST.**

This index was the release-authority map for the May 29 full-completion and core SIS superiority initiative. It identifies historical artifacts and work that was required at that time. It must not be used to authorize a current release, close an eight-lane requirement, or substitute older evidence for current exact-SHA proof.

## Historical artifacts

| Artifact | Historical purpose | Current status |
|---|---|---|
| `docs/release/CROWN_FULL_COMPLETION_BLOCKERS_20260529.md` | May 29 module/dashboard/component/wizard blocker register | HISTORICAL EVIDENCE ONLY |
| `scripts/execution/106_crown_full_completion_truth_gate.ps1` | Full-completion truth gate for preview/sample/fallback and scope signals | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/120_crown_release_authority_meta_gate.ps1` | Meta-gate for blocking markers and runtime status JSONs | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/121_crown_dashboard_data_provenance_gate.ps1` | Dashboard widget provenance and hidden sample/fallback detector | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/130_crown_data_migration_reconciliation_gate.ps1` | Migration/import/reconciliation proof gate | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/140_crown_financial_controls_gate.ps1` | Finance, billing, payment, aid, ledger, and export control gate | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/150_crown_performance_load_gate.ps1` | Performance/load scenario gate | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `scripts/execution/160_crown_observability_incident_gate.ps1` | Observability and incident-response evidence gate | CURRENT USE REQUIRES SAME-SHA VERIFICATION |
| `.github/workflows/crown-release-authority-gates.yml` | CI workflow for the historical gate stack | CURRENT RESULTS MUST BE EVALUATED UNDER #1619 |
| `docs/release/CROWN_CORE_SIS_SUPERIORITY_GATE_20260529.md` | May 29 superiority certification standard | HISTORICAL / NO CURRENT SUPERIORITY AUTHORITY |
| `docs/release/CROWN_DASHBOARD_DATA_PROVENANCE_CONTRACT_20260529.md` | Dashboard provenance contract | HISTORICAL REQUIREMENTS CONTEXT |
| `docs/architecture/CROWN_CORE_SIS_DOMAIN_MODEL_CERTIFICATION_20260529.md` | Core SIS domain model certification register | HISTORICAL REQUIREMENTS CONTEXT |
| `docs/release/CROWN_CORE_SIS_COMPETITOR_MATRIX_20260529.csv` | 25-competitor benchmark matrix | HISTORICAL; NO CURRENT SUPERIORITY CLAIM |
| `docs/release/CROWN_CORE_SIS_MODULE_PROOF_REGISTER_20260529.csv` | Module/capability proof register | HISTORICAL EVIDENCE ONLY |
| `docs/release/CROWN_CORE_SIS_REMEDIATION_LEDGER_20260529.csv` | P0/P1 remediation ledger | HISTORICAL EVIDENCE ONLY |
| `docs/release/CROWN_FINANCIAL_CONTROLS_GATE_20260529.md` | Finance/billing/payment/aid control definition | HISTORICAL REQUIREMENTS CONTEXT |
| `docs/operations/CROWN_OBSERVABILITY_AND_INCIDENT_READINESS_20260529.md` | Monitoring and incident readiness requirements | HISTORICAL REQUIREMENTS CONTEXT |
| `docs/customer/CROWN_GO_LIVE_RUNBOOK_20260529.md` | Customer go-live execution runbook | GO-LIVE NOT APPROVED |
| `docs/compliance/CROWN_COMPLIANCE_CUSTOMER_READINESS_PACKET_20260529.md` | FERPA/COPPA/DPA/retention/support/IR/subprocessor/backup/sandbox/pilot policy packet | HISTORICAL; NOT LEGAL-SIGNED |
| `docs/compliance/CROWN_DPA_TEMPLATE_20260529.md` | Customer DPA baseline template | TEMPLATE ONLY |
| `docs/compliance/CROWN_SUBPROCESSOR_REGISTER_20260529.csv` | Subprocessor register scaffold | VENDORS UNVERIFIED/TBD |
| `docs/release/CROWN_CONTROLLED_PILOT_ENTRY_EXIT_CHECKLIST_20260529.md` | Pilot entry and exit checklist | PILOT NOT APPROVED |
| `docs/release/CROWN_FINAL_RELEASE_AUTHORITY_SIGNOFF_TEMPLATE_20260529.md` | Final signature control | TEMPLATE ONLY, NOT SIGNED |

## Historical blocker set

The May 29 record required the following evidence. These items remain useful historical context, but current acceptance criteria and closure are governed only by #1619 and its eight lanes:

1. Full-completion truth gate passes without `-AllowPreviewData`.
2. Dashboard completion gate passes with deep frontend/backend/runtime checks.
3. Dashboard data provenance gate passes for every ready dashboard/widget.
4. Backend sample/fallback payloads cannot be certified in production/full-completion mode.
5. Current CI/workflow evidence exists for reviewed branch/commit.
6. Backend tests are green.
7. Frontend tests/build/contract tests are green.
8. Playwright/runtime workflow proof is green.
9. Tenant isolation and RBAC/object authorization are green.
10. All in-scope wizards are proven end-to-end or explicitly scoped out with approved rationale.
11. Module proof register has no unresolved blocking status for in-scope certification.
12. Domain model certification has no unproven required core SIS entities.
13. Migration/import/reconciliation gate passes.
14. Financial-controls gate passes.
15. Performance/load gate passes.
16. Observability/incident-readiness gate passes.
17. Compliance/customer-readiness materials are legally and product-owner approved.
18. Actual subprocessors are confirmed.
19. Backup/restore test is complete.
20. Incident response process is tested.
21. Support access process is active and auditable.
22. Pilot entry is signed before any pilot claim.
23. Pilot exit is signed before any GA claim.
24. Founder/Product Owner final acceptance is signed.
25. Competitor matrix is evidence-backed before any superiority claim.

## Allowed status language

Use:

> CROWN remains on release-authority integrity hold pending completion of the eight-lane program in #1619, current exact-SHA proof, operational and legal readiness, and explicit final acceptance.

Do not use statements asserting:

- general availability;
- pilot approval;
- unrestricted production readiness;
- superiority to all 25 private-school SIS competitors;
- completion of all modules, dashboards, components, and wizards.

## Historical command set

The following commands are retained for engineering reference. Running them does not establish current release authority unless the resulting evidence is tied to the selected immutable SHA and reconciled through #1619.

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

Historical output locations:

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

## Current authority rule

A current GO decision requires all eight lanes under #1619 to pass on one unchanged immutable release SHA, followed by an explicit Founder/Product Owner authorization record for that exact SHA. This historical index and the unsigned May 29 template cannot authorize production, pilot entry, buyer turnover, or payment processing.
