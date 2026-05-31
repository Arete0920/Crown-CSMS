# CROWN Full Completion Blockers — 2026-05-29

## Decision

NO-GO for full module/dashboard/component/wizard completion certification.

This file records connector-verified blockers and weaknesses for the CROWN full-completion project. It is intentionally evidence-first and must not be treated as a release signoff.

## Verified repo facts

- The frontend dashboard registry covers the declared Tier 1, Tier 2, later-tier, and platform operations dashboard surface.
- Backend installed apps include broad operational domains, including finance, financial aid, academics, gradebook, billing, communications, student records, HR, advancement, PD hub, safety, spiritual life, athletics, facilities operations, transportation, tenants, platform operations, payments, subscriptions, support, analytics, aftercare, home academy, and finance setup.
- The backend wizard registry contains 29 wizard entries and is wired into settings and URL routing.
- The frontend package exposes unit, shell, route, accessibility, navigation, role-matrix, and Playwright proof scripts.

## Blockers

### B1 — Dashboard templates are preview/fallback backed

The shared dashboard template base note says: `Sandbox preview data shown. Connect backend for live records.`

Many dashboard templates import or display this base note. This means the dashboard surface can exist and still fail the full-completion standard because the metrics are not proven live data.

Required fix:

- Replace template-only metrics with live service/API-backed data for every dashboard in the declared registry.
- Add explicit data provenance per dashboard widget.
- Mark dashboard data states accurately as `live`, `fallback`, `sample`, `unavailable`, or `error`.
- Fail certification if a ready dashboard is sample/template/fallback backed without a documented exception.

### B2 — Backend dashboard payloads include sample/fallback builders

The backend dashboard API can serve sample payloads when snapshots/live builders are absent. This is acceptable for sandbox preview, but not for full completion certification.

Required fix:

- Build live dashboard services per module.
- Replace broad sample payloads with real query/service payloads.
- Keep sample payloads only behind explicit demo/sandbox flags.
- Add tests proving production/full-completion mode refuses sample payload certification.

### B3 — Latest inspected commit did not return CI status/workflow proof

The connector did not return current workflow-run proof for the inspected recent commit. Without CI proof, tests cannot be treated as passed.

Required fix:

- Run the full local/CI completion gate.
- Attach generated evidence from `.crown-audit/dashboard-completion/latest` and `.crown-audit/full-completion-truth/latest`.
- Confirm frontend and backend gate outputs are current to the branch under review.

### B4 — Registry coverage is not equivalent to module completion

Frontend registry entries and route constants prove discoverability, not completion. A dashboard/module is not complete until it has live data, workflows, role enforcement, tests, screenshots, and runtime proof.

Required fix:

- Maintain a module-by-module completion matrix.
- Require evidence per module for backend model/service, API, frontend page/component, wizard, permission, and test coverage.
- Keep status as `IN_PROGRESS`, `NOT_DONE`, `BLOCKED`, or `UNKNOWN` until proof exists.

### B5 — Later-tier operational modules need deeper backend/runtime proof

Food Service, Fine Arts, Library/Media, Volunteer Management, Alumni, Network Benchmarking, and several platform operations dashboards have frontend registry evidence but still require backend and runtime verification.

Required fix:

- Add explicit backend apps/services or document the existing canonical backend surface.
- Add API tests and route proof for each module.
- Add Playwright proof for page render, permission visibility, and core workflow paths.

## Immediate fix added in this branch

This branch adds `scripts/execution/106_crown_full_completion_truth_gate.ps1`.

The gate scans:

- dashboard templates using preview/sandbox/base-note data;
- backend sample-payload signals;
- required CROWN scope coverage signals;
- current branch/head evidence.

Default behavior: fail when preview/sample/fallback dashboard data is present in certification context.

Run from repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\execution\106_crown_full_completion_truth_gate.ps1
```

For sandbox/demo-only inventory without failing on preview data:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\execution\106_crown_full_completion_truth_gate.ps1 -AllowPreviewData
```

## Required evidence outputs

Attach these files after running the gate:

```text
.crown-audit\full-completion-truth\latest\00_SUMMARY.md
.crown-audit\full-completion-truth\latest\10_dashboard_template_preview_blockers.csv
.crown-audit\full-completion-truth\latest\20_backend_sample_payload_blockers.csv
.crown-audit\full-completion-truth\latest\30_required_scope_status.csv
.crown-audit\full-completion-truth\latest\99_STATUS.json
```

Also run the existing dashboard completion gate:

```powershell
$env:CROWN_105_RUN_95_BASELINE = "1"
$env:CROWN_105_RUN_95_DEEP = "1"
$env:CROWN_105_RUN_HEAVY_FRONTEND = "1"
$env:CROWN_105_RUN_BACKEND_PYTEST = "1"
$env:CROWN_DEMO_TOKEN = "<valid token>"
powershell -ExecutionPolicy Bypass -File .\scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep
```

Required outputs:

```text
.crown-audit\dashboard-completion\latest\00_SUMMARY.md
.crown-audit\dashboard-completion\latest\30_check_results.csv
.crown-audit\dashboard-completion\latest\40_module_dashboard_matrix.csv
.crown-audit\dashboard-completion\latest\50_blockers.md
.crown-audit\dashboard-completion\latest\99_STATUS.json
```

## Completion rule

A module/dashboard/component/wizard cannot be marked COMPLETE unless all of the following are true:

- route exists;
- page renders at runtime;
- dashboard data is live or explicitly certified for the deployment context;
- no sample/template/fallback data is hidden behind a ready status;
- backend service/model/API exists where applicable;
- permissions are enforced;
- workflow wizard completes where applicable;
- frontend and backend tests pass;
- screenshots or CI artifacts exist;
- evidence files are current to the reviewed commit.
