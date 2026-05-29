# Current Release Scorecard - 2026-05-29

Canonical linkage:
- Repository-level authority: `docs/CURRENT_RELEASE_STATUS.md`
- This file is the single current scorecard referenced by that authority.

## Decision

- Current decision: CONDITIONAL GO
- Confidence basis: runtime-verified backend slices, runtime-verified frontend build/tests, runtime-verified tenant/RBAC checks.

## Scorecard

| Area | Status | Score | Evidence |
| --- | --- | --- | --- |
| Backend integrity | PASS | 92 | `python backend/manage.py check`; `pytest backend/applications/tests/test_admissions_endpoints.py -q -s` (`24 passed`); `pytest backend/aftercare -q` (`17 passed`) |
| Parent360 hotspot correctness | PASS | 83 | `backend/parent360/api/views.py` household + assignment + enrollment-scope hardening with regression passes above |
| Frontend operational proof | PASS | 90 | `npm run build` (PASS); `npm run test -- --run` (PASS: `37 passed` files, `341 passed` tests, `1 skipped`) |
| Route guard and permission posture | PASS | 89 | Guarded route wiring in `frontend/dashboards/src/routes/router.jsx`; role groups in `frontend/dashboards/src/routes/routeGroups.js`; nav permission scoping in `frontend/dashboards/src/components/navigation/navItems.js` |
| Tenant/RBAC proof | PASS | 90 | `pytest backend/tests/test_tenant_isolation.py -q` (`7 passed`) |
| Deploy SHA parity | PARTIAL | 65 | local HEAD `1febb85a160eb2430c300335c366953ac5f17174`; `origin/main` `d793766b6640d88a4bfdb87c999f429e06cd87ec`; `git rev-list --left-right --count origin/main...HEAD` -> `50 19`; deploy target parity for latest head not yet evidenced; see `docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md` |
| Release authority convergence | PARTIAL | 72 | Canonical authority now consolidated in `docs/CURRENT_RELEASE_STATUS.md`; legacy docs still present and require continued hygiene labeling |
| Operational readiness | CONDITIONAL | 83 | Composite of above; unresolved parity + authority convergence prevent unrestricted GO |

## Required to Move from CONDITIONAL GO to Unrestricted GO

1. Add deploy-target parity proof for the approved release SHA (or current head) across active environments.
2. Complete supersession hygiene across legacy GO/PARTIAL/FAIL artifacts and keep only canonical authority + scorecard as controlling sources.
3. Keep backend/frontend/tenant proofs fresh when material code changes occur.
