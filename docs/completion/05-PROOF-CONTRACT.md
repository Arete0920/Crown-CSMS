# Crown2026 — Proof Contract

## Purpose

This file locks the route, URL, and visible-content expectations for proof-checked pages.

If a test is asserting a route or heading, it must be documented here.

---

## Proof Surface Table

| Route | Expected Final URL | Expected Visible Heading | Expected Visible Control / Form | Role Context | Test File | Notes |
|---|---|---|---|---|---|---|
| / | /admin or /teacher or /parent (role redirected) | UNPROVEN at this route | no uncaught page errors | role-dependent | frontend/dashboards/tests/proof-smoke.spec.ts:75; frontend/dashboards/tests/proof-smoke.spec.ts:85; frontend/dashboards/tests/proof-smoke.spec.ts:95 | Local pass in _local_playwright_after_fix.log |
| /admin | /admin | h1/h2 visible (Administration asserted in executive suite) | at least one link visible | admin | frontend/dashboards/tests/proof-smoke.spec.ts:106; frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts:71 | Local pass; CI dashboard-ui checks pass |
| /teacher | /teacher (via role-home redirect) | UNPROVEN | no uncaught page errors on redirect flow | teacher | frontend/dashboards/tests/proof-smoke.spec.ts:85 | Redirect assertion only |
| /teacher/attendance | /teacher/attendance | h1/h2/h3 visible | heading/form surface visible | teacher | frontend/dashboards/tests/proof-smoke.spec.ts:121 | Local pass |
| /parent | /parent | Parent Dashboard | household KPI and children card | parent | frontend/dashboards/tests/proof-smoke.spec.ts | Local pass |
| /student | /student | Student Dashboard | KPI cards and upcoming assignments | student | frontend/dashboards/tests/ui/student-dashboard-v2.spec.ts:74 | Local pass |
| /gradebook | /gradebook | h1/h2 visible | heading surface visible | teacher/admin academic context | frontend/dashboards/tests/proof-smoke.spec.ts:145 | Local smoke pass; gradebook-proof CI check failing |
| /login | /login | h1/h2/form visible | login surface visible | anonymous | frontend/dashboards/tests/proof-smoke.spec.ts:156 | Local pass |

---

## Dashboard Gate Expectations

### Administration surface
- Route: /admin
- Required heading: h1/h2 visible (Administration asserted in executive suite)
- Test file: frontend/dashboards/tests/proof-smoke.spec.ts:106 and frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts:71
- Required controls: quick-action links (as asserted by proof smoke)
- Notes: Currently stable in local proof run.

### Parent surface
- Route: /parent
- Required heading: Parent Dashboard
- Test file: frontend/dashboards/tests/proof-smoke.spec.ts:134 and frontend/dashboards/tests/ui/parent-dashboard-v1.spec.ts:69
- Required controls: household KPI row, Children card
- Notes: Local run passed.

### Student surface
- Route: /student
- Required heading: Student Dashboard
- Test file: frontend/dashboards/tests/ui/student-dashboard-v2.spec.ts:74
- Required controls: KPI cards, Upcoming Assignments section
- Notes: Local run passed.

---

## Token / Auth Proof Expectations

- Token source: CI demo token endpoint at http://127.0.0.1:8000/api/dev/token/ and browser session/local storage seeding in proof-smoke tests
- Request format: POST /api/dev/token/ with header X-Demo-Key and body {}
- Response format: JSON containing access/access_token/token (top-level or under data)
- Required stdout contract: token acquisition succeeds before gradebook readiness probe and proof tests execute
- Required stderr behavior: explicit error output and non-zero exit on missing/invalid token response
- Empty response handling: explicit hard fail with message "empty response from token endpoint"
- Test / workflow location: .github/workflows/proof-gradebook.yml and frontend/dashboards/tests/proof-smoke.spec.ts
- Notes: Workflow evidence lines for token contract are .github/workflows/proof-gradebook.yml:151, .github/workflows/proof-gradebook.yml:153, .github/workflows/proof-gradebook.yml:171, .github/workflows/proof-gradebook.yml:172, .github/workflows/proof-gradebook.yml:196, and .github/workflows/proof-gradebook.yml:199. Merge remains blocked by failing gradebook-proof result.

---

## Change control

Any change to:
- proof routes
- expected visible headings
- token request behavior
- proof-visible controls/forms

must update this file and the corresponding tests together.

---

## Notes

- Proof surface is locally validated but not fully CI-clean due gradebook-proof failure.
- CodeQL failure is outside UI proof contract but still blocks merge readiness.
- Token request/response and failure behavior are documented from current proof workflow.
