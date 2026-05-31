# CROWN Core SIS Domain Model Certification — 2026-05-29

## Decision

**DOMAIN MODEL CERTIFICATION: NOT GREEN.**

This register defines the canonical core SIS entities that must be proven before CROWN can be certified as a complete core SIS. Presence of a page, route, dashboard, serializer, model name, migration, or app label is not sufficient.

## Certification standard

Each domain entity is certified only when all evidence exists for the reviewed commit:

1. Canonical model exists.
2. Migration exists and applies cleanly.
3. Tenant boundary is explicit.
4. Object-level authorization is proven.
5. Serializer/API surface exists where applicable.
6. UI/workflow usage exists where applicable.
7. Create/read/update/delete or lifecycle behavior is tested.
8. Audit fields or audit trail exist for sensitive changes.
9. Import/export behavior is defined where applicable.
10. Retention/deletion behavior is defined.
11. Runtime proof artifact exists.
12. Test evidence is current.

## Entity register

| Entity | Required purpose | Current certification status | Required evidence |
|---|---|---|---|
| Tenant / School | School data boundary and configuration root | NOT_GREEN | Tenant-scoped model/API/runtime tests |
| Academic Year | School year lifecycle | NOT_GREEN | Model, migration, rollover workflow, tests |
| Term / Marking Period | Grade/reporting period structure | NOT_GREEN | Model, setup wizard, report-card integration proof |
| Person | Shared identity foundation | NOT_GREEN | Canonical identity model or documented separation model |
| Student | Student record | NOT_GREEN | Model/API/UI/import/tenant/object auth proof |
| Applicant | Admissions lifecycle person | NOT_GREEN | Application-to-student conversion proof |
| Parent / Guardian | Family/guardian identity and portal access | NOT_GREEN | Relationship, permissions, portal proof |
| Household | Family grouping and billing/communications context | NOT_GREEN | Household wizard/API/UI proof |
| Staff / Faculty | Employee/teacher/admin user profile | NOT_GREEN | Staff onboarding, role assignment, permissions proof |
| User Account | Authentication/authorization principal | NOT_GREEN | Login, role claims, RBAC, tenant proof |
| Course | Academic course catalog | NOT_GREEN | Course catalog setup, section linkage, tests |
| Section | Scheduled instructional section | NOT_GREEN | Scheduling, roster, teacher, room proof |
| Enrollment | Student enrollment in school/year/grade/program | NOT_GREEN | Admissions/reenrollment/conversion proof |
| Attendance Record | Daily/class attendance fact | NOT_GREEN | Attendance entry, codes, reports, tenant proof |
| Assignment | Gradebook work item | NOT_GREEN | Teacher workflow and gradebook proof |
| Grade / Score | Student performance measure | NOT_GREEN | Grade entry, calculation, permission, audit proof |
| Grade Scale | Grade interpretation configuration | NOT_GREEN | Grade scale wizard and report-card integration |
| Report Card | Periodic academic report | NOT_GREEN | Generation, access, archive, parent/student visibility proof |
| Transcript | Longitudinal academic record | NOT_GREEN | Registrar workflow, export, audit proof |
| Invoice | Billing obligation | NOT_GREEN | Posting, immutability, adjustment, audit proof |
| Payment | Family/customer payment record | NOT_GREEN | Processor/reconciliation/refund proof |
| Financial Aid Application | Aid request and documents | NOT_GREEN | Privacy, award, review workflow proof |
| Financial Aid Award | Aid decision and tuition impact | NOT_GREEN | Award, approval, billing integration proof |
| Communication | School-to-family/staff/student messaging | NOT_GREEN | Delivery, opt-out, audit, role proof |
| Document / File | Uploaded/generated records | NOT_GREEN | Storage, access, retention, deletion proof |
| Health Visit | Health-office event | NOT_GREEN | Nurse role, privacy, parent notification, audit proof |
| Medication / Allergy | Health-sensitive record | NOT_GREEN | Restricted access and emergency visibility proof |
| Student Care Note | Counseling/intervention/private note | NOT_GREEN | Restricted access, audit, retention proof |
| Behavior / Incident | Discipline/safety event | NOT_GREEN | Workflow, notification, privacy proof |
| Activity / Team / Roster | Athletics/activities membership | NOT_GREEN | Eligibility, roster, schedule proof |
| Transportation Route / Rider | Transportation operations | NOT_GREEN | Route, stop, rider, communication proof |
| Food Service Account / Meal | Food service operations | NOT_GREEN | Meal count/charge/eligibility proof |
| Library Item / Loan | Library/media circulation | NOT_GREEN | Catalog, circulation, fine/fee proof |
| Volunteer Record | Volunteer relationship and approvals | NOT_GREEN | Approval, safety, hours proof |
| Alumni Record | Alumni constituent profile | NOT_GREEN | Communications/giving/event proof |
| Audit Log | Immutable operational/security record | NOT_GREEN | Sensitive action capture and tamper-resistant storage proof |

## Required evidence output

The certification process must produce:

```text
.crown-audit/domain-model/latest/00_SUMMARY.md
.crown-audit/domain-model/latest/10_entity_certification.csv
.crown-audit/domain-model/latest/20_missing_model_or_migration.csv
.crown-audit/domain-model/latest/30_missing_tenant_or_permission_proof.csv
.crown-audit/domain-model/latest/99_STATUS.json
```

## Status

Architecture register: **DOCUMENTED**

Domain certification: **NOT GREEN until every entity has current proof.**
