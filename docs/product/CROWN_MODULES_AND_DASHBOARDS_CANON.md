# CROWN Modules and Dashboards Canon

Status: Planning Authority
Effective Date: 2026-06-09
Scope: CROWN modules and dashboards only
Release authority: `docs/CURRENT_RELEASE_STATUS.md`

## Authority and Limits

This document is the controlling product and architecture canon for CROWN module and dashboard completion planning. It controls module order, module boundaries, dashboard fit, completion vocabulary, evidence requirements, certification prerequisites, and independent review expectations.

This document does not override `docs/CURRENT_RELEASE_STATUS.md` for repository release posture, production GO/NO-GO status, sandbox approval, current-head certification, or release freeze decisions.

Current operating rule:

```text
Modules first.
Dashboards second.
Certification last.
Registry coverage is not completion.
Sample/template data is not production proof.
TC cannot self-approve.
NO-GO remains until evidence proves otherwise.
```

## Evidence Basis

This canon is based on the current repository planning and inspection surface, including:

- `docs/CURRENT_RELEASE_STATUS.md`
- `backend/core/models.py`
- `backend/crown_api/settings.py`
- `frontend/dashboards/src/config/dashboardRegistry.js`
- `frontend/dashboards/src/config/dashboardCertificationRegistry.js`
- `frontend/dashboards/src/config/moduleReadiness.js`
- known module/dashboard blockers, especially dashboard live-data proof and later-tier backend/runtime proof
- CROWN product strategy, competitor research, and Core / Modules / Add-ons taxonomy

This canon is not itself proof that any module or dashboard is complete.

## Product Architecture Model

CROWN is organized into three product layers.

### Layer 1: Core

Core owns institutional truth and shared platform controls.

Core includes:

- school / tenant context
- academic year / term context
- grade levels
- student master record
- family / household / guardian records
- staff / user identity
- role and permission model
- enrollment lifecycle
- audit logging
- tenant isolation
- entitlement and subscription controls
- data retention and rollover controls
- shared API, event, export, and reporting standards

Core data is canonical. Modules may read Core data. Modules may write to Core only through approved service paths.

### Layer 2: Modules

Modules run school operations. They may own module-specific records, workflows, queues, and operational services.

Modules must not duplicate Core truth. For example, Transportation may read family address data, but Transportation must not become the source of truth for family address. Billing may read student and family records, but Billing must not create separate student identity truth.

### Layer 3: Add-ons

Add-ons extend CROWN for mission, analytics, governance, implementation, or standalone-capable experiences. Add-ons must declare whether they are:

- Core-dependent
- module-dependent
- standalone-capable
- read-only against Core
- allowed to write back to Core
- tenant-specific
- network-wide / multi-school

## Completion Vocabulary

Use only these statuses for modules and dashboards.

| Status | Meaning |
|---|---|
| Inventory | Repo surface exists: app, route, component, registry row, or documented module concept. |
| Schema-visible | Models or data structures are visible and mapped. |
| Wired | Backend service/API, frontend route, permission path, and dashboard mapping are connected. |
| Runtime-visible | The module or dashboard can be exercised in a running environment. |
| Evidence-backed | Current tests and runtime artifacts prove the claimed behavior. |
| Certified | Independent review and all required proof are complete. |

Only `Certified` means complete.

The following are not completion proof:

- frontend registry row exists
- route exists
- page renders
- component imports successfully
- sample payload exists
- dashboard card displays values
- screenshots without tenant/permission/API evidence
- historical PASS/GO/SHIP language superseded by current release authority

## Module-First Rule

A dashboard cannot certify a module. A dashboard can only expose, summarize, and operationalize a module that already has a verified data/service/API foundation.

Required completion flow:

```text
Core record ownership
→ module-specific models
→ service/query layer
→ API endpoint
→ tenant enforcement
→ action-level permission enforcement
→ audit events
→ frontend workflow
→ dashboard summary service
→ dashboard fit/certification row
→ runtime/test/evidence packet
→ independent review
```

No module may be promoted to Certified without completing this flow.

## Dashboard Fit Rule

Dashboards are fitted after modules.

Every dashboard must map to:

- module key
- module owner
- dashboard owner
- source service/API
- live or certified snapshot provenance
- freshness SLA
- sensitivity classification
- role access matrix
- tenant enforcement proof
- drilldown behavior
- export behavior
- current certification state

Dashboard states must be truthful:

| Dashboard State | Meaning |
|---|---|
| Scaffold | Route/component/template exists, but live module proof is missing. |
| Hybrid | Some live or snapshot-backed behavior exists, but sample/fallback/demo dependency remains. |
| Live | Live service/API or certified snapshot feeds the dashboard, but full certification is not complete. |
| Certified | Live/snapshot data, freshness, permissions, tenant boundaries, tests, runtime proof, and independent review are complete. |

Production-visible dashboards may not hide sample/template/fallback data. If data is sample, stale, unavailable, restricted, or fallback, the dashboard must say so.

## Required Module Completion Package

Every module must define and prove the following.

### 1. Identity

- module key
- module name
- layer: Core / Module / Add-on / Platform Ops
- phase and order
- product owner
- engineering owner
- independent reviewer
- dashboard key, if applicable
- current status
- target status

### 2. Domain Ownership

- records owned by module
- Core records read by module
- Core records written by module, if any
- write-back service path
- records the module must never duplicate
- lifecycle states
- audit-required state transitions

### 3. Backend Surface

- app/service location
- models
- migrations
- serializers/schemas
- service/query layer
- URLs/API routes
- permissions
- tenant checks
- validation rules
- error states
- audit events
- tests

### 4. Frontend Surface

- route
- navigation entry
- shell compliance
- list/index view
- detail view, if required
- create/edit/submit workflows, if required
- loading state
- empty state
- error state
- forbidden state
- tenant mismatch behavior
- frontend tests

### 5. Dashboard Surface

- dashboard registry row
- certification registry row
- summary service/API
- metrics
- alerts
- work queue
- drilldowns
- data provenance
- freshness
- sensitivity classification
- small-cell suppression rules
- role redaction rules
- export rules
- screenshot/Playwright proof

### 6. Security and Governance

- unauthenticated access blocked
- unauthorized role blocked
- authorized role allowed
- cross-tenant access blocked
- module entitlement checked
- write actions audited
- destructive actions protected
- sensitive data redacted
- demo/sandbox write restrictions honored

### 7. Evidence

- backend tests
- permission tests
- tenant tests
- API contract tests
- frontend route/render tests
- dashboard provenance tests
- runtime smoke proof
- screenshot/Playwright proof
- evidence path
- independent review signoff

## Required Control Matrices

This canon is supported by the following control files:

- `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md`
- `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md`
- `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md`
- `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md`
- `docs/product/CROWN_MODULE_REVIEW_RACI.md`

The matrices are not optional. They are the row-level controls for applying this canon.

## Module Order

### Phase 0: Control Layer

| Order | Control Area | Purpose |
|---:|---|---|
| 0.1 | Tenant / School Context | Scope every request to the correct school. |
| 0.2 | Identity / Users / Roles | Establish user identity and role membership. |
| 0.3 | RBAC / Permissions | Enforce action-level access. |
| 0.4 | Audit Logging | Record material actions and sensitive access. |
| 0.5 | Entitlements / Subscriptions | Determine module availability per school. |
| 0.6 | Retention / Rollover | Govern archival, retention, purge, and year-end operations. |
| 0.7 | Dashboard Certification Contract | Prevent fake-ready dashboard promotion. |

### Phase 1: Core SIS Truth

| Order | Module | Purpose |
|---:|---|---|
| 1 | School / Academic Year / Grade Level | Establish school, calendar, and grade context. |
| 2 | Staff / Identity / Roles | Establish staff/user access and workflow ownership. |
| 3 | Family / Guardian / Household | Establish family, guardian, custody, and portal truth. |
| 4 | Student Master Record | Establish canonical student identity and status. |
| 5 | Enrollment / Registrar | Establish applicant, active, withdrawn, graduated states. |
| 6 | Courses / Sections / Rosters | Establish instructional structure and student membership. |
| 7 | Attendance | Establish daily student presence operations. |
| 8 | Gradebook | Establish assignments, grades, and academic progress. |
| 9 | Transcript / Report Card / Graduation | Establish official academic records. |
| 10 | Student Care / Discipline | Establish student support and discipline workflow summary. |

### Phase 2: First Commercial Operating Modules

| Order | Module | Purpose |
|---:|---|---|
| 11 | Admissions | Manage applicant and enrollment funnel. |
| 12 | Re-enrollment | Manage returning-student annual commitment. |
| 13 | Billing / Tuition / Ledger | Manage tuition, charges, payments, balances, and ledger truth. |
| 14 | Financial Aid | Manage aid applications, awards, and billing impact. |
| 15 | Communications | Manage school-to-family and internal communications. |
| 16 | Parent / Family Portal | Expose family tasks, records, billing, and communications. |
| 17 | Teacher Portal | Expose faculty daily workflows. |
| 18 | Administrator Portal | Expose operational leadership workflows. |

### Phase 3: Operational Expansion Modules

| Order | Module | Purpose |
|---:|---|---|
| 19 | Scheduling | Manage schedule construction and section placement. |
| 20 | Activities / Athletics | Manage teams, activities, events, eligibility, and rosters. |
| 21 | Health Office | Manage health visits, restrictions, alerts, and sensitive records. |
| 22 | Transportation | Manage routes, riders, stops, and transport communication. |
| 23 | Food Service | Manage meal service, accounts, menus, and participation. |
| 24 | Facilities | Manage facilities, rooms, maintenance, and work orders. |
| 25 | Safety / Security | Manage safety incidents, drills, and security workflows. |
| 26 | HR | Manage staff lifecycle and compliance. |
| 27 | IT Support | Manage school and platform support workflows. |

### Phase 4: Enrichment, Mission, and Advancement

| Order | Module | Purpose |
|---:|---|---|
| 28 | Fine Arts | Manage arts participation, ensembles, events, and rosters. |
| 29 | Library / Media | Manage circulation, resources, and media support. |
| 30 | Extended Care | Manage before/after care sessions, attendance, and billing links. |
| 31 | Summer Camp | Manage seasonal camp sessions, rosters, and setup. |
| 32 | Spiritual Life / Chaplaincy | Manage chapel, discipleship, pastoral workflows, and mission care. |
| 33 | Service / Outreach / Portrait | Manage service learning, outreach, and portrait-of-graduate goals. |
| 34 | Volunteer Management | Manage family/community volunteers and approvals. |
| 35 | Advancement Operations | Manage development, donor, and campaign operations. |
| 36 | Alumni Relations | Manage alumni identity, engagement, and advancement links. |
| 37 | Board Governance | Manage board packet, governance, and leadership workflows. |
| 38 | Curriculum / PD | Manage curriculum maps, professional development, and faculty growth. |
| 39 | Network Benchmarking / Analytics | Manage anonymized/network analytics and school benchmarking. |

### Phase 5: Platform Operations

| Order | Module | Purpose |
|---:|---|---|
| 40 | Implementation Success | Manage customer onboarding and implementation health. |
| 41 | Data Migration | Manage imports, mapping, validation, and conversion. |
| 42 | Integrations / Automation | Manage external integrations and sync jobs. |
| 43 | Compliance Audit | Manage compliance evidence and exceptions. |
| 44 | Revenue Operations | Manage internal CROWN revenue operations. |
| 45 | Release Reliability | Manage release health, checks, and evidence. |
| 46 | Dashboard Certification Center | Manage dashboard certification visibility. |

## First Completion Batch

The first batch is intentionally dependency-driven, not alphabetical.

| Batch Order | Module | Reason |
|---:|---|---|
| 1 | School / Academic Year / Grade Level | Establish tenant/year/grade context. |
| 2 | Staff / User / Role | Establish users and permissions. |
| 3 | Family / Guardian / Household | Establish family truth. |
| 4 | Student Master Record | Establish student truth. |
| 5 | Enrollment / Registrar | Establish student lifecycle. |
| 6 | Courses / Sections / Rosters | Establish academic membership. |
| 7 | Attendance | First daily operational module and dashboard proof target. |
| 8 | Billing / Tuition / Ledger | Revenue-critical module. |
| 9 | Gradebook | Academic-critical module. |
| 10 | Communications | Cross-module utility and family experience backbone. |

## Wiring and Plumbing Standard

Every module must use this standard path:

```text
request
→ authentication
→ tenant resolution
→ entitlement check
→ role/action permission check
→ module service
→ validation
→ transaction boundary
→ audit event
→ API response
→ frontend state
→ dashboard summary/snapshot
→ evidence packet
```

No module may bypass tenant enforcement, permission checks, or audit requirements.

## Dashboard Data Standard

Every dashboard payload must declare:

- `dashboard_key`
- `module_key`
- `schema_version`
- `served_from`: `live`, `snapshot`, `stale_snapshot`, `sample`, `fallback`, `unavailable`, or `error`
- `source_module`
- `generated_at`
- `expires_at`, if snapshot-backed
- `sensitivity_level`
- `metrics`
- `alerts`
- `queue`
- `drilldowns`
- `redactions`, if any

Dashboard summary payloads must not contain full sensitive records. Drilldowns must be paginated and role-filtered.

## Security Rules

1. Authentication is required but not sufficient.
2. Every module API must enforce tenant context.
3. Every module action must enforce action-level permission.
4. Dashboard access must be checked per dashboard key.
5. Module entitlement must be checked before navigation, API access, and dashboard access.
6. Hidden navigation is not security.
7. Direct URL access must be tested.
8. Cross-tenant attempts must be denied and logged.
9. Sensitive dashboards require field-level redaction and small-cell suppression.
10. Exports must be permissioned, tenant-bound, redacted, audited, and time-limited.

## Performance Rules

1. Dashboards must not query large operational tables directly from components.
2. Every dashboard needs a bounded summary service.
3. Heavy metrics should be precomputed or snapshot-backed.
4. Every dashboard summary service needs a query-count budget.
5. Every dashboard payload needs a payload-size limit.
6. Drilldowns must paginate.
7. Snapshot freshness must be explicit.
8. Dashboard response time and payload size should be observable.

## Competitor Research Implications

The competitor research confirmed that market-leading school platforms compete on unified records, connected admissions/enrollment/billing workflows, family experience, role-specific portals, integrations, reporting, and actionable dashboards.

CROWN must match market expectations in:

- unified student/family/staff record truth
- admissions and enrollment workflows
- billing and financial aid workflows
- parent/family experience
- teacher daily workflows
- role-specific dashboards
- reporting and drilldowns
- integrations and data portability

CROWN must differentiate through:

- Christian-school mission layer
- Spiritual Life / Chaplaincy
- Service / Outreach / Portrait of the Graduate
- Board Governance
- Crown Compass-style mission/accountability surfaces
- dashboard truthfulness and certification rigor
- no hidden sample/template data in production-ready dashboards

## Independent Review Rule

TC may set direction and priorities, but TC cannot independently review or approve TC's own work.

Every Certified promotion requires independent review. The reviewer must inspect the evidence packet and sign off on:

- module boundary
- data ownership
- backend/API proof
- frontend proof
- tenant proof
- permission proof
- dashboard proof
- runtime proof
- certification status

## Promotion Rule

A module or dashboard may be promoted only when its matrix row has current evidence for every required proof item.

Promotion cannot be based on:

- historical evidence only
- planned work
- screenshots alone
- sample data
- registry coverage
- chat assertions
- unreviewed local work

## Required Next Step

Apply this canon through the supporting control matrices in this order:

1. `CROWN_MODULE_COMPLETION_MATRIX.md`
2. `CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md`
3. `CROWN_MODULE_PERMISSION_MATRIX.md`
4. `CROWN_DASHBOARD_FIT_MATRIX.md`
5. `CROWN_MODULE_REVIEW_RACI.md`

Until those matrices are filled with current evidence, all module/dashboard completion claims remain unverified.
