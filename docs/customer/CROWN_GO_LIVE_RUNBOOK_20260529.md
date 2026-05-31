# CROWN Go-Live Runbook — 2026-05-29

## Status

**RUNBOOK DOCUMENTED — GO-LIVE NOT APPROVED.**

This runbook defines the operational sequence for a controlled CROWN go-live. It is not authorization to launch. Go-live requires signed release authority and current green evidence.

## Go-live prerequisites

All items must be green before go-live:

1. Release authority meta-gate passes.
2. Full-completion truth gate passes.
3. Dashboard completion gate passes.
4. Dashboard data provenance is complete.
5. Core SIS domain model certification is complete.
6. Data migration reconciliation is complete.
7. Financial controls gate passes.
8. Performance/load gate passes.
9. Observability and incident-readiness evidence is attached.
10. Tenant isolation and RBAC/object authorization are green.
11. Backup/restore test is complete.
12. Compliance/customer-readiness packet is approved.
13. DPA/order form is executed where production data is used.
14. Subprocessor register is confirmed.
15. Support-access process is active.
16. Founder/Product Owner final signoff is signed.

## Go-live roles

| Role | Owner | Responsibility |
|---|---|---|
| Founder/Product Owner | TBD | Final authority and business acceptance |
| Technical Release Lead | TBD | Release execution and rollback decision support |
| Security/Compliance Lead | TBD | Security/privacy/compliance go/no-go review |
| Customer Success Lead | TBD | School training, readiness, communications |
| Support Lead | TBD | Support queue, escalation, incident handoff |
| School Executive Sponsor | TBD | Customer acceptance and launch coordination |
| School Data Owner | TBD | Data validation and reconciliation signoff |

## Go-live phases

### Phase 1 — Preflight

- Confirm reviewed commit SHA.
- Confirm environment and tenant configuration.
- Confirm user/role list.
- Confirm DNS/SSO/email/SMS/payment settings where applicable.
- Confirm backup is current.
- Confirm restore point.
- Confirm rollback plan.
- Confirm support/incident contacts.
- Confirm customer communications are approved.

### Phase 2 — Data migration / configuration

- Load tenant configuration.
- Load/import student, family, staff, academic, billing, and communication data as scoped.
- Run validation counts.
- Reconcile records by domain.
- Resolve or explicitly accept discrepancies.
- Lock migrated baseline.

### Phase 3 — User access

- Create/admin users.
- Validate roles.
- Validate parent/student/teacher access if in scope.
- Test disabled/departed user access denial.
- Test cross-tenant denial.
- Test support access approval/logging.

### Phase 4 — Workflow smoke test

Minimum smoke workflows:

- Create/update student record.
- Create/update household/guardian.
- Take attendance.
- Enter grade/assignment.
- Generate student academic output in scope.
- Create invoice/financial record in scope.
- Send communication.
- Render role dashboards.
- Export/report authorized data.
- Confirm unauthorized access is blocked.

### Phase 5 — Launch window

- Announce launch to approved user groups.
- Monitor health dashboards.
- Monitor login failures.
- Monitor API errors.
- Monitor email/SMS/payment/webhook failures.
- Monitor support queue.
- Hold go-live command bridge if applicable.

### Phase 6 — Stabilization

- Review defects/issues daily during stabilization window.
- Triage severity.
- Reconcile critical data domains after first operating cycle.
- Confirm backup jobs continue to run.
- Confirm support SLA performance.
- Confirm user training gaps.
- Produce stabilization report.

## Rollback criteria

Rollback or pause go-live if any occur:

- Cross-tenant data exposure or suspected exposure.
- Critical authentication/RBAC failure.
- Data corruption affecting student, grade, attendance, financial, health, or family records.
- Payment/financial ledger inconsistency that cannot be immediately contained.
- Backup/restore failure during launch window.
- Unresolved security incident.
- Customer executive sponsor requests halt.

## Required evidence bundle

```text
.crown-audit/release-authority/latest/99_STATUS.json
.crown-audit/full-completion-truth/latest/99_STATUS.json
.crown-audit/dashboard-completion/latest/99_STATUS.json
.crown-audit/data-migration/latest/99_STATUS.json
.crown-audit/financial-controls/latest/99_STATUS.json
.crown-audit/performance/latest/99_STATUS.json
.crown-audit/observability/latest/99_STATUS.json
signed_release_authority.pdf_or_md
customer_acceptance.md
rollback_plan.md
stabilization_report.md
```

## Final go-live approval

Go-live is approved only when the final release authority document is signed for the exact branch/commit and all evidence above is attached.

Founder/Product Owner: ____________________________

Date: ____________________________

Technical Release Lead: ____________________________

Date: ____________________________

Customer Executive Sponsor: ____________________________

Date: ____________________________
