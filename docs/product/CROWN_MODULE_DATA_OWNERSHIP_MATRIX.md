# CROWN Module Data Ownership Matrix

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This matrix prevents duplicate truth across CROWN. Each module must declare what it owns, what it reads, what it may write back to Core, and what it must never duplicate.

A module cannot be certified until its data ownership row is complete and independently reviewed.

## Ownership Rules

1. Core owns institutional truth.
2. Modules own module-specific workflow records.
3. Add-ons may own mission or extension records, but may not duplicate SIS truth.
4. Dashboards own no operational truth.
5. Snapshots summarize data; they do not become canonical operational records.
6. Write-back to Core requires an approved service path.
7. Sensitive data requires classification, redaction, and audit rules.

## Matrix Columns

| Field | Meaning |
|---|---|
| Module Key | Stable module identifier. |
| Owns | Canonical records owned by this module. |
| Reads From Core | Core records read by this module. |
| Writes To Core | Core records this module may update. |
| Write Path | Approved service/API path for Core write-back. |
| Must Not Own | Records this module must never duplicate. |
| Emits Events | Events produced by this module. |
| Consumes Events | Events consumed by this module. |
| Audit Required | Actions requiring audit. |
| Sensitivity | Public/Internal/Restricted/Confidential/Highly Sensitive. |
| Rollover/Retention | Year-end, archive, purge, or retention rules. |
| Open Questions | Items blocking certification. |

## Core Ownership Baseline

| Core Area | Owns | Notes |
|---|---|---|
| tenant-context | School identity, tenant context, school status | No module may invent school context. |
| school-year-grade | Academic year, grade level, school calendar context | Required by enrollment, billing, attendance, gradebook. |
| family-guardian-household | Family, guardian, custody flag, portal access, household links | Billing, transportation, parent portal, admissions consume this. |
| student-master | Student identity, student number, DOB, status, current grade | All student-facing modules consume this. |
| staff-user-role | Staff identity, user identity, assigned roles | All role-based modules consume this. |
| enrollment-registrar | Enrollment by school/year/student/grade | Billing, rosters, attendance, gradebook consume this. |
| rbac-permissions | Permission codes and role grants | Every API/action consumes this. |
| audit | Audit trail | Modules emit audit events. |
| retention-rollover | Retention, purge, archive, year-end rules | Applies to all records. |

## Phase 1: Core SIS and Daily Operations

| Module Key | Owns | Reads From Core | Writes To Core | Must Not Own | Sensitivity | Open Questions |
|---|---|---|---|---|---|---|
| school-year-grade | Academic year, grade levels, calendar context | School | School setup only through admin controls | Student, family, billing data | Internal | Term model and rollover rules need verification. |
| staff-user-role | Staff records, user accounts, role assignments | School | User/staff/role updates | Student/family operational data | Restricted | Align backend role choices with frontend role groups. |
| family-guardian-household | Family, guardian, custody, household links | School | Family/guardian updates | Student academic/enrollment status | Confidential | Custody/portal access visibility rules need review. |
| student-master | Student identity/status/current grade | School, Family, GradeLevel | Student identity/status through approved registrar workflow | Billing ledger, attendance records, grades | Confidential | Status transition rules need formal lifecycle. |
| enrollment-registrar | Enrollment records by year, registration/withdrawal/graduation state | Student, AcademicYear, GradeLevel | Student status only through registrar-approved service | Billing charges, grades, attendance | Confidential | Re-enrollment and withdrawal side effects need event map. |
| courses-sections-rosters | Courses, sections, rosters, instructional membership | School, AcademicYear, Staff, Student, Enrollment | Roster membership only | Student identity, enrollment status | Restricted | Canonical roster model must be verified. |
| attendance | Attendance marks, daily attendance state, corrections | Student, Enrollment, Rosters, Staff | May notify student care; must not directly rewrite enrollment | Student identity, rosters, gradebook | Confidential | Correction workflow, audit, parent visibility, and freshness SLA needed. |
| gradebook | Assignments, grades, grade status, teacher grade workflows | Student, Staff, Sections, Enrollment | Official grade finalization may feed transcripts through approved service | Student identity, enrollment, transcript lock records | Confidential | Grade lock/finalization and parent visibility rules needed. |
| transcripts-reportcards | Official report cards, transcript records, graduation status | Student, Enrollment, Gradebook | Student graduation/alumni status through registrar-approved path | Raw assignment workflow | Highly Sensitive | Lock/reopen rules and audit depth needed. |
| student-care-discipline | Student care notes, discipline incidents, interventions | Student, Staff, Guardian | May update student care flags through approved service | Student identity, academic grades, billing | Highly Sensitive | Role redaction and small-cell dashboard suppression required. |

## Phase 2: Commercial Operating Modules

| Module Key | Owns | Reads From Core | Writes To Core | Must Not Own | Sensitivity | Open Questions |
|---|---|---|---|---|---|---|
| admissions | Applications, applicant pipeline, admissions checklist | Family, Guardian, Student applicant shell | Student applicant/admitted state only through enrollment service | Active enrollment truth, billing ledger | Confidential | Conversion path to Student/Enrollment needs exact proof. |
| re-enrollment | Returning-student intent, contract/checklist workflow | Student, Family, AcademicYear, Enrollment | Next-year enrollment through registrar-approved service | Billing ledger, student identity | Confidential | Year rollover and contract completion states needed. |
| billing-tuition-ledger | Tuition plans, student tuition, charges, payments, ledger entries, reversals | Family, Student, Enrollment, AcademicYear | May update account status; must not rewrite student identity | Student master, family address truth | Highly Sensitive | Payment provider, immutable ledger, export rules, and dashboard redaction needed. |
| financial-aid | Aid applications, awards, discounts, appeals | Student, Family, Admissions, Billing | Award impact to billing through approved service | Billing ledger transaction truth | Highly Sensitive | Award lifecycle and confidential access rules needed. |
| communications | Messages, announcements, delivery status, notification preferences if module-owned | Users, Roles, Families, Students, Staff | May update communication preferences through approved service | Student/family identity | Confidential | Delivery channels, opt-out, audit, and emergency rules needed. |
| parent-family-portal | Family-facing tasks/views, parent action queue if owned here | Guardian, Family, Student, Billing, Attendance, Gradebook | Limited family updates through approved service | Core records directly; must not bypass registrar/billing workflows | Confidential | Read/write boundaries and custody redaction needed. |
| teacher-portal | Teacher task queues and workflow views | Staff, Sections, Students, Attendance, Gradebook | Attendance/grade actions through module services | Student identity/enrollment | Confidential | Role scope by section/roster needed. |
| administrator-portal | Executive rollup views and leadership queues | All approved module summaries | None unless delegated to underlying module services | Operational source records | Restricted | Aggregate redaction and drilldown rules needed. |

## Phase 3: Operational Expansion Modules

| Module Key | Owns | Reads From Core | Writes To Core | Must Not Own | Sensitivity | Open Questions |
|---|---|---|---|---|---|---|
| scheduling | Schedule periods, placements, constraints | Staff, Students, Courses, Sections, Rooms if present | Roster updates only through approved academic service | Staff/student identity | Restricted | Conflict engine and room/location ownership needed. |
| activities-athletics | Teams, activities, rosters, events, eligibility workflow | Student, Staff, Attendance, Gradebook | Eligibility flags only through approved service if needed | Student academic or attendance truth | Confidential | Eligibility source and parent visibility needed. |
| health-office | Health visits, restrictions, medication/health alerts if implemented | Student, Guardian | Critical health flags through approved service | Student identity, guardian identity | Highly Sensitive | HIPAA-like access controls, redaction, and audit depth needed. |
| transportation | Routes, riders, stops, bus assignments | Student, Family, Address | None or address-change request only | Family address truth | Confidential | Address consumption and emergency contact rules needed. |
| food-service | Meal participation, menus, balances if module-owned | Student, Family, Billing account links | Billing charges only through billing service | Billing ledger truth | Confidential | Meal account boundary and privacy rules needed. |
| facilities | Work orders, rooms, maintenance tasks | School, Staff | None | School identity, staff identity | Internal | Location/asset model needed. |
| safety-security | Incidents, drills, safety tasks, security events | School, Student, Staff | Critical flags only through approved service | Student/staff identity | Highly Sensitive | Incident access, notification, and audit rules needed. |
| hr | Staff lifecycle, compliance, documents if implemented | Staff, User | Staff status through approved HR/user service | User authentication internals | Highly Sensitive | HR data separation and manager access rules needed. |
| it-support | Tickets, access requests, support queues | User, Staff, Platform Ops | Access changes only through approved identity path | User identity source of truth | Restricted | Escalation and audit rules needed. |

## Phase 4: Enrichment, Mission, Advancement

| Module Key | Owns | Reads From Core | Writes To Core | Must Not Own | Sensitivity | Open Questions |
|---|---|---|---|---|---|---|
| fine-arts | Ensembles, events, participation | Student, Staff, Schedule | None or participation flags only | Student identity, grades | Internal/Confidential | Roster/event model needed. |
| library-media | Resources, circulation, holds, media activity | Student, Staff | None | Student identity | Confidential | Circulation privacy and overdue rules needed. |
| extended-care | Care sessions, attendance, billing-adjacent records | Student, Family, Billing | Charges only through billing service | Billing ledger, student identity | Confidential | Attendance/billing interface needed. |
| summer-camp | Camp sessions, rosters, camp setup | Family, Student, Billing | Charges only through billing service | Core student/family truth | Confidential | Seasonal lifecycle and dashboard source needed. |
| spiritual-life | Chapel, discipleship, chaplaincy workflows as appropriate | Student, Staff | None unless approved mission flags exist | Student identity, academic/discipline truth | Highly Sensitive | Pastoral confidentiality rules required. |
| service-outreach-portrait | Service hours, outreach participation, portrait goals | Student, Staff | Graduation/portrait completion only through approved service | Student academic record truth | Confidential | Approval workflow and graduation linkage needed. |
| volunteer-management | Volunteer profiles, opportunities, approvals | Guardian, Family | Approved volunteer status through module service | Guardian identity/custody truth | Highly Sensitive | Background check and restricted access rules needed. |
| advancement-operations | Donors, campaigns, gifts if implemented | Families, Alumni, Board | None to Core unless constituent link approved | Student/family identity | Highly Sensitive | Donor privacy and finance boundary needed. |
| alumni-relations | Alumni engagement records | Graduated students, families | Alumni link only through approved registrar process | Student academic record truth | Confidential | Alumni conversion and contact rules needed. |
| board-governance | Board packets, decisions, governance tasks | School, Finance summaries, Advancement summaries | None to Core | Operational source records | Highly Sensitive | Board access boundaries and export rules needed. |
| curriculum-pd | Curriculum maps, PD records | Staff, Academics | None or approved staff PD completion flags | Staff identity | Restricted | Curriculum ownership and versioning needed. |
| network-benchmarking | Anonymized/aggregated benchmark data | Certified module metrics | None to tenant source records | Identifiable student/family/staff data | Highly Sensitive | Anonymization and small-cell suppression rules required. |

## Phase 5: Platform Operations

| Module Key | Owns | Reads From Core | Writes To Core | Must Not Own | Sensitivity | Open Questions |
|---|---|---|---|---|---|---|
| implementation-success | Onboarding state, launch readiness | Tenant, modules, support | None unless setup workflow approved | Customer production records | Internal/Restricted | Customer readiness metric source needed. |
| data-migration | Import jobs, mappings, validation errors | Core schema | Core writes only through validated import services | Manual duplicate records | Highly Sensitive | Backfill and rollback plan needed. |
| integrations-automation | Sync jobs, connector state, automation logs | Module APIs | Writes only through module APIs | Canonical source records directly | Highly Sensitive | Retry, dedupe, and external failure rules needed. |
| compliance-audit | Compliance evidence, exceptions | Audit, release evidence | None | Source operational records | Restricted | Exception workflow and evidence retention needed. |
| revenue-operations | Internal CROWN account/revenue ops | Subscriptions, payments | None to customer module records | School operational data | Restricted | Separation from school data needed. |
| release-reliability | Release health, gate evidence | CI/evidence systems | None | Product module records | Internal | Current-head gate source required. |
| dashboard-certification-center | Certification visibility | Dashboard registry/certification registry | None | Dashboard source records | Internal | Must prove live derivation from registries and no template contamination. |

## Certification Blockers

A module data ownership row blocks certification if any of these are unresolved:

- canonical owner unknown
- Core write-back path unknown
- duplicate truth risk unresolved
- sensitive data classification missing
- retention/rollover rule missing
- event side effects undefined
- audit requirements undefined
- dashboard data source unclear
- independent review missing
