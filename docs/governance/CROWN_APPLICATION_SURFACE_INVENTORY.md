# CROWN Application Surface Inventory

**Document ID:** CROWN-GOV-006  
**Status:** ACTIVE — Stage 1 Census in Progress  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Baseline repository SHA:** `fc4d6907a079efb3f8aedbd041c11d8f01a218f4`  
**Verification date:** 2026-07-24  
**Controlling issue:** #1587

## Purpose

Create one authoritative census of every active CROWN application surface before module certification or final runtime proof. Inventory presence does not prove completion. Every item must ultimately map to an owner, canonical path, persona, tenant scope, sensitivity classification, proof mechanism and current disposition.

## Allowed disposition values

`ACTIVE`, `DISABLED_FAIL_CLOSED`, `EXCLUDED_PAYMENT_PROCESSING`, `EXCLUDED_HANDOFF`, `NOT APPLICABLE`, `SUPERSEDED`, or `REMOVED`.

## Allowed proof mechanisms

`CRAWLER`, `PLAYWRIGHT`, `API_CONTRACT`, `BACKEND_TEST`, `OPERATIONAL_DRILL`, `MANUAL_REVIEW`, `EXCLUDED_PAYMENT_PROCESSING`, `EXCLUDED_HANDOFF`, or `NOT_APPLICABLE`.

## Census summary

| Surface class | Verified source | Current count/state | Census status |
|---|---|---:|---|
| Backend configured applications | `backend/crown_api/settings.py`; `backend/crown_api/wizard_registry.py`; `docs/governance/CROWN_BACKEND_CONFIGURATION_LEDGER.md` | 95 total: 67 explicit plus 28 registry-derived wizard apps | INVENTORIED at configuration level — per-app implementation and runtime proof pending |
| Backend root route layers | `backend/crown_api/urls.py`; `backend/crown_api/api_v1_urls.py`; `docs/governance/CROWN_BACKEND_CONFIGURATION_LEDGER.md`; `docs/governance/CROWN_NESTED_BACKEND_ROUTE_LEDGER_BATCH1.md` | 73 always-registered root patterns plus one optional; 47 always-registered API-v1 patterns plus one optional; first high-risk nested batch inventoried | PARTIAL — Batch 1 controlled; remaining nested URL leaves and executable resolver manifest pending |
| Registered wizards | `backend/crown_api/wizard_registry.py` | 28 | INVENTORIED — per-wizard evidence mapping pending |
| Dashboard registry entries | `frontend/dashboards/src/config/dashboardRegistry.js` | 40 across seven tiers | INVENTORIED — source/API/runtime mapping pending |
| Frontend application routes | `frontend/dashboards/src/routes/router.jsx` plus generated route collections | Large mixed canonical, alias, guarded, public, sandbox and launch-preview surface | PARTIAL — exact route row extraction pending |
| Product control areas | `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | 7 control-layer areas plus 46 ordered module/platform areas | INVENTORIED — implementation reconciliation pending |
| GitHub workflow surfaces | `.github/workflows/*` | Multiple merge, release, runtime, security, evidence and advisory workflows | PARTIAL — proof hierarchy pending under #1394 |

## Backend route-layer inventory

| Layer | Representative prefix or endpoint | Disposition | Initial proof mechanism | Open reconciliation |
|---|---|---|---|---|
| Health and diagnostics | `/health/`, `/api/health/`, `/health/version/`, `/api/system/health/`, `/api/integrity/`, `/api/v1/version/` | ACTIVE | API_CONTRACT | Bind to deployed identity and access policy |
| API schema and documentation | `/api/schema/`, `/api/docs/`, `/api/redoc/` | ACTIVE or environment-limited | API_CONTRACT + MANUAL_REVIEW | Confirm production exposure policy |
| Authentication | `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/me/`, `/accounts/` | ACTIVE | API_CONTRACT + PLAYWRIGHT | Reconcile JWT, session and Microsoft identity flows |
| Tenant identity proof | `/api/system/whoami/` | ACTIVE | API_CONTRACT | Confirm tenant and role outputs in deployed runtime |
| Wizard discovery and routes | `/api/v1/wizards/` and registry-derived prefixes | ACTIVE | API_CONTRACT + PLAYWRIGHT | Expand all 28 workflows |
| Dashboard API | `/api/v1/dashboards/` | ACTIVE | API_CONTRACT + PLAYWRIGHT | Map all 40 dashboard keys to source services |
| Canonical API | `/api/v1/` | ACTIVE | API_CONTRACT + BACKEND_TEST | Complete remaining nested route inventory and resolver precedence proof |
| Compatibility API alias | `/api/` | ACTIVE compatibility layer | API_CONTRACT | Classify each alias for retention or retirement |
| Dashboard compatibility alias | `/api/dashboards/` | ACTIVE compatibility layer | API_CONTRACT | Prove authorization parity with canonical path |
| Curriculum and classroom | `/api/curriculum/`, `/api/classroom/` | ACTIVE | API_CONTRACT + BACKEND_TEST | Verify read-only/demo-safe claims against settings |
| Student and executive summaries | `/api/student360/`, `/api/executive360/` | ACTIVE | API_CONTRACT + PLAYWRIGHT | Map data ownership and redaction |
| Finance | `/api/finance/` | ACTIVE provider-neutral scope | API_CONTRACT + BACKEND_TEST | External payment entry points remain fail closed |
| Platform operations | `/api/platform/` | ACTIVE privileged surface | API_CONTRACT + MANUAL_REVIEW | Verify cross-tenant authorization and audit |
| Subscriptions and entitlements | `/api/v1/subscriptions/`, `/api/v1/admin/modules/` | ACTIVE | API_CONTRACT + BACKEND_TEST | Reconcile module visibility and entitlement enforcement |
| Integrations | `/api/integrations/` | ACTIVE or configured-disabled by integration | API_CONTRACT + OPERATIONAL_DRILL | Inventory enabled providers, retries and ownership |
| Microsoft identity | `/auth/`, `/api/iam/` | ACTIVE where configured | API_CONTRACT + PLAYWRIGHT | Reconcile session and bearer-token identities |
| Director persona routes | `/director/` and persona subroutes | ACTIVE/legacy mixed | PLAYWRIGHT | Reconcile with frontend role dashboards and redirects |
| Development token | `/api/dev/token/` | DISABLED_FAIL_CLOSED outside approved development | BACKEND_TEST | Verify production deterministic denial |
| External payment processing | checkout/webhook/confirmation entry points | EXCLUDED_PAYMENT_PROCESSING | EXCLUDED_PAYMENT_PROCESSING | Must remain disabled and fail closed |

## Wizard registry inventory

All 28 registry entries are installed and routed from one backend registry. Their presence is verified; functional certification is not.

| # | Wizard | API prefix | Initial disposition | Proof required |
|---:|---|---|---|---|
| 1 | Student Onboarding | `/api/v1/onboarding/imports/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 2 | Re-enrollment | `/api/v1/reenrollment/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 3 | Billing Setup | `/api/v1/billing-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 4 | Financial Aid Setup | `/api/v1/aid-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 5 | Scheduling Setup | `/api/v1/scheduling-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 6 | Communications Campaign | `/api/v1/comms-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 7 | Section Assignments | `/api/v1/section-assign-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 8 | Bell Schedule | `/api/v1/bell-schedule-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 9 | Gradebook Setup | `/api/v1/gradebook-setup-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 10 | Attendance Rules | `/api/v1/attendance-rules-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 11 | Enrollment Conversion | `/api/v1/enrollment-conversion-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 12 | Invoice Run | `/api/v1/invoice-run-wizard/sessions/` | ACTIVE provider-neutral scope | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 13 | Staff Onboarding | `/api/v1/staff-onboarding-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 14 | Fee Schedule Setup | `/api/v1/fee-schedule-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 15 | Academic Year Rollover | `/api/v1/academic-year-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, OPERATIONAL_DRILL |
| 16 | Enrollment Period Setup | `/api/v1/enrollment-period-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 17 | Grade Scale Setup | `/api/v1/grade-scale-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 18 | Term Structure Setup | `/api/v1/term-structure-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 19 | Section Scheduler Seed | `/api/v1/section-scheduler-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 20 | Staff and Roles Setup | `/api/v1/staff-setup-wizard/sessions/` | ACTIVE privileged | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT, MANUAL_REVIEW |
| 21 | Course Catalog Setup | `/api/v1/course-catalog-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 22 | Rooms Setup | `/api/v1/room-setup-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 23 | Promotion Map Setup | `/api/v1/promotion-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 24 | Student Import | `/api/v1/student-import-wizard/sessions/` | ACTIVE sensitive import | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT, OPERATIONAL_DRILL |
| 25 | Guardian and Household Setup | `/api/v1/guardian-household-wizard/sessions/` | ACTIVE sensitive | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 26 | Section Staffing | `/api/v1/section-staffing-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 27 | Attendance Codes Setup | `/api/v1/attendance-codes-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |
| 28 | Grade Weights and Categories | `/api/v1/grade-weights-wizard/sessions/` | ACTIVE | API_CONTRACT, BACKEND_TEST, PLAYWRIGHT |

## Dashboard registry inventory

The registry contains 40 entries across seven tiers. Registry presence and frontend role metadata do not prove module readiness or backend authorization.

| Tier | Dashboard keys |
|---:|---|
| 1 | attendance; billing; financial-aid; registrar |
| 2 | scheduling; gradebook; student-care; activities-athletics; communications |
| 3 | school-administrator; school-board; master-control; admissions; advancement |
| 4 | hr; facilities; health-office; transportation; food-service; it-support |
| 5 | fine-arts; athletics-director; library-media; extended-care; summer-camp; safety-security; curriculum-pd |
| 6 | chaplain-spiritual-life; advancement-operations; volunteer-management; portrait-service; alumni-relations; network-benchmarking |
| 7 | implementation-success; data-migration; integrations-automation; compliance-audit; revenue-operations; release-reliability; dashboard-certification-center |

### Dashboard evidence warning

Three registry entries contain explicit release-state or evidence metadata, but those artifacts are historical and do not establish current certification:

- `school-administrator` references evidence collected 2026-06-22;
- `release-reliability` references candidate SHA `8097d4c23e847bfaced4d9a49637a3aa0e20617b`;
- `dashboard-certification-center` references the same historical candidate SHA.

These rows remain subject to current-SHA source, permission, tenant, freshness, browser and independent-review requirements.

## Frontend route-surface classes

| Class | Verified examples | Initial status | Required reconciliation |
|---|---|---|---|
| Public/authentication | `/login`, `/logout`, admissions start/apply routes | PARTIAL | Confirm intended public boundaries and negative paths |
| Role landing and dashboards | `/`, `/dashboard`, `/dash/:role`, school/teacher/parent/student/board dashboards | PARTIAL | Reconcile role groups with backend permissions |
| Teacher workflows | attendance, gradebook alias, communications alias, scheduling alias, classes, lesson plans, daily cockpit | PARTIAL | Canonicalize aliases and section/roster scope |
| Parent workflows | attendance, admissions, billing, payment-held path, aid preparation, lifecycle status, learning status | PARTIAL | Confirm guardian/student scope and payment fail-closed behavior |
| Student workflows | dashboard, today, assignments and learning surfaces | PARTIAL | Confirm student identity and tenant scope |
| Administrative modules | billing, finance, financial aid, registrar, academics, scheduling, HR, facilities, safety and specialist routes | PARTIAL | Extract exact route rows and backend dependencies |
| Dashboard-generated routes | `dashboardRoutes` | PARTIAL | Reconcile all 40 keys and guard behavior |
| Wizard-generated routes | `wizardRoutes` plus dedicated setup wizard pages | PARTIAL | Reconcile frontend routes with 28 backend registry entries |
| Sandbox/launch-preview | sandbox landing, command center and launch takeover surfaces | ACTIVE bounded test surface | Verify production exclusion and no hidden fallback |
| Legacy aliases | billing and teacher aliases plus compatibility redirects | PARTIAL | Retain with tests or retire through controlled decision |
| Error/denial | not-authorized, forbidden, not-found | ACTIVE | Verify direct-route and role-negative behavior |

## Critical unresolved census questions

1. Per-app model, migration, service, serializer, command, signal, task, import/export and runtime evidence for the 95 configured applications.
2. Remaining nested Django URL configurations, router-generated actions, route names and executable resolver precedence.
3. Full frontend route extraction from `router.jsx`, `dashboardRoutes`, `wizardRoutes` and path constants.
4. Complete command, scheduler, signal, webhook, upload, import, export and report inventory.
5. Enabled-versus-installed integration classification by environment.
6. Canonical versus compatibility route and model ownership.
7. Exact GitHub workflow proof hierarchy and obsolete-duplicate disposition.
8. Mapping of every row to one primary proof mechanism and any required secondary mechanisms.

## Current conclusion

Stage 1 is materially underway but not complete. The exact configured-application count, wizard count, dashboard count, middleware count, root route population, canonical API-v1 population and first high-risk nested-route batch are now controlled. The next census passes must complete remaining backend resolver leaves, frontend route collections, commands/jobs/integrations and workflow surfaces as row-level records.