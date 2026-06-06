# PR #918 Connector Status — 2026-06-06

Scope: Security P0 remediation branch `copilot/fix-security-and-quality-warnings`.

## Connector-verified fixes

- `backend/inspect_events.py` no longer logs raw event payload values.
- `frontend/dashboards/src/pages/InvoiceRunWizard.jsx` keeps wizard context in memory only.
- `frontend/dashboards/src/pages/GradebookSetupWizard.jsx` keeps wizard context in memory only.
- `frontend/dashboards/src/pages/EnrollmentConversionWizard.jsx` keeps wizard context in memory only.
- `frontend/dashboards/src/pages/AttendanceRulesWizard.jsx` keeps wizard context in memory only.
- `.github/workflows/crown-release-authority-gates.yml` declares explicit read-only workflow permissions.

## Connector-verified green checks at latest inspection

- CodeQL Security Analysis: success.
- Secret scan: success.
- Frontend npm audit jobs: success.
- Dependency Review: success.
- Workflow Lint: success.
- Workflow Policy Gate: success.
- CROWN Release Authority Gates: success.
- dashboards-build-gate: success.
- backend-gate: success.
- Frontend Quality Gates: success.
- Tenant Isolation Gate: success.
- Phase3 Runtime Proof Ceremony: success.
- Crown Full Surface Verification: success.

## Connector-verified remaining blockers

- Sandbox Ready Evidence Gate: failure (issue #926)

- Frontend npm audit jobs are passing in both dependency workflows.

## Files inspected for backend dependency lane

- `backend/requirements.txt`
- `requirements.txt`
- `backend/requirements-loadtest.txt`
- `.github/workflows/dependency-scan.yml`
- `.github/workflows/dependency-audit.yml`

## Connector boundary

The GitHub connector can identify the failing jobs and inspect workflow definitions, but cannot run local `pip-audit`, regenerate dependency locks, or read the downloaded ZIP artifact contents in this session. Exact package/advisory remediation must be confirmed in VS Code with local `pip-audit` output before this PR is marked ready.

## Required next local command lane

Run `pip-audit` against:

1. `backend/requirements.txt`
2. `backend/requirements-loadtest.txt`
3. `requirements.txt`

Then patch the vulnerable Python dependency or add a documented risk acceptance only if no fixed version exists and the risk is non-exploitable in Crown's deployment context.

Decision remains: PR #918 must stay draft/open until backend pip-audit is green and dependency gates rerun successfully.
