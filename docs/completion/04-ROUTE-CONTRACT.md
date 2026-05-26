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
| /teacher | canonical role route | TeacherDashboard | No | Teacher Dashboard | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs; frontend/dashboards/tests/proof-smoke.spec.ts:85 | Canonical teacher landing route |
| /teacher/dashboard | canonical dashboard alias | TeacherDashboard | No | Teacher Dashboard | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Explicit teacher dashboard route |
| /teacher/attendance | canonical proof route | TeacherAttendancePage | No | h1/h2/h3 visible | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs; frontend/dashboards/tests/proof-smoke.spec.ts:121 | Single canonical teacher attendance route |
| /teacher/gradebook | alias route | Navigate -> /gradebook | Yes | Gradebook heading at redirect target | teacher/academic roles | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Explicit alias to proven /gradebook route |
| /teacher/classes | canonical teacher workflow route | ClassroomsDashboard | No | UNPROVEN | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Truthful teacher classes entry |
| /teacher/lesson-plans | canonical teacher workflow route | ClassroomsDashboard | No | UNPROVEN | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Planning workspace currently shares classrooms surface |
| /teacher/curriculum | canonical teacher workflow route | CurriculumPDDashboard | No | UNPROVEN | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Canonical curriculum route for Slice 1 |
| /teacher/communications | alias route | Navigate -> /communications | Yes | Communications heading at redirect target UNPROVEN | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Explicit alias to existing communications route |
| /teacher/student-support | pending workflow route | TeacherWorkflowPending | No | Student Support - Planned workflow | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Pending implementation; not a completed workflow |
| /teacher/discipline | pending workflow route | TeacherWorkflowPending | No | Discipline - Planned workflow | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Pending implementation; not a completed workflow |
| /teacher/remote-day | pending workflow route | TeacherWorkflowPending | No | Remote Day - Planned workflow | teacher | frontend/dashboards/src/routes/router.jsx; frontend/dashboards/tests/teacher-route-truth-static.mjs | Pending implementation; not a completed workflow |
| /parent | canonical role route | ParentDashboard | No | Parent Dashboard | parent | frontend/dashboards/src/routes/router.jsx:198; frontend/dashboards/tests/proof-smoke.spec.ts:134; frontend/dashboards/tests/ui/parent-dashboard-v1.spec.ts:69 | Covered by proof smoke and parent dashboard suite |
| /parent/attendance | alias route | ParentAttendancePage (duplicate literal alias also present) | No | UNPROVEN | parent | frontend/dashboards/src/routes/router.jsx:112; frontend/dashboards/src/routes/router.jsx:177 | Alias contract present; no direct heading assertion for this route |
| /student | canonical role route | StudentDashboard | No | Student Dashboard | student | frontend/dashboards/src/routes/router.jsx:202; frontend/dashboards/tests/ui/student-dashboard-v2.spec.ts:74 | Student dashboard suite asserts heading and KPI content |
| /gradebook | canonical proof route | GradebookRO | No | h1/h2 visible | academic roles | frontend/dashboards/src/routes/router.jsx:210; frontend/dashboards/tests/proof-smoke.spec.ts:145 | Route renders locally; CI gradebook-proof still failing |
| /login | canonical auth route | LoginPage | No | h1/h2/form visible | anonymous/auth | frontend/dashboards/src/routes/router.jsx:99; frontend/dashboards/tests/proof-smoke.spec.ts:156 | Login surface check passes locally |

---

## Route Rules

### Canonical routes
- /, /login, /admin, /teacher, /parent, /student, /gradebook
- /teacher/dashboard and /teacher/attendance are canonical proof-bearing teacher routes in this slice
- Canonical route behavior must stay consistent with proof-smoke and dashboard proof suites

### Alias routes
- /parent/attendance is an alias path preserved in router
- /teacher/gradebook and /teacher/communications exist as contract-preserving aliases in router (redirects)
- /teacher/scope-sequence and /teacher/scheduling remain legacy aliases redirecting to truthful teacher workflow routes
- /administration remains UNPROVEN in this snapshot

### Proof/test routes
- /admin, /teacher/attendance, /parent, /gradebook, /login
- /student (student-dashboard-v2)
- Executive/parent/student dashboard tests are part of current proof surface

### Redirect rules
- / may redirect based on role context
- Redirect to /admin, /teacher, and /parent from / is explicitly asserted
- Teacher and parent alias routes may redirect to canonical dashboard routes
- Pending teacher workflow routes must render explicit pending state and must not imply completed functionality
- Redirect outcomes must remain aligned to proof-smoke assertions

### Forbidden route drift
- No casual renaming of proof/test routes.
- No redirect changes without proof-contract review.
- No route deletion without updating this file and the proof contract.

---

## Resolved Issues

- Duplicate /teacher/attendance route definition removed in Slice 1.
- /teacher now truthfully resolves to TeacherDashboard instead of attendance-oriented behavior.

## Notes

- Route truth is evidence-scoped to current router capture and local proof runs.
- Any route not directly evidenced is marked UNPROVEN.
- Pending teacher workflows are intentionally marked pending and not claimed complete.
