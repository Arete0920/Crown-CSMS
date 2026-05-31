# CROWN Final 95+ Module Implementation Sequence - 2026-05-30

Status: ACTIVE FINAL-SPRINT EXECUTION ORDER
Authority: Non-shipping execution control until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This sequence defines the order for completing CROWN to 95+ without scattering effort across unrelated modules or creating noisy partial fixes.

The order is based on dependency gravity: identity and tenant controls first, then canonical data spine, then admissions/enrollment/finance, then academic and operational modules, then platform/compliance/release proof.

## Execution rule

Do not start broad implementation in a lower sequence while a higher sequence has failing P0 gates, unless the lower-sequence task is required to fix the higher-sequence blocker.

## Sequence 0 - Evidence baseline

Status: NOT DONE until local evidence exists.

Required:

1. Run VS Code evidence pack.
2. Commit evidence root.
3. Identify first failing gate.
4. Do not update release authority until evidence is green.

## Sequence 1 - Identity, tenant, RBAC, object permissions

Status: NOT DONE

Reason this comes first:

All other module completion depends on correct school, user, role, and object scoping.

Required closure:

- Backend role code inventory.
- Frontend role alias inventory.
- Route-to-role matrix.
- API-to-permission matrix.
- Object ownership model for student/family/household/finance/aid/admissions records.
- Tenant/RBAC/object negative tests.

Exit artifacts:

- `FINAL_ROLE_PERMISSION_MATRIX.md`
- `FINAL_ROUTE_GUARD_AUDIT.md`
- `FINAL_BACKEND_PROTECTED_SPINE_PACKET.md`

## Sequence 2 - Core SIS data spine

Status: NOT DONE

Reason this comes second:

Admissions, enrollment, attendance, gradebook, billing, parent portals, and reports all depend on student/family/guardian/household correctness.

Required closure:

- Student records.
- Family/guardian/household records.
- Household-family linking.
- Parent/student scope.
- Staff scope.
- Imports/exports.
- Audit trail.

Exit artifacts:

- `FINAL_CORE_SIS_ACCEPTANCE.md`
- `FINAL_DATA_FLOW_MAP.md`

## Sequence 3 - Admissions to enrollment golden path

Status: NOT DONE

Required closure:

- Public admissions start.
- Prospective family wizard.
- Submit validation.
- Checklist creation.
- Fee/waiver state.
- Staff review/decision.
- Accepted-to-enrolled transition.
- Contract/deposit state.
- Classroom readiness.
- Parent portal activation.
- CRM and communications touchpoints.

Exit artifacts:

- `FINAL_ADMISSIONS_ENROLLMENT_GOLDEN_PATH.md`
- `FINAL_PARENT_ADMISSIONS_PROOF.md`

## Sequence 4 - Tuition, billing, payments, ledger, financial aid

Status: NOT DONE

Required closure:

- Tuition setup.
- Fee schedules.
- Obligations.
- Invoice runs.
- Statements.
- Payment handoff.
- Reconciliation.
- Ledger reversals.
- Financial aid application/review/award.
- Award-to-contract/billing sync.
- Parent billing/aid visibility.

Exit artifacts:

- `FINAL_FINANCE_BILLING_AID_ACCEPTANCE.md`
- `FINAL_LEDGER_PAYMENT_PROOF.md`

## Sequence 5 - Teacher, academic, and learning continuity journeys

Status: NOT DONE

Required closure:

- Teacher attendance.
- Gradebook.
- Comments/communications.
- Scheduling.
- Lesson plans.
- Scope and sequence.
- Curriculum import/edit.
- LMS/online classroom.
- Teams/MS365 learning continuity.
- Parent/student academic visibility.

Exit artifacts:

- `FINAL_TEACHER_JOURNEY_PROOF.md`
- `FINAL_LMS_ONLINE_CLASSROOM_PROOF.md`
- `FINAL_CURRICULUM_LESSON_PLAN_PROOF.md`

## Sequence 6 - Parent and student complete journeys

Status: NOT DONE

Required closure:

- Parent dashboard.
- Student profile.
- Attendance view.
- Grades view.
- Billing/payment status.
- Financial aid status.
- Communications.
- Learning status.
- Student dashboard.
- Student schedule/assignments/grades.

Exit artifacts:

- `FINAL_PARENT_JOURNEY_PROOF.md`
- `FINAL_STUDENT_JOURNEY_PROOF.md`

## Sequence 7 - Operational modules

Status: NOT DONE

Required modules:

- HR.
- Facilities.
- Health office.
- Transportation.
- Food service.
- IT support.
- Safety/security.
- Fine arts.
- Library/media.
- Extended care.
- Summer camp.
- Spiritual life/service hours.
- Advancement/alumni.
- Board/governance.

Exit artifacts:

- module-specific rows in `FINAL_95_PLUS_ACCEPTANCE_MATRIX.md`, or replacement final current acceptance matrix.
- module-specific test and dashboard provenance evidence.

## Sequence 8 - Platform operations and implementation success

Status: NOT DONE

Required closure:

- Tenant health.
- Implementation success dashboard.
- Data migration workflow.
- Integrations/automation.
- Compliance/audit dashboard.
- Revenue operations.
- Release reliability.
- Dashboard certification center.

Exit artifacts:

- `FINAL_PLATFORM_OPERATIONS_PROOF.md`
- `FINAL_IMPLEMENTATION_SUCCESS_PROOF.md`

## Sequence 9 - Compliance, customer readiness, and operations

Status: NOT DONE

Required closure:

- FERPA/COPPA posture.
- DPA template.
- Privacy/security summary.
- Data retention.
- Support access.
- Incident response.
- Backup/restore.
- Subprocessor register.
- Sandbox data policy.
- Production support runbook.
- Customer onboarding runbook.

Exit artifacts:

- `FINAL_CUSTOMER_TRUST_PACKET.md`
- `FINAL_PRODUCTION_SUPPORT_RUNBOOK.md`
- `FINAL_BACKUP_RESTORE_PROOF.md`

## Sequence 10 - Release proof and final authority

Status: NOT DONE

Required closure:

- Full backend proof.
- Full frontend proof.
- API/navigation proof.
- Accessibility proof.
- Protected-spine packet.
- Policy gate packet.
- Deploy SHA parity.
- Final 95+ scorecard.
- Final release authority.
- Final signoff.

Exit artifacts:

- `FINAL_RELEASE_SCORECARD.md`
- `FINAL_RELEASE_AUTHORITY.md`
- `FINAL_RELEASE_SIGNOFF.md`

## Final rule

No sequence is complete until its exit artifacts are current, evidence-backed, and committed.
