# CROWN Module Permission Matrix

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

> **Implementation authority:** This is a **target control-design matrix**, not an
> inventory of currently seeded permissions. Live permission authority is the current
> `backend/core/management/commands/seed_permissions.py` registry together with
> backend permission enforcement and its tests. A permission name in this planning
> matrix must not be represented as implemented until those sources prove it.

### Current naming / convergence exceptions

- Re-enrollment staff management currently enforces tenant-scoped
  `admissions.edit` or `admin.view`; guardian family actions are separately
  account/household scoped. The target `reenrollment.*` taxonomy is not currently seeded.
- Financial-aid runtime currently uses `financial_aid.view`,
  `financial_aid.edit`, and `financial_aid.view_rationale`. The target naming in
  this matrix is planning vocabulary until deliberately reconciled.
- Other target permissions below likewise require implementation and tests before
  certification; this document alone does not create or prove an authorization control.

## Purpose

This matrix defines action-level permissions for CROWN modules and dashboards. Page-level access is not sufficient. Hidden navigation is not security. Every module action, dashboard summary, drilldown, and export must enforce backend permission checks.

A module cannot be certified until its action-level permission row is complete and tested.

## Permission Code Pattern

Permission codes should follow this pattern:

```text
<module_key>.<action>
```

Examples:

```text
attendance.view
attendance.create
attendance.correct
attendance.export
billing.view
billing.adjust
billing.reverse
billing.export
student-care.view_restricted
health-office.view_restricted
```

## Standard Actions

| Action | Meaning |
|---|---|
| view | View module landing/list/summary. |
| view_restricted | View sensitive or restricted fields. |
| create | Create records. |
| edit | Edit records. |
| submit | Submit workflow step. |
| approve | Approve workflow step. |
| reject | Reject workflow step. |
| correct | Correct previously submitted records. |
| delete | Delete where allowed. Most tenant-owned records should use soft-delete/reversal instead. |
| archive | Archive or close records. |
| reopen | Reopen closed records. |
| export | Export records or reports. |
| configure | Configure module settings. |
| certify | Certify dashboard/module evidence. |
| administer | Full module administration. |

## Global Rules

1. Authentication is required for all production-visible module and dashboard routes.
2. Tenant context is required for all tenant-owned module APIs.
3. Module entitlement is required before route, API, dashboard, drilldown, or export access.
4. Dashboard access must enforce permission by dashboard key.
5. Direct URL access must be tested; navigation visibility is not authorization.
6. Exports require explicit `export` permission and audit events.
7. Restricted data requires `view_restricted` or a stronger module-specific permission.
8. Cross-tenant access attempts must be denied and logged.
9. Super/admin roles do not bypass data classification unless policy grants them access.
10. Independent review is required for permission matrix changes affecting sensitive modules.

## Persona Groups

The dashboard registry currently identifies persona groups including:

- super admin
- master control
- school admin
- board member
- finance team
- registrar team
- attendance team
- academic team
- admissions team
- advancement team
- HR team
- facilities team
- health team
- transportation team
- food service team
- IT team
- fine arts team
- athletics team
- library/media team
- extended care team
- summer camp team
- safety/security team
- curriculum/PD team
- chaplain/spiritual life team
- volunteer team
- portrait/service team
- alumni team
- implementation team
- data operations team
- integrations team
- compliance team
- revenue operations team
- release/platform engineering team
- platform certification team

These frontend role groupings must be aligned to backend `UserRole`, `CrownPermission`, and `RolePermission` records before certification.

## Phase 0: Control Layer Permissions

| Module Key | Target Permissions | Primary Roles | Sensitive Notes | Required Tests |
|---|---|---|---|---|
| tenant-context | tenant.view, tenant.configure, tenant.switch, tenant.audit | super_admin, master_control, school_admin | Tenant switching is high risk. | cross-tenant deny, tenant header required, wrong school blocked |
| identity-roles | identity.view, identity.create, identity.edit, identity.disable, identity.assign_role | super_admin, master_control, school_admin, hr_manager where appropriate | Role assignment can escalate privileges. | unauthorized role assignment blocked, audit event logged |
| rbac-permissions | permissions.view, permissions.edit, permissions.seed, permissions.audit | super_admin, master_control, platform_certification | Changes affect all modules. | permission mutation audit, non-admin denied |
| audit | audit.view, audit.export, audit.view_sensitive | compliance, master_control, school_admin limited | Audit may contain sensitive values. | export audited, sensitive fields redacted |
| entitlements | entitlements.view, entitlements.configure | super_admin, master_control, revenue_ops | Controls module availability. | disabled module route/API blocked |
| retention-rollover | retention.view, retention.configure, retention.run, retention.audit | compliance, master_control, school_admin limited | Purge/archive actions are high risk. | destructive action protected and audited |
| dashboard-certification | dashboard-cert.view, dashboard-cert.certify, dashboard-cert.revoke | platform_certification, compliance, release_team | Cannot be self-approved. | certification requires reviewer and evidence |

## Phase 1: Core SIS Permissions

| Module Key | Target Permissions | Primary Roles | Restricted Access | Required Tests |
|---|---|---|---|---|
| school-year-grade | school-year.view, school-year.configure, grade-level.configure | school_admin, registrar, master_control | Setup affects all modules. | unauthorized setup blocked; tenant-scoped setup only |
| staff-user-role | staff.view, staff.create, staff.edit, staff.disable, staff.export | school_admin, hr_manager | Staff HR details may be restricted. | staff from another school blocked; export audited |
| family-guardian-household | family.view, family.create, family.edit, guardian.view, guardian.edit, guardian.view_custody | registrar, admissions, school_admin | Custody flags and contact data restricted. | custody visible only to authorized roles |
| student-master | student.view, student.create, student.edit, student.change_status, student.export | registrar, school_admin | DOB/status restricted; exports audited. | status changes audited; cross-tenant student blocked |
| enrollment-registrar | enrollment.view, enrollment.create, enrollment.edit, enrollment.withdraw, enrollment.graduate, enrollment.export | registrar, school_admin | Enrollment transitions affect billing/academics. | lifecycle transition tests and event audit |
| courses-sections-rosters | academics.view, courses.configure, sections.configure, rosters.edit | academic_admin, registrar, school_admin | Roster scope affects teacher access. | teacher sees only assigned rosters |
| attendance | attendance.view, attendance.submit, attendance.correct, attendance.export, attendance.dashboard | attendance_admin, registrar, school_admin, teacher scoped | Student presence is confidential. | teacher scope, correction audit, export audit |
| gradebook | gradebook.view, gradebook.create, gradebook.edit, gradebook.submit, gradebook.finalize, gradebook.export | teacher scoped, academic_admin, school_admin | Student grades restricted. | teacher section scope; parent/student visibility rules |
| transcripts-reportcards | transcript.view, transcript.generate, transcript.lock, transcript.reopen, transcript.export | registrar, academic_admin, school_admin | Official records highly sensitive. | lock/reopen audit; export permission required |
| student-care-discipline | student-care.view, student-care.view_restricted, student-care.create, student-care.edit, student-care.close, student-care.export | student_care, school_admin limited | Highly sensitive; role redaction required. | restricted notes hidden from unauthorized users |

## Phase 2: Commercial Operating Permissions

| Module Key | Target Permissions | Primary Roles | Restricted Access | Required Tests |
|---|---|---|---|---|
| admissions | admissions.view, admissions.create, admissions.edit, admissions.approve, admissions.reject, admissions.export | admissions_manager, school_admin | Applicant/family data confidential. | applicant conversion audited; exports permissioned |
| re-enrollment | reenrollment.view, reenrollment.configure, reenrollment.submit, reenrollment.approve, reenrollment.export | registrar, admissions, school_admin | Contract data confidential. | parent submission scope; school approval audit |
| billing-tuition-ledger | billing.view, billing.create_charge, billing.adjust, billing.reverse, billing.export, billing.dashboard | finance_admin, school_admin limited | Highly sensitive financial data. | reversal not delete; small-cell dashboard suppression |
| financial-aid | financial-aid.view, financial-aid.view_restricted, financial-aid.award, financial-aid.approve, financial-aid.export | aid_director, finance_admin limited, school_admin limited | Highly sensitive. | restricted awards hidden; award-to-billing path audited |
| communications | communications.view, communications.create, communications.send, communications.approve, communications.export | school_admin, communications_director, teacher scoped | Messages may include student data. | role-targeting, emergency override, delivery audit |
| parent-family-portal | parent.view, parent.submit, parent.update_contact_request, parent.pay, parent.message | parent, guardian | Custody and restricted notes must be enforced. | guardian sees only linked students and permitted fields |
| teacher-portal | teacher.view, teacher.attendance, teacher.gradebook, teacher.message | teacher | Teacher scope is roster/section bounded. | direct URL outside roster blocked |
| administrator-portal | admin.view, admin.dashboard, admin.drilldown, admin.export | school_admin, head_of_school | Aggregates may reveal sensitive data. | redaction and drilldown permission tests |

## Phase 3: Operational Expansion Permissions

| Module Key | Target Permissions | Primary Roles | Restricted Access | Required Tests |
|---|---|---|---|---|
| scheduling | scheduling.view, scheduling.configure, scheduling.edit, scheduling.publish | registrar, academic_admin, school_admin | Schedule changes affect many modules. | conflict publish test; unauthorized publish blocked |
| activities-athletics | activities.view, activities.edit, athletics.view, athletics.edit, athletics.eligibility | athletics_director, student_life, school_admin | Eligibility may expose grades/attendance. | eligibility redacted by role |
| health-office | health.view, health.view_restricted, health.create, health.edit, health.export | nurse, health_office, school_admin restricted | Highly sensitive health data. | restricted health access and audit tests |
| transportation | transportation.view, transportation.edit, transportation.export | transportation_manager, school_admin | Address and rider data confidential. | family scope and route export audit |
| food-service | food.view, food.edit, food.charge, food.export | food_service_manager, finance_admin limited | Student participation/account data confidential. | billing boundary and export tests |
| facilities | facilities.view, facilities.create, facilities.assign, facilities.close | facilities_manager, school_admin | Internal operations. | work order tenant scope |
| safety-security | safety.view, safety.view_restricted, safety.create, safety.close, safety.export | safety_manager, security_officer, school_admin restricted | Highly sensitive incident data. | incident redaction and audit tests |
| hr | hr.view, hr.view_restricted, hr.create, hr.edit, hr.export | hr_manager, school_admin restricted | Highly sensitive staff data. | HR restricted data hidden from general admins |
| it-support | support.view, support.create, support.assign, support.close, support.escalate | it_support, master_control, school_admin limited | May include access/security details. | access request audit and escalation tests |

## Phase 4: Enrichment, Mission, Advancement Permissions

| Module Key | Target Permissions | Primary Roles | Restricted Access | Required Tests |
|---|---|---|---|---|
| fine-arts | fine-arts.view, fine-arts.edit, fine-arts.export | fine_arts_director, school_admin | Student participation confidential. | roster scope/export tests |
| library-media | library.view, library.edit, library.export | librarian, media_specialist, school_admin | Student borrowing data restricted. | circulation visibility tests |
| extended-care | extended-care.view, extended-care.checkin, extended-care.checkout, extended-care.charge, extended-care.export | extended_care_manager, school_admin, finance limited | Childcare records confidential. | pickup/custody and billing boundary tests |
| summer-camp | summer-camp.view, summer-camp.configure, summer-camp.roster, summer-camp.charge, summer-camp.export | summer_camp_coordinator, extended_care_manager, school_admin | Seasonal student/family data confidential. | session scope and billing boundary tests |
| spiritual-life | spiritual-life.view, spiritual-life.view_restricted, spiritual-life.create, spiritual-life.export | chaplain, spiritual_life, school_admin restricted | Pastoral information highly sensitive. | restricted pastoral notes hidden and audited |
| service-outreach-portrait | service.view, service.approve, portrait.view, portrait.edit, portrait.export | service_learning_coordinator, school_admin | Student service/mission data confidential. | approval and graduation linkage tests |
| volunteer-management | volunteer.view, volunteer.approve, volunteer.reject, volunteer.export | volunteer_coordinator, school_admin | Background check/eligibility highly sensitive. | restricted volunteer status tests |
| advancement-operations | advancement.view, advancement.view_restricted, advancement.edit, advancement.export | advancement_officer, school_admin restricted | Donor/gift data highly sensitive. | donor privacy and export audit |
| alumni-relations | alumni.view, alumni.edit, alumni.export | alumni_relations, advancement_officer | Alumni contact data confidential. | alumni conversion and export tests |
| board-governance | board.view, board.view_restricted, board.packet, board.export | board_member, school_admin restricted, master_control | Board packets highly sensitive. | board-only access and export audit |
| curriculum-pd | curriculum.view, curriculum.edit, pd.view, pd.approve, pd.export | curriculum_director, pd_coordinator, school_admin | Staff PD data restricted. | staff visibility and PD approval tests |
| network-benchmarking | benchmark.view, benchmark.configure, benchmark.export | platform_leadership, master_control | Anonymized data must stay anonymized. | small-cell suppression and de-identification tests |

## Phase 5: Platform Ops Permissions

| Module Key | Target Permissions | Primary Roles | Restricted Access | Required Tests |
|---|---|---|---|---|
| implementation-success | implementation.view, implementation.edit, implementation.export | implementation_team, master_control | Customer onboarding data restricted. | customer/tenant scope tests |
| data-migration | migration.view, migration.run, migration.rollback, migration.export | data_ops, master_control | Imported data highly sensitive. | rollback, validation, and audit tests |
| integrations-automation | integrations.view, integrations.configure, integrations.run, integrations.retry | integrations_team, it_team, master_control | API secrets and sync data highly sensitive. | secret redaction and retry/dedupe tests |
| compliance-audit | compliance.view, compliance.exception, compliance.export | compliance_team, master_control | Evidence may expose security gaps. | exception workflow audit tests |
| revenue-operations | revenue.view, revenue.edit, revenue.export | revenue_ops, master_control | Internal business ops restricted. | customer data separation tests |
| release-reliability | release.view, release.evidence, release.certify | release_team, platform_certification | Release evidence controls GO/NO-GO support. | current-head evidence and stale-proof rejection tests |
| dashboard-certification-center | dashboard-cert.view, dashboard-cert.certify, dashboard-cert.revoke | platform_certification, compliance, release_team | Cannot be self-approved. | independent reviewer required |

## Certification Blockers

A permission row blocks certification if any of these are unresolved:

- frontend role group not mapped to backend permission
- direct URL access not tested
- tenant boundary not tested
- dashboard access not checked by key
- export permission missing
- sensitive field redaction missing
- small-cell suppression missing where applicable
- action audit missing
- independent review missing
