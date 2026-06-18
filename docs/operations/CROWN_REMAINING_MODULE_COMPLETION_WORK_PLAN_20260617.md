# CROWN Remaining Module Completion Work Plan

Generated: 2026-06-17
Branch: docs/remaining-module-completion-workplan-20260617
Base SHA: 3a0a08837c701200429a8903b34a1ebb4c7e9812
Scope: planning and evidence inventory only

## Purpose

This document converts the current remaining-module inventory into an executable completion plan for CROWN proof work. It is intended to guide ChatGPT, GitHub connector, VS Code, Copilot, and human contributors without creating product-completion claims.

## Current Canonical Boundary

Main currently contains the merged Module 025 proof PR #1062. Canonical reconciliation PR #1063 is still open at the time this plan was created.

Until PR #1063 merges, the canonical main scorecard may still show Module 025 as not fully reconciled even though proof has merged. After PR #1063 merges, the remaining NOT_PROVEN module set is expected to be:

1. Module 026: After-School & Extended Care
2. Module 030: Student Portal
3. Module 031: Administrative Portal
4. Module 037: Advanced Discipline Workflows
5. Module 039: Christian Formation & Tracking
6. Module 050: Business Intelligence Suite

## Non-Claims

This plan does not certify product completion, dashboard live-data status, wizard functional-flow status, deployment status, or independent review.

## Operating Rules

1. Use one proof branch per module.
2. Use a separate reconciliation branch after each proof branch merges.
3. Keep proof implementation separate from canonical scorecard edits.
4. Do not mutate main directly.
5. Do not combine unrelated modules in a single proof PR.
6. Do not touch auth, RBAC, tenant isolation, migrations, workflows, packages, or cloud resources unless explicitly scoped.
7. Every proof PR needs raw test output and an evidence packet.
8. Every reconciliation PR must cite the merged proof PR and only update canonical matrix/scorecard artifacts.
9. Independent review remains required before merge decisions.

## GitHub Connector Work Plan

The GitHub connector can safely perform these actions:

### Connector Task 1: Monitor and report PR state

- Monitor PR #1061 process-hardening checks.
- Monitor PR #1063 Module 025 reconciliation checks.
- Report state, draft status, mergeability, head SHA, changed files, pending count, failed count, and cancelled count.
- Do not merge while checks are pending, failed, cancelled, stale, action-required, or on a moved head.

### Connector Task 2: Maintain planning artifacts

- Keep this work plan current as proof lanes merge.
- Add work-order files on new proof branches.
- Add docs-only inventories when local evidence packets are committed.

### Connector Task 3: Create proof lane branches

Create these only when main has been synced and the prior reconciliation state is clear:

- feat/module-026-aftercare-proof-20260617
- feat/module-039-christian-formation-proof-20260617
- feat/module-030-student-portal-proof-20260617
- feat/module-031-admin-portal-proof-20260617
- feat/module-037-advanced-discipline-proof-20260617
- feat/module-050-business-intelligence-proof-20260617

### Connector Task 4: Open PRs with bounded descriptions

Each proof PR body must include:

- module number and name
- canonical blocker
- exact changed files
- evidence packet path
- focused validation commands
- result summary
- non-scope statement
- independent review required

### Connector Task 5: Open reconciliation PRs after proof merges

Each reconciliation PR should update only:

- audit-artifacts/module-completion/current/01_module_matrix_expanded.csv
- audit-artifacts/module-completion/current/05_completion_scorecard.md

Exception only if a generated index or evidence pointer file is explicitly required.

## VS Code / Local Work Plan

VS Code and Copilot should perform local repo operations, tests, and implementation. The local lane should never assume connector search is complete enough for implementation. Run the inventory script before editing.

## Remaining Module Execution Order

### 1. Module 026: After-School & Extended Care

Reason for priority: existing aftercare implementation is substantial and includes models, API, services, URLs, frontend surfaces, seed files, and a starter evidence test.

Known surfaces:

- backend/aftercare/models.py
- backend/aftercare/api.py
- backend/aftercare/services.py
- backend/aftercare/urls.py
- backend/aftercare/wizard_api.py
- backend/aftercare/seed.py
- backend/tests/test_51x51_evidence_026_aftercare.py
- frontend/dashboards/src/api/aftercareApi.js
- frontend/dashboards/src/pages/AftercareRosterPage.jsx
- frontend/dashboards/src/pages/wizards/AftercareSetupWizard.jsx

Proof target:

- enrollment creation/listing
- day-of-week roster filtering
- inactive/out-of-date enrollment exclusion
- unauthorized/forbidden behavior
- tenant/school isolation
- check-in/check-out lifecycle
- late-fee calculation
- monthly billing idempotency
- incident/discipline hook behavior where supported

Expected proof file:

- backend/tests/test_51x51_evidence_026_aftercare.py

Evidence packet:

- audit-artifacts/module-completion/module-026-aftercare/<timestamp>/

### 2. Module 039: Christian Formation & Tracking

Reason for priority: strong existing spiritual-life and formation model/service surface exists.

Known surfaces:

- backend/spiritual_life/models.py
- backend/spiritual_life/formation_models.py
- backend/spiritual_life/services.py
- frontend/dashboards/src/config/dashboardTemplates/spiritualLifeDashboard.js

Proof target:

- spiritual profile one-per-school/student
- spiritual assessment score aggregation
- portrait/domain rubric records
- formation artifacts as portfolio evidence
- devotional/worldview/campaign links
- tenant isolation across formation records
- sensitive pastoral-note boundary
- spiritual-life dashboard live DB aggregation

Expected proof file:

- backend/tests/test_51x51_evidence_039_christian_formation.py

Evidence packet:

- audit-artifacts/module-completion/module-039-christian-formation/<timestamp>/

### 3. Module 030: Student Portal

Reason for order: endpoint and frontend template exist, but proof must establish student account and enrollment visibility.

Known surfaces:

- frontend/dashboards/src/config/dashboardTemplates/studentDashboard.js
- backend/crown_api/metrics_views.py
- backend/crown_api/api_urls.py
- backend/crown_api/views_students.py
- backend/crown_api/views_academics.py
- backend/crown_api/views_scheduling.py

Proof target:

- student.view permission
- student metrics endpoint contract
- student account/detail access
- enrollment/schedule/grades view
- blocked cross-student access
- blocked cross-tenant access
- frontend dashboard route/API alignment

Expected proof file:

- backend/tests/test_51x51_evidence_030_student_portal.py

Evidence packet:

- audit-artifacts/module-completion/module-030-student-portal/<timestamp>/

### 4. Module 031: Administrative Portal

Reason for order: admin metrics endpoint exists, but likely includes static values. Proof must avoid overstating operational completeness.

Known surfaces:

- backend/crown_api/metrics_views.py
- backend/crown_api/api_urls.py
- frontend dashboard registry/templates if local inventory finds admin surfaces

Proof target:

- admin.view permission
- forbidden non-admin behavior
- admin oversight endpoint contract
- workspace keys for enrollment, attendance, discipline, messages, billing, and alerts
- tenant/school scoping where DB-backed
- static-data boundary explicitly tested or replaced with live queries if required by proof scope

Expected proof file:

- backend/tests/test_51x51_evidence_031_administrative_portal.py

Evidence packet:

- audit-artifacts/module-completion/module-031-administrative-portal/<timestamp>/

### 5. Module 037: Advanced Discipline Workflows

Reason for order: existing adjacent discipline tests appear metadata-like. Appeal and retention behavior may require new implementation.

Known adjacent surfaces:

- backend/tests/test_51x51_evidence_22_student_care___discipline_summary.py
- backend/tests/test_51x51_evidence_38_extended_discipline_workflows.py
- backend/crown_api/metrics_views.py counseling metrics
- backend discipline app surfaces from local inventory

Proof target:

- appeal submission lifecycle
- appeal decision lifecycle
- data retention policy evaluation
- audit trail or immutable history
- sensitive record access boundaries
- tenant/school isolation
- parent/admin review boundaries where implemented

Expected proof file:

- backend/tests/test_51x51_evidence_037_advanced_discipline.py

Evidence packet:

- audit-artifacts/module-completion/module-037-advanced-discipline/<timestamp>/

### 6. Module 050: Business Intelligence Suite

Reason for final position: highest uncertainty. Connector search did not find a clear BI/data-warehouse implementation surface.

Known adjacent surfaces:

- backend/crown_api/metrics_views.py
- scripts/execution/136_fast_mode_51x51_audit.ps1
- scripts/execution/136_crown_51x51_module_integrity_audit.ps1
- reporting/export evidence files from older release-audit paths

Proof target:

- report definition or warehouse contract
- tenant-scoped aggregate correctness
- export/report endpoint permissions
- no cross-tenant leakage
- deterministic seeded report data
- empty-state behavior
- static dashboard metrics not counted as BI proof

Expected proof file:

- backend/tests/test_51x51_evidence_050_business_intelligence.py

Evidence packet:

- audit-artifacts/module-completion/module-050-business-intelligence/<timestamp>/

## Required Proof Packet Contents

Each module packet should contain:

- 00_prechange_packet.txt
- 01_inventory.txt
- 02_changed_files.txt
- 03_validation_output.txt
- 04_git_diff_stat.txt
- 05_decision.md
- evidence.manifest.json

## Module Completion Definition

A module remains NOT_PROVEN until all are true:

1. proof branch merged
2. focused tests pass
3. evidence packet exists
4. changed files are scoped
5. canonical reconciliation PR merges

## Command Discipline

Use local VS Code for inventory, implementation, and tests. Use GitHub connector for remote verification, branch/PR metadata, and docs-only planning changes.

## Next Immediate Actions

1. Poll PR #1063 and do not merge unless checks are settled and review obligations are handled.
2. Run the remaining-six local inventory script from VS Code.
3. Open Module 026 proof lane from current main.
4. Add hardening tests to existing Module 026 aftercare proof file.
5. Commit and open a bounded Module 026 proof PR.
6. After merge, open Module 026 canonical reconciliation PR.
