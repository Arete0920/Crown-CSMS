# Live Release Authority Signoff - 2026-05-26

## Decision

- CONDITIONAL NO-GO for final release approval.

## Decision Basis

- Core protected-spine runtime evidence is green and authoritative.
- Public endpoint and CSRF governance hardening is implemented and locally verified.
- Frontend truth disclosure now covers the admissions live slice, board executive live/demo surface, finance live/unavailable surface, and template-backed dashboards through shared fallback labeling.
- Final hosted CI proof after Node 22 uplift and policy-gate insertion is still missing. The branch merge conflict on PR `#854` was resolved, the affected workflows were disabled and re-enabled to refresh registration, and a second retrigger commit was pushed, but GitHub Actions still did not attach any checks to the now-mergeable PR during this session.

## Current Approval Posture

| Area | Status | Evidence |
| --- | --- | --- |
| Protected-spine runtime authority | PASS | `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260526_052724.md` |
| Auth/RBAC guarded baseline | PASS | `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_SUBBATCH_SUMMARY_auth_security_baseline_20260526_055509.md` |
| Admissions protected slice | PASS | `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_SUBBATCH_SUMMARY_admissions_applications_20260526_052724.md` |
| Public endpoint / CSRF governance | PASS (local) | `tools/verify_public_surface_policy.py`, `docs/security/public_endpoint_policy_matrix.json`, `docs/security/csrf_exception_policy_matrix.json` |
| Policy gate regression coverage | PASS | `tests/test_public_surface_policy_gate.py` (`4 passed`) |
| Frontend truth disclosure slice | PASS | `frontend/dashboards/src/pages/AdmissionsDashboard.test.jsx`, `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx`, `node scripts/release/verify-frontend-rc.mjs` |
| Hosted CI sweep after latest gate changes | NOT COMPLETE | PR `#854` is now `CLEAN` / `MERGEABLE`, workflows were re-registered, but `gh pr checks 854` still reports no checks and Release Verify workflow dispatch still returns GitHub HTTP 500 |

## Evidence Summary

1. Protected-spine packet `20260526_052724` is green with `blocked=false`, `proof_runner_failures=0`, and `product_test_failures=0`.
2. Auth/security authoritative rerun at `20260526_055509` passed with `269 passed in 178.84s`.
3. Admissions subbatch authoritative summary at `20260526_052724` passed with `34 passed in 33.10s`.
4. Public-surface governance automation is implemented with hard-fail behavior for unmanaged or stale `AllowAny` and `csrf_exempt` usage.
5. Local policy gate verification passed with `AllowAny entries tracked: 14` and `csrf_exempt entries tracked: 19`.
6. Policy-gate regression tests passed: `4 passed in 0.22s`.
7. Shared dashboard template now injects fallback data-truth disclosure for template-backed dashboards without bespoke live wiring.
8. Focused frontend unit validation passed with `32/32` test files and `125/125` tests, including template disclosure, admissions truth-contract coverage, and finance disclosure coverage.
9. PR `#854` branch conflict was resolved by merging `main` into `feature/teacher-route-truth-slice1` and reconciling `.github/workflows/deploy-prod-dispatch.yml`; GitHub now reports the PR as `CLEAN` and `MERGEABLE`.
10. Workflow registration was refreshed for `contract-gate` and `Release Verify`, followed by retrigger commit `fdc2913faa9ee4ba522119f913f5615a2f93968c`; GitHub still created zero check suites for the head commit.

## Remaining Blockers To Final GO

1. Restore normal GitHub Actions scheduling for PR `#854` so hosted checks actually attach to branch `feature/teacher-route-truth-slice1`.
2. Run hosted `contract-gate` after the public-surface gate insertion and capture pass/fail artifact output.
3. Run hosted `release-verify` after the Node 22 uplift and policy-gate insertion and capture pass/fail artifact output.

## What Is Approved Now

1. Runtime protected-spine authority can be treated as current release truth source.
2. Public endpoint and CSRF exception inventory is now under explicit policy governance.
3. Unmanaged additions to those surfaces are now blocked locally and in workflow configuration.
4. Template-backed dashboards now disclose fallback/template data truth by default.
5. Current known bespoke live-data dashboards disclose their runtime truth state explicitly.

## What Is Not Approved Yet

1. Final release-ready claim.
2. Hosted CI completeness claim for the latest workflow state.
3. Any assertion that PR `#854` has passed required checks.

## Release Authority Statement

This branch is materially stronger than the prior state and the primary runtime blocker lane is closed. Final release approval is intentionally withheld until hosted CI executes on the latest workflow graph for the current branch state. The PR mergeability blocker is fixed; the remaining blocker is GitHub Actions failing to attach checks or honor workflow dispatch for PR `#854`.
