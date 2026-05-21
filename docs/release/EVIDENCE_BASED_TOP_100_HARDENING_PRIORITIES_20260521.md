<!-- markdownlint-disable MD012 MD029 MD032 -->

# Crown2026 Evidence-Based Top 100 Hardening Priorities

Generated: 2026-05-21

Purpose: rank the next 100 hardening and release-readiness priorities from currently verified repository evidence, not from generic best-practice guesswork.

Evidence sources used for this list:
- `audit-artifacts/release-closeout-proof/20260521-001341/release-closeout-scorecard.md`
- `PRODUCTION_GO_PRIORITIES_CHECKLIST.md`
- `docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md`
- current PR #836 blocker work and local validation runs on 2026-05-21

Status labels:
- `DONE` = completed with evidence in this branch/session
- `IN PROGRESS` = actively being worked in this branch/session
- `QUEUED` = actionable engineering task not yet started
- `MANUAL` = requires human decision, access, or sign-off
- `DEFERRED` = intentionally postponed until earlier gates are closed

## 1. Immediate Release Blockers

1. `DONE` Align unfixed Python advisory policy across all active `pip-audit` workflows.
2. `DONE` Re-validate tenant isolation suite after local cleanup using the repo virtualenv.
3. `QUEUED` Commit and push the current PR #836 blocker fixes from a clean review of staged changes.
4. `QUEUED` Get PR #836 status checks green after the latest workflow and test changes.
5. `QUEUED` Merge PR #836 into `main` once checks and review state are green.
6. `QUEUED` Re-run the release closeout proof gate on `main` only after merge.
7. `QUEUED` Clear the `working tree clean` failure before the main-only release proof run.
8. `QUEUED` Eliminate the `main sync` failure by aligning `main` with the approved release SHA.
9. `MANUAL` Lift the active release authority hold recorded in `docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md`.
10. `MANUAL` Replace the pending founder token in `docs/release/FOUNDER_ACCEPTANCE.md` with a real signed acceptance record.
11. `QUEUED` Close the open PR backlog failure after PR #836 merges.
12. `QUEUED` Deploy the merged release so production `build_sha` matches `main`.

## 2. Dependency and Supply Chain Controls

13. `DONE` Add explicit risk acceptance documentation for `PYSEC-2024-271` affecting transitive `flask-cors` in load-test resolution.
14. `QUEUED` Verify GitHub Actions Dependency Audit passes with both accepted unfixed advisories ignored.
15. `QUEUED` Verify GitHub Actions Dependency Scan passes with the same ignore set and artifact generation.
16. `QUEUED` Verify the crown main gate continues to warn cleanly for ignored unfixed advisories.
17. `QUEUED` Remove temporary ignore rules immediately when a fixed `PyJWT` release is published.
18. `QUEUED` Remove temporary ignore rules immediately when a fixed `flask-cors` release is published.
19. `QUEUED` Decide whether the load-test stack should remain in release-critical dependency scope or be isolated further.
20. `QUEUED` Export and retain a current `pip-audit` artifact for backend requirements.
21. `QUEUED` Export and retain a current `pip-audit` artifact for load-test requirements.
22. `QUEUED` Export and retain a current `npm audit` artifact for `frontend/dashboards`.
23. `QUEUED` Review root `requirements.txt` delegation to ensure audit behavior is unambiguous for CI and local runs.
24. `QUEUED` Re-check whether `pip-audit --fix` or upstream advisory metadata changes create a safer remediation path.

## 3. Backend Tenant and Auth Hardening

25. `DONE` Restore deterministic pytest discovery for audit and tenants smoke tests under `test_*.py` names.
26. `DONE` Prove tenant isolation behavior with a passing `backend/households/tests/test_tenant_isolation.py` run.
27. `DONE` Clean unnecessary password literals and dead imports from the tenant isolation test.
28. `QUEUED` Commit the tenant isolation pytest output as a durable release artifact if release docs require it.
29. `QUEUED` Review all endpoints that still permit empty-scope tenant behavior and decide whether they must hard-fail with `required=True`.
30. `QUEUED` Add explicit tests for any remaining finance-sensitive endpoints beyond `/api/billing/summary/`.
31. `QUEUED` Verify non-staff cross-tenant access returns `404` across all scoped detail routes, not just households and students.
32. `QUEUED` Verify staff override behavior is limited to intended roles and explicit headers only.
33. `QUEUED` Verify invalid tenant header handling is consistent across all scoped backend views.
34. `QUEUED` Verify nonexistent tenant UUID handling is consistent across all scoped backend views.
35. `QUEUED` Audit backend auth responses to ensure token success proof uses actual access-token presence, not assumed custom claims.
36. `QUEUED` Review backend settings for any permissive CORS or auth debug behavior not already covered by CI guards.
37. `QUEUED` Verify database migration dry-run remains clean after the PR merges to `main`.
38. `QUEUED` Capture a fresh backend `manage.py check` artifact on `main` as part of the final release packet.

## 4. Frontend Hardening and Verification

39. `DONE` Prove `frontend/dashboards` full verification passes end-to-end locally.
40. `QUEUED` Commit or index the latest `verify:full` manifest in the release evidence packet if required.
41. `QUEUED` Review the large bundle warning from the frontend build and decide whether chunk-splitting is required before GA.
42. `QUEUED` Verify no release-critical frontend route depends on a backend endpoint that is unavailable in prod.
43. `QUEUED` Re-check the release auth golden path after the next production deploy.
44. `QUEUED` Re-check release accessibility smoke after the next production deploy.
45. `QUEUED` Validate that frontend role routing still matches backend authorization after any post-merge changes.
46. `QUEUED` Confirm frontend contract tests remain current with backend shell contract versioning.
47. `QUEUED` Review Playwright report retention so final release evidence is reproducible.
48. `QUEUED` Ensure dashboard verification artifacts are included in final sign-off docs, not just local artifact directories.

## 5. CI and Workflow Hardening

49. `DONE` Expand active workflow coverage to include `backend/requirements-loadtest.txt`.
50. `DONE` Add CI authoring guard for load-test dependency audit coverage.
51. `QUEUED` Re-run the CI authoring meta-gate after merge to prove the new guard stays green on `main`.
52. `QUEUED` Review all workflow `paths` filters for release-critical files to prevent silent CI skips.
53. `QUEUED` Review all workflow caches for dependency-path drift after requirements changes.
54. `QUEUED` Verify each release-critical workflow uploads actionable artifacts on failure, not just console output.
55. `QUEUED` Audit workflow step names and job conditions again after merge to catch policy drift.
56. `QUEUED` Review concurrency groups for release-critical workflows to avoid canceled evidence runs.
57. `QUEUED` Ensure warn-only audit jobs are clearly separated from hard-fail release gates.
58. `QUEUED` Review workflow pinning for all third-party GitHub Actions used in release-critical jobs.
59. `QUEUED` Confirm `deploy-prod.yml` heredoc and auth-guard concerns are still resolved or still blocked exactly as documented.
60. `QUEUED` Export a fresh green PR check matrix after PR #836 is merged.

## 6. Production Deploy and Runtime Currentness

61. `QUEUED` Prove production `/api/health/` is healthy from the deployed release SHA on `main`.
62. `QUEUED` Prove production database health is `ok` from the same deployed release SHA.
63. `QUEUED` Eliminate the current production-sha mismatch that blocks release closeout.
64. `QUEUED` Capture the deployed `build_sha` payload in a committed release artifact.
65. `QUEUED` Capture the deployed health payload in a committed release artifact.
66. `QUEUED` Verify no post-proof redeploy changed production after final sign-off evidence is collected.
67. `QUEUED` Confirm release appsettings remain frozen after deployment.
68. `QUEUED` Re-run post-deploy validation gates for health, DB, auth, authz, performance, and data isolation.
69. `QUEUED` Confirm rollback instructions are current for the exact deployed SHA.
70. `MANUAL` Assign clear release authority for the production deployment decision and rollback decision.

## 7. Evidence, Governance, and Manual Captures

71. `QUEUED` Export the latest green-on-main evidence snapshot required by `KNOWN_GAPS_AND_DEFERRED_ITEMS.md`.
72. `QUEUED` Commit tenant isolation pytest artifact if final release packet still requires it.
73. `QUEUED` Commit golden path pytest artifact if final release packet still requires it.
74. `QUEUED` Commit final load test HTML/CSV artifacts if final release packet still requires them.
75. `MANUAL` Capture branch protection UI proof with repository-admin access.
76. `MANUAL` Capture security-gate blocking screenshots with controlled PR execution.
77. `MANUAL` Capture production endpoint field verification requiring live environment access.
78. `QUEUED` Refresh the release evidence index so it points at the newest artifacts, not stale runs.
79. `QUEUED` Generate a fresh immutable decision record after the main-only closeout gate passes.
80. `QUEUED` Verify evidence file integrity and immutability before final sign-off.
81. `MANUAL` Obtain founder or product-owner final acceptance on the actual release candidate.
82. `MANUAL` Obtain compliance and operations sign-off on the actual release candidate.

## 8. Repository Hygiene and Static Quality

83. `QUEUED` Resolve modified and deleted files into an intentional commit set instead of a broad `git add .` sweep.
84. `QUEUED` Separate release-critical code changes from artifact churn where possible before merge.
85. `QUEUED` Review remaining hard-coded test credentials or tokens in the repo and eliminate nonessential ones.
86. `QUEUED` Review local scripts for relative-path assumptions that break when run from nested artifact directories.
87. `DONE` Harden `scripts/crown_finish_now.ps1` to default to audit-only behavior and collision-safe outputs.
88. `QUEUED` Re-parse and smoke-check all release-critical PowerShell scripts from repo root with absolute paths.
89. `QUEUED` Audit root-level operational documents for stale “complete” claims that no longer match current evidence.
90. `QUEUED` Reduce noisy artifact-directory search drift by tightening documented search scopes for future work.
91. `QUEUED` Decide which generated artifacts belong in git and which should be excluded or moved.
92. `QUEUED` Review type-checker setup for Django tests so editor diagnostics are actionable rather than mostly false positives.

## 9. Security Review Deepening

93. `QUEUED` Re-run CodeQL or equivalent static security analysis on the merge candidate and review any live findings.
94. `QUEUED` Review repository secret-handling examples (`.env.example`, local examples, scripts) for accidental production leakage patterns.
95. `QUEUED` Review all tenant header injection paths to ensure clients cannot bypass school scoping unexpectedly.
96. `QUEUED` Review logging paths for possible untrusted input injection, especially in debug-only dependencies and operational tooling.
97. `QUEUED` Verify CORS policy remains least-privilege in production settings and environment-specific overrides.
98. `QUEUED` Verify release-critical endpoints do not expose extra data fields beyond what tests currently assert.
99. `QUEUED` Reconfirm that backend and frontend authorization models fail closed under unknown or new roles.
100. `QUEUED` Perform a final evidence-first production-readiness review on `main` after all preceding priorities are complete.

## Operating Rules For This Backlog

- Do not mark any item complete without same-turn evidence.
- Prefer the smallest root-cause fix that changes the gate outcome.
- Treat `MANUAL` items as tracked blockers, not engineering-complete work.
- Re-rank this list after PR #836 merges and the main-only release closeout gate is rerun.

