# Known Gaps and Deferred Items

Generated: 2026-04-02

This document is intentionally candid. It records unresolved items and what is required to close them.

## 1. Still Not Complete

| Item | Current State | Why Incomplete | Next Action | Owner |
|---|---|---|---|---|
| Green-on-main evidence snapshot | Missing | No committed recent green-run export for main | Export latest successful run matrix and attach in release docs | DevOps |
| Golden path pytest output | Missing | Artifact file not committed | Run tests and commit `artifacts/golden-path-pytest-output.txt` | QA |
| Tenant isolation pytest output | Missing | Artifact file not committed | Run tests and commit `artifacts/tenant-isolation-pytest-output.txt` | QA |
| Final load evidence | Missing | No load html/csv artifacts committed | Generate and commit expected files under `artifacts/load/` | QA |
| Branch protection screenshot | Missing | Manual UI capture not done | Capture settings screenshot and commit to release evidence folder | Repo admin |
| PR backlog and conflict PR cleanup | In progress | 16 open PRs with conflict states still present | Execute `docs/release/PR_ISSUES_CONCERNS_ACTION_PLAN.md` and update counts/status | Eng lead

## 2. Manual-Only Items

| Item | Why Manual | Required Output |
|---|---|---|
| GitHub branch protection UI proof | Requires admin access to repository settings | Screenshot + optional JSON/API export |
| Security-gate blocking screenshots | Requires controlled PR execution in GitHub UI | PNG evidence files in `docs/release/security-gate-evidence/` |
| Production endpoint field verification | Requires live environment access | Captured `/api/health` and `/api/integrity` responses |

## 3. Blocked on Green Runs

| Item | Blocking Dependency |
|---|---|
| Final PASS on release gate | Fresh successful CI and evidence artifact exports |
| Security gate PASS | Demonstrated blocking behavior on PR checks |
| Load test PASS | Availability of runtime environment and executed load suite |

## 4. Blocked on GitHub Settings Access

| Item | Access Needed |
|---|---|
| Enforce-admins confirmation | Repository admin privileges |
| Force-push/delete restriction proof | Repository admin privileges |
| Conversation resolution and codeowner proof | Repository admin privileges |

## 5. Blocked on Environment Access

| Item | Environment Requirement |
|---|---|
| Production health/integrity full payload capture | Access to production endpoint with proper tenant/auth headers |
| Load test final report generation | Accessible performance-test target environment |

## 6. Intentionally Deferred (Safety/Scope)

| Item | Reason Deferred |
|---|---|
| Deep workflow consolidation beyond Phase 2 removals | Requires validation against branch protection and live run history to avoid accidental gate regression |
| Additional root-file relocation beyond safe non-runtime moves | Avoiding runtime/deploy script breakage without full impact map |
| Branch-protection policy escalation (adding many required checks) | Must be done only after checks are green on main and agreed by maintainers |

## 7. Investor-Reviewability Statement

The repository is `investor-reviewable now` for documentation quality, governance visibility, and architecture/security narrative.

The repository is `not fully release-ready yet` until manual captures and green-run evidence are completed for:
- branch protection enforcement proof,
- security gate blocking proof,
- golden-path and tenant-isolation run artifacts,
- final load test artifacts,
- production endpoint field capture.
