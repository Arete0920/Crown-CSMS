# Dev Team Runtime Proof Checklist - 2026-05-01

## Goal
Close all manual-required runtime proof rows and attach evidence links for each row.

## Rules of execution
- Use production-aligned roles and tenant context.
- Record exact user role, school context, endpoint or UI route, and result.
- Attach evidence per row: screenshot, HAR/API response, and timestamp.
- Any FAIL in TI or RBAC rows is P0 and reopens certification.

## Required rows
1. TI-001 - School A admin cannot access School B student by URL/API id. Expected: 403/404/safe redirect. Owner: Dev 1 / Dev 2 / Dev 5.
2. TI-002 - School A parent cannot access School B household record. Expected: 403/404/safe redirect. Owner: Dev 1 / Dev 2 / Dev 5.
3. TI-003 - School A finance user cannot access School B billing data. Expected: 403/404/safe redirect. Owner: Dev 1 / Dev 3 / Dev 5.
4. TI-004 - School A teacher cannot access School B roster/attendance/grades. Expected: 403/404/safe redirect. Owner: Dev 1 / Dev 2 / Dev 5.
5. TI-005 - School A dashboard cannot aggregate School B data. Expected: only active school data. Owner: Dev 1 / Dev 4 / Dev 5.
6. TI-006 - Unauthorized school switcher context change is rejected. Expected: denied. Owner: Dev 1 / Dev 5.
7. TI-007 - School A user cannot download School B document/file. Expected: 403/404/safe redirect. Owner: Dev 1 / Dev 5.
8. RBAC-001 - Parent cannot access admin dashboard. Expected: denied. Owner: Dev 1 / Dev 5.
9. RBAC-002 - Teacher cannot access finance billing admin. Expected: denied. Owner: Dev 1 / Dev 5.
10. RBAC-003 - Student cannot access staff/student admin records. Expected: denied. Owner: Dev 1 / Dev 5.
11. RBAC-004 - Finance cannot edit grades/transcripts. Expected: denied. Owner: Dev 1 / Dev 5.
12. RBAC-005 - Admissions cannot edit transcript records. Expected: denied. Owner: Dev 1 / Dev 5.
13. RBAC-006 - Direct API call outside role is denied even if frontend route is guessed. Expected: denied. Owner: Dev 1 / Dev 5.
14. WF-001 - Inquiry to applicant to admitted to enrolled. Expected: canonical SIS student/enrollment created once. Owner: Dev 2 / Dev 3 / Dev 5.
15. WF-002 - Re-enrollment checklist to next-year enrollment. Expected: returning student status updates correctly. Owner: Dev 2 / Dev 3 / Dev 5.
16. WF-003 - Billing charge to payment to balance. Expected: admin and parent views reconcile. Owner: Dev 3 / Dev 5.
17. WF-004 - Teacher roster to attendance posting. Expected: attendance persists and admin sees result. Owner: Dev 2 / Dev 4 / Dev 5.
18. WF-005 - Parent portal household/student/billing/messages. Expected: parent sees only authorized household data. Owner: Dev 4 / Dev 5.
19. WF-006 - Admin dashboard KPI drill-downs. Expected: dashboard totals match source data. Owner: Dev 4 / Dev 5.
20. CHAOS-001 - Double-click submit does not duplicate records. Expected: no duplicate/corruption. Owner: Dev 4 / Dev 5.
21. CHAOS-002 - Refresh/back mid-wizard recovers safely. Expected: no stuck state/corruption. Owner: Dev 4 / Dev 5.
22. CHAOS-003 - Two tabs editing same record handles stale update safely. Expected: no silent overwrite. Owner: Dev 1 / Dev 5.
23. SEC-001 - IDOR object id swapping fails. Expected: denied. Owner: Dev 1 / Dev 5.
24. SEC-002 - XSS payload in names/messages/notes is neutralized. Expected: no script execution. Owner: Dev 1 / Dev 4 / Dev 5.
25. DATA-001 - Migration check and backup/restore procedure verified. Expected: no data loss. Owner: Dev 2 / Dev 5.
26. DATA-002 - Withdrawn/archived student keeps history but blocks active workflows. Expected: correct lifecycle behavior. Owner: Dev 2 / Dev 5.

## Evidence capture table
| ProofId | Result (PASS/FAIL) | Evidence path/link | Executor | Timestamp |
|---|---|---|---|---|
| TI-001 |  |  |  |  |
| TI-002 |  |  |  |  |
| TI-003 |  |  |  |  |
| TI-004 |  |  |  |  |
| TI-005 |  |  |  |  |
| TI-006 |  |  |  |  |
| TI-007 |  |  |  |  |
| RBAC-001 |  |  |  |  |
| RBAC-002 |  |  |  |  |
| RBAC-003 |  |  |  |  |
| RBAC-004 |  |  |  |  |
| RBAC-005 |  |  |  |  |
| RBAC-006 |  |  |  |  |
| WF-001 |  |  |  |  |
| WF-002 |  |  |  |  |
| WF-003 |  |  |  |  |
| WF-004 |  |  |  |  |
| WF-005 |  |  |  |  |
| WF-006 |  |  |  |  |
| CHAOS-001 |  |  |  |  |
| CHAOS-002 |  |  |  |  |
| CHAOS-003 |  |  |  |  |
| SEC-001 |  |  |  |  |
| SEC-002 |  |  |  |  |
| DATA-001 |  |  |  |  |
| DATA-002 |  |  |  |  |

## Escalation rules
- Any TI-* FAIL: P0 tenant bypass.
- Any RBAC-* FAIL: P0 authorization bypass.
- Any SEC-* FAIL: P0 security vulnerability.
- Any DATA-* FAIL: P0 data integrity risk.
