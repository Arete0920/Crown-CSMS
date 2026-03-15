# Crown2026 — Route Contract

## Purpose

This file defines the allowed route behavior for Crown2026.

For each route, specify:
- canonical vs alias vs proof/test
- owning page/component
- redirect behavior
- required visible heading
- required role
- evidence

---

## Route Table

| Route | Type | Owning Page / Component | Redirect Allowed | Required Visible Heading | Required Role | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| / | canonical entry route | RoleHomeRedirect | Yes (role redirect) | UNPROVEN at this route | authenticated role context | frontend/dashboards/src/routes/router.jsx:95; frontend/dashboards/tests/proof-smoke.spec.ts:75; frontend/dashboards/tests/proof-smoke.spec.ts:85; frontend/dashboards/tests/proof-smoke.spec.ts:95 | Redirect destination proven for admin/teacher/parent |
| /admin | canonical proof route | AdminDashboard | No | h1/h2 visible (Administration also asserted in executive suite) | admin | frontend/dashboards/tests/proof-smoke.spec.ts:106; frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts:71 | Covered by proof smoke and executive dashboard suite |
| /administration | alias/legacy (UNPROVEN) | UNPROVEN | UNPROVEN | UNPROVEN | UNPROVEN | UNPROVEN | Route not confirmed in current snapshot |
| /teacher | canonical role route | AttendanceDashboard | No | UNPROVEN (no direct heading assertion on /teacher) | teacher | frontend/dashboards/src/routes/router.jsx:171; frontend/dashboards/tests/proof-smoke.spec.ts:85 | Direct route exists; proof only asserts redirect to URL |
| /teacher/attendance | canonical proof route | TeacherAttendancePage (duplicate literal alias also present) | No | h1/h2/h3 visible | teacher | frontend/dashboards/src/routes/router.jsx:108; frontend/dashboards/src/routes/router.jsx:154; frontend/dashboards/tests/proof-smoke.spec.ts:121 | Duplicate route definition exists in router snapshot |
| /parent | canonical role route | ParentDashboard | No | Parent Dashboard | parent | frontend/dashboards/src/routes/router.jsx:198; frontend/dashboards/tests/proof-smoke.spec.ts:134; frontend/dashboards/tests/ui/parent-dashboard-v1.spec.ts:69 | Covered by proof smoke and parent dashboard suite |
| /parent/attendance | alias route | ParentAttendancePage (duplicate literal alias also present) | No | UNPROVEN | parent | frontend/dashboards/src/routes/router.jsx:112; frontend/dashboards/src/routes/router.jsx:177 | Alias contract present; no direct heading assertion for this route |
| /student | canonical role route | StudentDashboard | No | Student Dashboard | student | frontend/dashboards/src/routes/router.jsx:202; frontend/dashboards/tests/ui/student-dashboard-v2.spec.ts:74 | Student dashboard suite asserts heading and KPI content |
| /gradebook | canonical proof route | GradebookRO | No | h1/h2 visible | academic roles | frontend/dashboards/src/routes/router.jsx:210; frontend/dashboards/tests/proof-smoke.spec.ts:145 | Route renders locally; CI gradebook-proof still failing |
| /login | canonical auth route | LoginPage | No | h1/h2/form visible | anonymous/auth | frontend/dashboards/src/routes/router.jsx:99; frontend/dashboards/tests/proof-smoke.spec.ts:156 | Login surface check passes locally |

---

## Route Rules

### Canonical routes
- /, /login, /admin, /teacher, /parent, /student, /gradebook
- /teacher/attendance is treated as canonical for proof coverage
- Canonical route behavior must stay consistent with proof-smoke and dashboard proof suites

### Alias routes
- /parent/attendance is an alias path preserved in router
- /teacher/gradebook, /teacher/communications, /teacher/scheduling exist as contract-preserving aliases in router (redirects)
- /teacher/attendance and /parent/attendance both appear twice in router snapshot (PATHS.* and literal aliases)
- /administration remains UNPROVEN in this snapshot

### Proof/test routes
- /admin, /teacher/attendance, /parent, /gradebook, /login
- /student (student-dashboard-v2)
- Executive/parent/student dashboard tests are part of current proof surface

### Redirect rules
- / may redirect based on role context
- Redirect to /admin, /teacher, and /parent from / is explicitly asserted
- Teacher and parent alias routes may redirect to canonical dashboard routes
- Redirect outcomes must remain aligned to proof-smoke assertions

### Forbidden route drift
- No casual renaming of proof/test routes.
- No redirect changes without proof-contract review.
- No route deletion without updating this file and the proof contract.

---

## Notes

- Route truth is evidence-scoped to current router capture and local proof runs.
- Any route not directly evidenced is marked UNPROVEN.
- CI still blocks merge due gradebook-proof and CodeQL failures.
