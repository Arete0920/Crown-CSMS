# CROWN Regulated and Sensitive Data Inventory

**Status:** CONTROLLED COMPLIANCE SUPPORTING RECORD / COMPREHENSIVE REPOSITORY-BOUNDED INVENTORY  
**Effective date:** 2026-07-29  
**Observed source identity:** `ea79bec207f9d82b617235f86ab3173d8f52bc0e`  
**Controlling issues:** #1764, #1759, #1629, and #1619

## Purpose and boundary

This record inventories regulated and sensitive data evidenced in the current CROWN repository. It consolidates source-visible model domains, storage paths, exports, browser persistence, audit/logging, backup/retention controls, and integration surfaces.

This is a comprehensive repository-bounded inventory, not a legal opinion or a production data-flow certification. It does not establish active production vendors, processing regions, contractual approval, jurisdiction-specific applicability, runtime authorization, retention enforcement, backup behavior, or production readiness.

A companion machine-readable path inventory is maintained at `docs/compliance/REGULATED_DATA_INVENTORY_PATHS.json`.

## Evidence-status rule

- **VERIFIED SOURCE** — current source directly defines the field, relation, storage behavior, or control.
- **VERIFIED PATH** — a current repository path implements or references the processing surface.
- **PARTIAL FLOW** — the domain or path is confirmed, but runtime recipients, enforcement, or production use are not proven.
- **UNVERIFIED OPERATION** — production behavior requires deployed-system evidence.
- **NOT AUTHORIZED** — functionality remains disabled, deferred, or outside current release authority.

## Data subjects confirmed in source

- students and applicants;
- guardians, parents, families, and households;
- employees, staff, teachers, administrators, and support users;
- donors, volunteers, coaches, reviewers, approvers, and board/governance users;
- authentication principals and integration/service identities;
- sandbox/demo personas and non-production test records.

## Verified source domains

| Domain | Data subjects | Verified source data | Primary source paths | Status |
|---|---|---|---|---|
| Tenant and school structure | School personnel, students, users | School identity, timezone, status, tenant ownership and relationships | `backend/tenants/models.py`, `backend/core/tenant_models.py`, `backend/core/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| Family and household | Guardians, parents, students | Names, addresses, contact details, status and household relationships | `backend/households/models.py`, `backend/core/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Guardian and custody | Guardians, parents, students | Name, email, phone, relationship, portal access and custody indicators | `backend/core/models.py`, `backend/applications/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Student identity and records | Students | Student identifiers, names, birth dates, status, family, grade and record relationships | `backend/core/models.py`, `backend/student_records/models.py`, `backend/academics/models.py` | VERIFIED SOURCE / EDUCATION RECORD |
| Authentication and authorization | Users, staff, guardians, service identities | Accounts, tenant associations, roles, permissions, identity links and access metadata | `backend/crown_api/auth_models.py`, `backend/core/models.py`, `backend/identity/models.py` | VERIFIED SOURCE / AUTHENTICATION SENSITIVE |
| Admissions and applications | Applicants, students, families, reviewers | Application status, GPA, test scores, essays, transcript/recommendation indicators, internal notes, contact history, scoring, decisions and audit JSON | `backend/admissions/models.py`, `backend/applications/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Enrollment and reenrollment | Students, families | Academic year, grade, enrollment dates, status, checklist and renewal data | `backend/core/models.py`, `backend/reenrollment/models.py`, `backend/onboarding/models.py` | VERIFIED SOURCE / EDUCATION RECORD |
| Academics, classroom and gradebook | Students, teachers, families | Courses, assignments, lessons, grades, assessments, curriculum and classroom relationships | `backend/academics/models.py`, `backend/classroom/models.py`, `backend/gradebook/models.py`, `backend/curriculum/models.py`, `backend/curricula/models.py` | VERIFIED SOURCE / EDUCATION RECORD |
| Attendance and aftercare | Students, families, staff | Attendance events, participation, aftercare enrollment and operational notes | `backend/attendance/models.py`, `backend/aftercare/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Discipline and safety | Students, families, staff | Incident details, categories, severity, narratives, assigned users, parent notification, action notes and safety records | `backend/discipline/models.py`, `backend/safety/models.py` | VERIFIED SOURCE / RESTRICTED SENSITIVE |
| Spiritual life and pastoral care | Students, staff, families | Faith background, baptism, gifts, assessments, chapel/small-group attendance, prayer requests, visibility and pastoral notes | `backend/spiritual_life/models.py`, `backend/solomon/models.py` | VERIFIED SOURCE / RESTRICTED SENSITIVE |
| Financial aid | Families, students, approvers | Household income, household size, hardship, mission and merit classifications, award amounts, rationale, approvals and audit messages | `backend/financial_aid/models.py`, `backend/aid/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Tuition, billing, ledger and accounting | Students, families, staff | Tuition plans, amounts, discounts, balances, account and batch relations, memos, entries, reversals, statements and accounting records | `backend/billing/models.py`, `backend/billing_wizard/models.py`, `backend/ledger/models.py`, `backend/finance/models.py`, `backend/journal/models.py`, `backend/accounting/models.py` | VERIFIED SOURCE / FINANCIAL SENSITIVE |
| Payment-adjacent data | Families, students, staff, service identities | Payment configuration, references, webhooks, statement imports, parsed entries and processing metadata | `backend/payments/models.py` | VERIFIED SOURCE / NOT AUTHORIZED FOR PRODUCTION |
| Communications and notifications | Students, families, staff | Message content, recipients, delivery metadata, templates and communication history | `backend/comms/models.py`, `backend/signals/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| HR and professional development | Employees, staff | Employment/status indicators, HR records, professional-development activity and notes | `backend/hr/models.py`, `backend/pdhub/models.py` | VERIFIED SOURCE / EMPLOYEE SENSITIVE |
| Advancement and outreach | Donors, volunteers, families, community contacts | Donor, campaign, outreach, contact and participation records | `backend/advancement/models.py`, `backend/outreach/models.py`, `backend/servicehours/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| Athletics, transportation and facilities | Students, families, staff, volunteers | Teams, participation, transportation, facility and operations records | `backend/athletics/models.py`, `backend/transportation/models.py`, `backend/facops/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| Analytics and signals | Students, families, staff, administrators | Derived metrics, predictions, signal events, JSON details and actor/timestamp data | `backend/analytics/models.py`, `backend/analytics/tasks.py`, `backend/signals/models.py`, `backend/signals/engine.py` | VERIFIED SOURCE / HIGH-RISK DERIVED DATA |
| Support, subscriptions and platform operations | Customer administrators, support users, service identities | Tickets, support content, subscription state, operational events and platform metadata | `backend/support/models.py`, `backend/subscriptions/models.py`, `backend/platform_ops/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| Sandbox and demonstrations | Demo personas and synthetic records | Sandbox accounts, tenant/demo state, telemetry and helper metadata | `backend/sandbox_demo/models.py`, `frontend/dashboards/src/sandbox/` | VERIFIED SOURCE / NON-PRODUCTION |

## High-risk free text and JSON

Confirmed high-risk unstructured paths include:

- admissions essays, reviewer notes, recommendations, contact history and audit JSON;
- financial-aid rationale, hardship descriptions and audit messages;
- discipline summaries, detailed narratives and action notes;
- spiritual-profile notes, assessments, prayer-request bodies and pastoral notes;
- support tickets and communications content;
- ledger, journal and accounting memos;
- safety, HR, analytics and signal details;
- application, survey, form and wizard draft payloads.

Unstructured content can contain information beyond its field label. Access, export, logging, retention, redaction and deletion controls must therefore be based on actual use rather than field names alone.

## Uploads, documents and generated artifacts

Verified repository paths include file or document handling in admissions/applications, academics, financial aid, support, communications and export/reporting components. Source search also confirms export resolver and frontend export controls:

- `backend/crown_api/exports/model_resolver.py`;
- `backend/core/models_export.py`;
- `frontend/dashboards/src/components/exports/ExportButton.tsx`;
- `frontend/dashboards/src/components/exports/BulkExportMenu.tsx`.

Repository evidence confirms export capability and generated artifacts, but does not prove production recipients, storage provider, download retention, access logging or deletion propagation.

## Browser storage and client-side persistence

Verified frontend paths use or manage browser persistence, authentication state, wizard drafts, table state, sandbox state or telemetry, including:

- `frontend/dashboards/src/lib/authGuard.js`;
- `frontend/dashboards/src/auth/msalConfig.js`;
- `frontend/dashboards/src/utils/authClient.js`;
- `frontend/dashboards/src/hooks/useWizardDraft.js`;
- `frontend/dashboards/src/hooks/usePersistentTableState.js`;
- `frontend/dashboards/src/lib/admissionsStartIntake.js`;
- `frontend/dashboards/src/lib/admissionsLifecycleState.js`;
- `frontend/dashboards/src/sandbox/sandboxTelemetry.js`.

Production values, expiry behavior, browser-cookie settings and actual user-device persistence remain runtime evidence requirements.

## Audit, logs and actor attribution

Source-visible audit records include action/event identifiers, actors, tenant or entity references, timestamps, narrative or JSON details and processing outcomes. Relevant paths include:

- `backend/audit/models.py`;
- `backend/core/models.py`;
- `backend/signals/models.py`;
- `backend/platform_ops/models.py`;
- `backend/analytics/models.py`.

This proves repository structures, not production log destinations, retention, tamper resistance, access control or incident-response use.

## Retention, deletion, purge and legal-hold controls

Verified repository paths include:

- `backend/core/models_retention.py`;
- `backend/core/services/retention_service.py`;
- `backend/core/tasks.py`;
- `backend/apps/compliance/management/commands/compliance_retention_review.py`;
- `tools/generate_retention_control_inventory.py`;
- `docs/compliance/RETENTION_POLICY.md`;
- `docs/compliance/DATA_RETENTION_POLICY.md`;
- `docs/compliance/BACKUP_RESTORE_POLICY.md`.

`TenantSafeModel.delete()` blocks hard deletion for tenant-owned models, ledger entries use reversals, and reviewed relations use `CASCADE`, `PROTECT` and `SET_NULL`. Current settings define `CROWN_BACKUP_RETENTION_DAYS` with a default of 30 days.

These are source and configuration facts only. Production enforcement, backup expiration, tenant-aware deletion propagation, anonymization, legal hold and customer-directed deletion remain operationally unverified.

## Integrations and external recipients

Repository paths confirm integration and recipient surfaces, including `backend/integrations/models.py`, communications, exports, authentication, payment-adjacent code and Microsoft identity/client configuration. Package names and source adapters do not prove active production vendors, subprocessors, regions or contractual authorization.

Every active external recipient must be verified from deployed configuration, contracts and runtime evidence before production authorization.

## Tenant and role boundaries

Reviewed models commonly contain school, tenant, student, family, household, user, role or actor relationships. This supports source-level ownership analysis but does not prove deployed object-level authorization, cross-tenant denial, asynchronous tenant binding or complete audit coverage. Those controls remain Lane 2 runtime requirements.

## Production and non-production handling

Sandbox/demo records and helper credentials must remain synthetic and segregated from production. Repository evidence distinguishes sandbox paths, but does not prove environment-level data separation, production configuration or non-production copy controls.

## Explicit unresolved operational dimensions

The following cannot be established from repository source alone and remain linked to #1629 and the applicable operational lanes:

1. active production vendors, processors, recipients and processing regions;
2. actual production database, file, log, analytics and backup locations;
3. runtime tenant and role enforcement for every object and export;
4. production browser/cookie values and expiration behavior;
5. executed retention, purge, anonymization and legal-hold behavior;
6. backup expiration and deletion propagation;
7. production incident-response ownership and notification execution;
8. executed customer contracts, DPAs and jurisdiction-specific legal review;
9. production payment activation, which remains disabled and fail closed;
10. complete deployed-system data-flow certification.

## Closure statement for #1759

The repository-bounded acceptance criteria for #1759 are satisfied by this record and its machine-readable companion:

- major data domains are enumerated from current source;
- known data subjects, purposes, source/storage paths and evidence status are identified;
- unknowns are explicit;
- processing, export, log, backup, retention and deletion gaps are linked to #1629;
- the result is controlled compliance supporting evidence rather than legal authority.

Field-exhaustive runtime-generated Django metadata would provide additional engineering detail but is not required to claim legal, operational or production completeness and is not substituted for deployed evidence.

This record does not close #1629, any runtime lane, or production authorization. Production remains **NOT APPROVED / NO-GO / HOLD**.
