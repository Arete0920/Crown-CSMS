# CROWN Dashboard Completion Project

Status: Planning control document
Date: 2026-06-18
Branch: docs/dashboard-plan-20260618
Scope: Dashboard live-data completion and certification only
Release authority: docs/CURRENT_RELEASE_STATUS.md

## Current verified baseline

- 40 dashboard rows exist in the canonical dashboard live-data matrix.
- All 40 are currently MAPPED only.
- All 40 currently carry the same blocker: route registered but live-data not wired.
- Module proof is now separately reconciled as 51/51 PROVEN, but module proof does not certify dashboard live-data readiness.
- Existing dashboard structure, shell, route/nav conventions, style, widget patterns, and UI format are treated as established. This project does not authorize a redesign or new route sprawl.

## Operating decision

This is not a dashboard design project. It is a dashboard live-data, KPI, provenance, permission, tenant, runtime-proof, and certification project.

## Governing rules

1. Registry coverage is not completion.
2. Page render is not completion.
3. Sample/template data is not production proof.
4. A dashboard may only expose proven module truth.
5. Core owns canonical truth.
6. Modules own bounded operational records and services.
7. Dashboards consume live or certified snapshot summaries.
8. Each dashboard must disclose data provenance.
9. Each dashboard must prove role access and direct URL denial.
10. Each dashboard must prove cross-tenant denial.
11. Each dashboard must include useful empty, loading, error, and forbidden states.
12. Each dashboard must retain the established CROWN visual structure and widget language.
13. TC may direct priorities and accept product fit, but TC cannot independently review or approve certification.
14. No dashboard moves to CERTIFIED without independent review.

## Completion statuses

| Status | Meaning |
|---|---|
| MAPPED | Route/registry/page exists; live data not proven. |
| DATA_CONTRACTED | KPI, alert, queue, drilldown, provenance, security, and freshness contract approved. |
| API_WIRED | Backend summary service/API returns dashboard payload with provenance. |
| UI_WIRED | Dashboard consumes summary payload and renders real states. |
| PERMISSION_PROVEN | Authenticated/unauthenticated/role/direct URL proof exists. |
| TENANT_PROVEN | Cross-tenant denial proof exists. |
| RUNTIME_PROVEN | Running environment proof, screenshots/traces, and Playwright evidence exist. |
| CERTIFIED | Independent reviewer has approved the evidence packet and matrix row. |

Only CERTIFIED means complete.

## Required dashboard payload contract

Every dashboard summary payload must contain:

```json
{
  "dashboard_key": "attendance",
  "module_key": "attendance",
  "schema_version": "1.0",
  "served_from": "live",
  "source_module": "attendance",
  "generated_at": "2026-06-18T00:00:00Z",
  "expires_at": null,
  "sensitivity_level": "internal",
  "metrics": [],
  "alerts": [],
  "queue": [],
  "drilldowns": [],
  "redactions": []
}
```

Allowed served_from values:

- live
- snapshot
- stale_snapshot
- sample
- fallback
- unavailable
- error

Production-visible dashboards may not hide sample, fallback, stale, unavailable, or error status. The dashboard must say what it is serving.

## Standard dashboard evidence packet

Each dashboard must produce this packet:

```text
01_contract.md
02_backend_summary_service_reference.txt
03_api_route_reference.txt
04_permission_tests.txt
05_tenant_tests.txt
06_frontend_render_test.txt
07_playwright_runtime_proof.txt
08_screenshot_or_trace_artifact.txt
09_payload_sample_redacted.json
10_independent_review.md
11_matrix_update.diff
```

## Workstreams

### Workstream 1: Dashboard contracts

Owner: SIS/Data Lead plus module owner.

Deliverables:

- KPI definitions
- metric source map
- alert definitions
- queue/list/table definition
- drilldown map
- role access matrix
- sensitivity classification
- freshness SLA
- served_from rules
- empty/error/forbidden state rules

### Workstream 2: Backend summary services

Owner: Core Platform Lead plus module owner.

Deliverables:

- bounded summary service
- dashboard summary API route
- entitlement check
- dashboard permission check
- tenant enforcement
- redaction/small-cell suppression where required
- backend pytest proof

### Workstream 3: Frontend wiring

Owner: Frontend/UX Lead.

Deliverables:

- existing dashboard page wired to summary API
- KPI row wired
- alert/status area wired
- queue/table/list wired
- drilldowns wired
- loading state
- empty state
- error state
- forbidden state
- provenance indicator

### Workstream 4: QA and certification

Owner: Integration/QA/Release Lead.

Deliverables:

- route/render tests
- permission tests
- tenant tests
- Playwright runtime tests
- screenshot/trace proof
- evidence packet
- independent review
- matrix promotion

## Batches

### Batch 0: Control dashboards

- dashboard-certification-center
- release-reliability
- compliance-audit

Purpose: create the proof machinery and dashboard certification visibility before claiming business dashboard completion.

### Batch 1: Operational school backbone

- attendance
- billing
- gradebook
- communications
- registrar
- school-administrator

Purpose: prove the core daily operating dashboards first.

### Batch 2: Commercial and role experience

- admissions
- financial-aid
- parent
- teacher
- student
- activities-athletics

Purpose: prove buyer-visible, family-visible, teacher-visible, and student-visible value.

### Batch 3: Operational expansion

- scheduling
- health-office
- transportation
- food-service
- facilities
- safety-security
- hr
- it-support

Purpose: complete operational breadth with sensitive-data and logistics proof.

### Batch 4: Mission, advancement, and enrichment

- chaplain-spiritual-life
- portrait-service
- curriculum-pd
- fine-arts
- library-media
- volunteer-management
- advancement
- advancement-operations
- alumni-relations
- school-board
- network-benchmarking

Purpose: complete CROWN differentiation and leadership-facing dashboards.

### Batch 5: Platform operations and remaining specialized dashboards

- master-control
- implementation-success
- data-migration
- integrations-automation
- revenue-operations
- summer-camp
- extended-care
- athletics-director

Purpose: complete platform operations and specialized service dashboards.

## Acceptance criteria

The dashboard project is complete only when:

- 40/40 dashboards have assigned owners.
- 40/40 dashboards have assigned independent reviewers.
- 40/40 dashboards have data contracts.
- 40/40 dashboards have summary APIs or certified snapshot services.
- 40/40 dashboards have UI wiring.
- 40/40 dashboards have permission proof.
- 40/40 dashboards have tenant proof.
- 40/40 dashboards have runtime proof.
- 40/40 dashboards have evidence packets.
- 40/40 dashboards are CERTIFIED or explicitly marked non-production-visible.
- 0 dashboards hide sample/template/fallback data.
- 0 dashboards remain owner TBD.
- 0 dashboards remain reviewer TBD.

## Non-goals

- No public release approval.
- No production GO.
- No sandbox GO.
- No broad redesign.
- No arbitrary new dashboard routes.
- No duplicate dashboard concepts.
- No product-code change in the planning branch unless explicitly authorized later.
