# Crown2026 4-School Production Onboarding Packet

Date/time: 2026-04-25 12:38:28 -04:00
Strike artifact: audit-artifacts\48h-sandbox-prod-readiness\20260425_114916

## Launch Objective

Prepare 4 schools to begin full-service onboarding while keeping sandbox and production boundaries separate.

## Current Technical Gate

- Strike FAIL rows: 0
- Release packet checker: PASS
- Backend checks: PASS
- Migration drift: PASS
- Workflow YAML parse: PASS
- Hygiene burndown: completed through classified categories

## Full-Service School Onboarding Requirements

Each full-service school must have:

| Requirement | Status |
|---|---|
| Signed onboarding approval | Required |
| Production tenant/school record | Required |
| Admin user | Required |
| Staff/teacher import path | Required |
| Student/family import path | Required |
| Billing/finance configuration | Required if finance module enabled |
| M365/Teams/Entra scope confirmed | Required if enabled |
| Data migration plan | Required |
| Go-live support contact | Required |
| Rollback/escalation plan | Required |

## Four-School Production Readiness Checklist

For each of the 4 schools:

1. Confirm legal school name.
2. Confirm production admin contact.
3. Confirm data import owner.
4. Confirm launch modules:
   - Admissions
   - Enrollment
   - Attendance
   - Gradebook
   - Finance/Billing
   - Communications
   - M365/Teams/Entra integrations
5. Confirm production URL.
6. Confirm first-login process.
7. Confirm support window.
8. Confirm acceptance signoff.

## Production Acceptance Standard

Production onboarding may proceed only when:

- School tenant isolation is confirmed.
- Admin login works.
- Core dashboard loads.
- No sandbox data appears in production.
- Required modules are enabled by school.
- Support/escalation path is live.
- Backup/rollback approach is documented.
