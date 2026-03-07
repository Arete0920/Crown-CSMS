# Crown Demo Audit Matrix (Functional = Real)

This is the definition of "thorough". If any item fails, the demo is not certified.

## Pass criteria
- FAIL = 0
- WARN = 0
- UI stability: no 503 spikes
- API stability: no 500/404/400 in normal flows
- Auth semantics:
  - Unauth: 401
  - Wrong tenant: 403
  - Never 400 for normal auth/tenant flows

## Audit layers
1) Availability
- UI base returns 200/3xx consistently (no 503/timeout)
- API /api/health returns 200

2) Role Matrix (seeded users)
- admin
- teacher
- parent
- student
- finance
- registrar
- (add department_director, investor_view as applicable)

3) Endpoint Matrix (must be 200 + schema)
- /api/v1/nav/
- /api/admissions/summary/
- /api/financial-aid/summary/
- all dashboard widget endpoints per role (list grows)

4) UI Matrix (Playwright)
- login per role
- dashboard renders
- nav renders
- no pageerror
- no console error
- no API >= 400 responses
- no debug panels visible

## Output artifacts
- artifacts/demo_audit/audit_report.md
- artifacts/demo_audit/api_probe_results.json
- artifacts/demo_audit/playwright_demo_audit.txt
- artifacts/demo_audit/spike_log.txt
