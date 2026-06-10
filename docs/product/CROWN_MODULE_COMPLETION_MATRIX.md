# CROWN Module Completion Matrix

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This matrix tracks CROWN module completion from inventory through certification. It is a planning and evidence-control document. It is not release approval and does not override the current repository release posture.

A module is not complete until its row is evidence-backed, independently reviewed, and marked Certified.

## Status Vocabulary

| Status | Meaning |
|---|---|
| Inventory | Repo surface exists: app, route, component, registry row, or documented concept. |
| Schema-visible | Models or data structures are visible and mapped. |
| Wired | Backend service/API, frontend route, permission path, and dashboard mapping are connected. |
| Runtime-visible | The module can be exercised in a running environment. |
| Evidence-backed | Current tests and runtime artifacts prove the claimed behavior. |
| Certified | Independent review and all required proof are complete. |

## Matrix Columns

Each module row must be completed using these fields:

| Field | Meaning |
|---|---|
| Order | Completion order. |
| Phase | Control, Core, Commercial, Operations, Mission, or Platform Ops. |
| Module Key | Stable module identifier. |
| Module Name | User-facing module name. |
| Layer | Core, Module, Add-on, or Platform Ops. |
| Repo Surface | Existing app/model/frontend/dashboard evidence. |
| Core Dependencies | Core records required. |
| Module-Owned Records | Data owned by this module. |
| Backend App | Canonical backend app/service. |
| Models Verified | Yes/No/Partial/Unknown. |
| Service Layer Verified | Yes/No/Partial/Unknown. |
| API Verified | Yes/No/Partial/Unknown. |
| Frontend Surface | Route/page/component surface. |
| Dashboard Key | Related dashboard key, if any. |
| Dashboard Cert Status | Scaffold/Hybrid/Live/Certified/None. |
| Persona Roles | Primary roles/personas. |
| Action Permissions Needed | View/create/edit/approve/delete/export/etc. |
| Tenant Proof Needed | Required tenant-bound tests. |
| Audit Events Needed | Required audit events. |
| Runtime Proof Needed | Required smoke/UI/API proof. |
| Current Status | Inventory/Schema-visible/Wired/Runtime-visible/Evidence-backed/Certified. |
| Blocking Questions | Items that block promotion. |
| Next Action | Next planning or verification action. |
| Independent Reviewer | Reviewer required before certification. |

## Phase 0: Control Layer

| Order | Module Key | Module Name | Layer | Repo Surface | Current Status | Next Action |
|---:|---|---|---|---|---|---|
| 0.1 | tenant-context | Tenant / School Context | Core | `core`, `tenants`, tenant middleware | Schema-visible | Verify strict tenant resolution for every module and dashboard endpoint. |
| 0.2 | identity-roles | Identity / Users / Roles | Core | `UserAccount`, `UserRole`, dashboard role groups | Schema-visible | Align frontend role groups with backend role/permission codes. |
| 0.3 | rbac-permissions | RBAC / CrownPermission / RolePermission | Core | `CrownPermission`, `RolePermission` | Schema-visible | Define action-level permission matrix. |
| 0.4 | audit | Audit Logging | Core | `audit` app and middleware | Inventory | Define module audit event catalog. |
| 0.5 | entitlements | Entitlements / Subscriptions | Core | `subscriptions`, `payments` | Inventory | Define module enablement and entitlement checks. |
| 0.6 | retention-rollover | Retention / Rollover | Core | retention models imported in core | Inventory | Define module retention, archival, and year-end rules. |
| 0.7 | dashboard-certification | Dashboard Certification Contract | Platform Ops | dashboard certification registry, module readiness guard | Inventory | Enforce live-data/provenance certification rules. |

## Phase 1: Core SIS Truth

| Order | Module Key | Module Name | Layer | Repo Surface | Core Dependencies | Dashboard Key | Current Status | Next Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | school-year-grade | School / Academic Year / Grade Level | Core | `School`, `AcademicYear`, `GradeLevel` | Tenant context | registrar, school-administrator | Schema-visible | Verify APIs, admin workflows, rollover behavior, and tenant tests. |
| 2 | staff-user-role | Staff / User / Role | Core | `Staff`, `UserAccount`, `UserRole` | School | hr, school-administrator | Schema-visible | Align role choices, frontend role groups, and permission capabilities. |
| 3 | family-guardian-household | Family / Guardian / Household | Core | `Family`, `Guardian`, `HouseholdFamilyLink` | School | parent/family, registrar | Schema-visible | Verify custody flags, portal access, household mapping, and parent scoping. |
| 4 | student-master | Student Master Record | Core | `Student` | Family, GradeLevel, School | registrar, student-care | Schema-visible | Verify status lifecycle and downstream references. |
| 5 | enrollment-registrar | Enrollment / Registrar | Core | `Enrollment`, `student_records`, registrar dashboard | Student, AcademicYear, GradeLevel | registrar | Schema-visible | Verify APIs, enrollment transitions, documents, and dashboard summary source. |
| 6 | courses-sections-rosters | Courses / Sections / Rosters | Core | `academics`, `classroom`, `curricula` | School, AcademicYear, Staff, Student | scheduling, gradebook | Inventory | Map canonical models and roster ownership. |
| 7 | attendance | Attendance | Module | attendance dashboard, dashboard snapshot/sample surface | Student, Enrollment, Rosters | attendance | Inventory/Hybrid dashboard | Verify attendance model/API/service and live dashboard summary. |
| 8 | gradebook | Gradebook | Module | `gradebook`, gradebook dashboard | Courses, Sections, Students, Staff | gradebook | Inventory | Verify models, assignment/grade lifecycle, teacher permissions, dashboard source. |
| 9 | transcripts-reportcards | Transcript / Report Card / Graduation | Module | `graduation`, `student_records` | Student, Enrollment, Gradebook | registrar, academic | Inventory | Map official record ownership and lock rules. |
| 10 | student-care-discipline | Student Care / Discipline | Module | `discipline`, `student_records`, `student360` | Student, Staff, Guardian | student-care | Inventory | Define sensitive-data policy, role redaction, and audit events. |

## Phase 2: First Commercial Operating Modules

| Order | Module Key | Module Name | Layer | Repo Surface | Core Dependencies | Dashboard Key | Current Status | Next Action |
|---:|---|---|---|---|---|---|---|---|
| 11 | admissions | Admissions | Module | `admissions`, `applications`, admissions dashboard | Family, Guardian, Student applicant state | admissions | Inventory | Verify application pipeline, family linkage, and enrollment conversion. |
| 12 | re-enrollment | Re-enrollment | Module | enrollment/applications workflow surface | Student, Family, AcademicYear | registrar, school-administrator | Inventory | Define returning-student intent and next-year enrollment rules. |
| 13 | billing-tuition-ledger | Billing / Tuition / Ledger | Module | `billing`, `finance`, `ledger`, `TuitionPlan`, `StudentTuition`, `LedgerEntry` | Family, Student, Enrollment, AcademicYear | billing | Schema-visible | Verify ledger immutability, account model, payment integration, dashboard source. |
| 14 | financial-aid | Financial Aid | Module | `aid`, `financial_aid`, financial-aid dashboard | Admissions, Family, Student, Billing | financial-aid | Inventory | Verify award lifecycle and billing impact. |
| 15 | communications | Communications | Module | `comms`, communications dashboard | Users, roles, families, staff, students | communications | Inventory | Verify message model, delivery state, notifications, and role targeting. |
| 16 | parent-family-portal | Parent / Family Portal | Module | `parent360`, guardian portal access | Guardian, Family, Student, Billing, Attendance, Gradebook | parent/family | Inventory | Define family action queue and sensitive visibility rules. |
| 17 | teacher-portal | Teacher Portal | Module | classroom/gradebook/attendance surfaces | Staff, Sections, Students | teacher/academic | Inventory | Define teacher daily workflow and direct access rules. |
| 18 | administrator-portal | Administrator Portal | Module | `executive360`, school admin dashboard | All core modules | school-administrator | Inventory | Define executive rollup source and redaction rules. |

## Phase 3: Operational Expansion Modules

| Order | Module Key | Module Name | Layer | Repo Surface | Core Dependencies | Dashboard Key | Current Status | Next Action |
|---:|---|---|---|---|---|---|---|---|
| 19 | scheduling | Scheduling | Module | scheduling dashboard, academics/classroom surface | Courses, Sections, Staff, Students | scheduling | Inventory | Verify schedule builder and conflict rules. |
| 20 | activities-athletics | Activities / Athletics | Module | `athletics`, activities-athletics and athletics-director dashboards | Students, Staff, Attendance, Gradebook | activities-athletics, athletics-director | Inventory | Verify rosters, events, eligibility, and dashboard source. |
| 21 | health-office | Health Office | Module | health-office dashboard, safety surface | Student, Guardian | health-office | Inventory | Define sensitive health data handling and access rules. |
| 22 | transportation | Transportation | Module | `transportation`, transportation dashboard | Student, Family, Address | transportation | Inventory | Verify route/rider ownership and family address consumption. |
| 23 | food-service | Food Service | Module | food-service dashboard | Student, Family, Billing/account links | food-service | Inventory | Verify meal/account model and billing boundary. |
| 24 | facilities | Facilities | Module | `facops`, facilities dashboard | School, Staff | facilities | Inventory | Verify work orders, locations, and maintenance workflow. |
| 25 | safety-security | Safety / Security | Module | `safety`, safety-security dashboard | Student, Staff, School | safety-security | Inventory | Verify incident/drill/security workflows and audit rules. |
| 26 | hr | HR | Module | `hr`, HR dashboard | Staff, User | hr | Inventory | Verify staff lifecycle and compliance records. |
| 27 | it-support | IT Support | Module | `support`, IT dashboard | Users, Staff, Platform Ops | it-support | Inventory | Verify ticket/access workflow and escalation rules. |

## Phase 4: Enrichment, Mission, and Advancement

| Order | Module Key | Module Name | Layer | Repo Surface | Core Dependencies | Dashboard Key | Current Status | Next Action |
|---:|---|---|---|---|---|---|---|---|
| 28 | fine-arts | Fine Arts | Module | fine-arts dashboard | Students, Staff, Schedule | fine-arts | Inventory | Verify participation, events, and roster data. |
| 29 | library-media | Library / Media | Module | library-media dashboard | Students, Staff | library-media | Inventory | Verify circulation/resource model. |
| 30 | extended-care | Extended Care | Module | `aftercare`, extended-care dashboard | Student, Family, Billing | extended-care | Inventory | Verify care sessions, attendance, and billing link. |
| 31 | summer-camp | Summer Camp | Module | `summer_camp`, summer-camp dashboard | Family, Student, Billing | summer-camp | Inventory | Verify seasonal setup, roster, and billing boundary. |
| 32 | spiritual-life | Spiritual Life / Chaplaincy | Add-on | `spiritual_life`, chaplain-spiritual-life dashboard | Student, Staff | chaplain-spiritual-life | Inventory | Define mission data boundaries and sensitive pastoral access. |
| 33 | service-outreach-portrait | Service / Outreach / Portrait | Add-on | `servicehours`, `portrait`, `outreach` | Student, Staff | portrait-service | Inventory | Verify service hours, outreach, and portrait goal ownership. |
| 34 | volunteer-management | Volunteer Management | Module/Add-on | volunteer-management dashboard | Guardian, Family | volunteer-management | Inventory | Verify approvals, background checks, opportunities, and event links. |
| 35 | advancement-operations | Advancement Operations | Module | `advancement`, advancement dashboards | Families, Alumni, Board | advancement, advancement-operations | Inventory | Verify donor/campaign/gift boundaries. |
| 36 | alumni-relations | Alumni Relations | Module/Add-on | alumni-relations dashboard | Graduated Students, Families | alumni-relations | Inventory | Define alumni conversion from student records. |
| 37 | board-governance | Board Governance | Add-on | `board_oversight`, school-board dashboard | School, Finance, Advancement | school-board | Inventory | Verify governance packet and board access rules. |
| 38 | curriculum-pd | Curriculum / PD | Module/Add-on | `curriculum`, `pdhub`, curriculum-pd dashboard | Staff, Academics | curriculum-pd | Inventory | Verify curriculum map and PD ownership. |
| 39 | network-benchmarking | Network Benchmarking / Analytics | Add-on | `analytics`, network-benchmarking dashboard | Certified anonymized data | network-benchmarking | Inventory | Define anonymization, aggregation, and small-cell suppression. |

## Phase 5: Platform Operations

| Order | Module Key | Module Name | Layer | Repo Surface | Dependencies | Dashboard Key | Current Status | Next Action |
|---:|---|---|---|---|---|---|---|---|
| 40 | implementation-success | Implementation Success | Platform Ops | implementation-success dashboard | Tenant, Migration, Support | implementation-success | Inventory | Define onboarding lifecycle and customer readiness metrics. |
| 41 | data-migration | Data Migration | Platform Ops | data-migration dashboard | Core schema | data-migration | Inventory | Define import validation, mapping, and backfill proof. |
| 42 | integrations-automation | Integrations / Automation | Platform Ops | `integrations`, `integrations_real`, integrations dashboard | Module APIs | integrations-automation | Inventory | Define sync jobs, external API contracts, and retry rules. |
| 43 | compliance-audit | Compliance Audit | Platform Ops | compliance app, compliance-audit dashboard | Audit, Release Evidence | compliance-audit | Inventory | Define compliance evidence and exception workflow. |
| 44 | revenue-operations | Revenue Operations | Platform Ops | revenue-operations dashboard | Subscriptions, Payments | revenue-operations | Inventory | Define internal revenue/account workflow. |
| 45 | release-reliability | Release Reliability | Platform Ops | release-reliability dashboard | CI/evidence gates | release-reliability | Inventory/Hybrid dashboard | Verify current-head evidence source and sample fallback removal. |
| 46 | dashboard-certification-center | Dashboard Certification Center | Platform Ops | dashboard-certification-center | Dashboard registry/certification registry | dashboard-certification-center | Inventory/Live dashboard | Verify no template contamination and runtime derivation from registries. |

## First Completion Batch

The first completion batch is:

1. School / Academic Year / Grade Level
2. Staff / User / Role
3. Family / Guardian / Household
4. Student Master Record
5. Enrollment / Registrar
6. Courses / Sections / Rosters
7. Attendance
8. Billing / Tuition / Ledger
9. Gradebook
10. Communications

These rows must be fully mapped before later modules are promoted.

## Promotion Requirements

A row cannot move to Certified unless all are true:

- backend app/service verified
- models verified
- API verified
- frontend workflow verified
- tenant enforcement tested
- action-level permissions tested
- audit events defined and tested where required
- dashboard source is live or certified snapshot, if applicable
- runtime proof current
- evidence path attached
- independent reviewer signoff recorded
