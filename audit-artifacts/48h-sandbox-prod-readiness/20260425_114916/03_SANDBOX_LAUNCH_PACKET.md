# Crown2026 20-School Sandbox Launch Packet

Date/time: 2026-04-25 12:38:16 -04:00
Strike artifact: audit-artifacts\48h-sandbox-prod-readiness\20260425_114916

## Launch Objective

Prepare 20 sandbox schools for guided sandbox use without requiring real school data.

## Current Technical Gate

- Strike FAIL rows: 0
- Release packet checker: PASS
- Python syntax: PASS
- Django check: PASS
- Migration drift: PASS
- Workflow YAML parse: PASS
- Frontend spec inventory: PASS

## Sandbox School Requirements

Each sandbox school must have:

| Requirement | Status |
|---|---|
| Sandbox-only identity/data boundary | Confirm before send |
| Pre-filled login where supported | Confirm before send |
| Admin account | Required |
| Teacher account | Required |
| Parent account | Required |
| Student/sample learner account | Required if student UX is in sandbox |
| Sample admissions records | Required |
| Sample attendance records | Required |
| Sample gradebook records | Required if gradebook shown |
| Sample billing/finance records | Required if finance shown |
| Guided script | Required |
| Feedback form | Required |
| Support contact path | Required |

## Recommended 20-School Sandbox Cohort

Use sandbox/dummy data only.

1. Heritage Christian Academy
2. Harvest Christian School
3. Faith Christian Academy
4. Calvary Christian School
5. St. Anne Christian Academy
6. Grace Covenant School
7. Providence Christian Academy
8. Trinity Classical School
9. Redeemer Christian School
10. Cornerstone Christian Academy
11. New Hope Christian School
12. Legacy Christian Academy
13. Emmanuel Christian School
14. King's Way Christian Academy
15. Bethel Christian School
16. Veritas Christian Academy
17. Crossroads Christian School
18. Shepherd's Gate Academy
19. Lighthouse Christian School
20. Covenant Preparatory School

## Sandbox Tester Script

1. Open sandbox login page.
2. Select assigned sandbox school.
3. Confirm credentials are visible/prefilled or provided.
4. Log in as school admin.
5. Review dashboard landing page.
6. Open admissions.
7. Open students/enrollment.
8. Open attendance.
9. Open gradebook if enabled.
10. Open finance/billing if enabled.
11. Open communications/messages if enabled.
12. Log out.
13. Repeat with teacher or parent role.
14. Complete feedback form.

## Minimum Acceptance Standard

Sandbox is acceptable only if:

- Login works without confusion.
- Assigned school context is clear.
- No real data is required.
- Core dashboards load.
- No role sees another school's data.
- Feedback path is clear.
- Support escalation path is clear.

## Immediate Operator Tasks

- Confirm final sandbox URL.
- Confirm 20 sandbox school names/accounts.
- Confirm prefilled login behavior.
- Confirm tester instructions.
- Confirm feedback form.
- Confirm support contact.
