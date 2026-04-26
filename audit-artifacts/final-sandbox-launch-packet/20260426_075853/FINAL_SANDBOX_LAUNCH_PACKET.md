# CROWN Final Sandbox Launch Packet

Date/time: 2026-04-26 07:58:53 -04:00

## Launch Authority

- Branch: hotfix/sandbox-auth-proof-final-wip
- Main HEAD: 941185b5358885ac61f70e250e98fe164e85899d
- PR #775: MERGED
- PR checks: 38 successful / 0 failing / 0 pending / 1 skipped
- Working tree clean: False

## Product Brand

- Product: CROWN
- Tagline: Christian School Management Solution

## Final Gate Matrix

| Gate | Result |
|---|---|
| Visual proof | PASS |
| School Admin login | PASS |
| Teacher login | PASS |
| Parent login | PASS |
| Student/Learner login | PASS |
| Logout flow | PASS |
| Correct school context persistence | PASS |
| Backend token endpoint | PASS |
| Sandbox invite technical gate | PASS |

## Verified Heritage Sandbox Personas

| Role | Username | Password |
|---|---|---|
| School Admin | admin@heritage.example.org | demo-password |
| Teacher | teacher.lower@heritage.example.org | demo-password |
| Parent | parent.reed@heritage.example.org | demo-password |
| Student/Learner | student.avery.reed11@heritage.example.org | demo-password |

## 20-School Sandbox Cohort

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

## Tester Script

1. Open the sandbox login link.
2. Select assigned sandbox school.
3. Select role.
4. Confirm credentials prefill or enter provided credentials.
5. Sign in.
6. Confirm correct school context.
7. Review dashboard.
8. Open Admissions.
9. Open Attendance.
10. Open Gradebook.
11. Open Finance.
12. Open Communications.
13. Log out.
14. Submit feedback form.

## Hard Rules

- Use demo data only.
- Do not enter real student, family, staff, financial, health, or disciplinary records.
- Report login failure immediately.
- Report incorrect school context immediately.
- Report blank page, fallback, or raw API error immediately.

## Launch Decision

CROWN is cleared for controlled sandbox invite execution, subject to final operator smoke and staged invite rollout.
