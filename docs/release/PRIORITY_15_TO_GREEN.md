# CROWN2026 â€” 15 HIGHEST PRIORITIES TO GREEN

1. Auth / RBAC / Tenant proof
   Green when tenant isolation and negative-access tests pass in CI.
2. Health and integrity endpoint proof
   Green when `/api/health/` and `/api/integrity/` return 200 in local/staging verification.
3. Django import, check, migration, deploy check
   Green when `manage.py check`, `showmigrations`, and `check --deploy` are clean.
4. OpenAPI / Swagger publication
   Green when `/api/schema/`, `/api/docs/`, and `docs/openapi/crown-openapi.yaml` exist.
5. Dependency audit blocking
   Green when backend and frontend dependency audit workflows fail on high/critical issues.
6. Release verify workflow
   Green when one workflow proves backend checks, tenant tests, frontend smoke, and schema export.
7. Golden path E2E
   Green when admissions â†’ enrollment â†’ billing â†’ attendance runs through Playwright.
8. Tenant + URL smoke tests
   Green when URL imports resolve and cross-tenant negative tests pass.
9. Load evidence
   Green when Locust profile exists and a written threshold/result report is produced.
10. Export UI surface
    Green when shared export controls exist and point to stable report endpoints.
11. Transcript/report-card/export closeout
    Green when report endpoints exist and are exercised in smoke tests.
12. CompuWerx / payment evidence
    Green when live or sandbox payment path proof is captured in release artifacts.
13. Branch protection checklist
    Green when required checks are named and enforced on main.
14. Evidence bundle capture
    Green when logs, screenshots, schema, and workflow outputs are written to `audit-artifacts/release-verify`.
15. Final release command pack
    Green when one command sequence can be run from repo root and outputs a proof bundle.