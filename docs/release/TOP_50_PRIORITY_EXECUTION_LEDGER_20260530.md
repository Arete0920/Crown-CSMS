# Top 50 Priority Execution Ledger - 2026-05-30

## Scope

- Source list: docs/release/EVIDENCE_BASED_TOP_100_HARDENING_PRIORITIES_20260521.md
- This ledger covers priorities 1 through 50 in strict order.
- Authority handoff packet: `audit-artifacts/runtime-release-closure/20260418_070051/RELEASE_AUTHORITY_ACTION_PACKET_20260530.md`
- Same-day owner timeline board: `audit-artifacts/runtime-release-closure/20260418_070051/SAME_DAY_OWNER_TIMELINE_BOARD_20260530.md`
- Live infra escalation issue: `https://github.com/tcmegahan/Crown2026/issues/871`
- Governance decision log: `audit-artifacts/runtime-release-closure/20260418_070051/GOVERNANCE_DECISION_LOG_20260530.md`
- PR backlog closeout matrix: `audit-artifacts/runtime-release-closure/20260418_070051/PR_BACKLOG_CLOSEOUT_MATRIX_20260530.md`
- Issue blocker closeout plan: `audit-artifacts/runtime-release-closure/20260418_070051/ISSUE_BLOCKER_CLOSEOUT_PLAN_20260530.md`
- Status terms:
  - RESOLVED: repaired with direct evidence in this repo/session.
  - ADDRESSED-BLOCKED: investigated and actioned, but final closure depends on external/manual or broader follow-on work.

## Ordered Execution Status (1-50)

| Priority | Status | Evidence | Next Required Action |
| --- | --- | --- | --- |
| 1 | RESOLVED | listed DONE in source canon | none |
| 2 | RESOLVED | listed DONE in source canon | none |
| 3 | RESOLVED | PR 836 is merged (`gh pr view 836`) | none |
| 4 | ADDRESSED-BLOCKED | active PR surfaces remain unstable (`gh pr checks 869`: 43 failing, `gh pr checks 870`: 27 failing; 0 successful in both). Sampled failed jobs are pre-step runner failures (`steps=[]`, `runner_id=0`), and rerun of dependency-scan run `26676516965` reproduced same mode; artifact `pr_runner_prestep_failures_20260530.txt` | green active PR check matrix |
| 5 | RESOLVED | PR 836 merged to main | none |
| 6 | ADDRESSED-BLOCKED | latest main scheduled runs still failing on SHA `d22fabb685f5` (`26676524314`, `26676520864`); both fail pre-step with empty `steps` and no runner assignment (`runner_id=0`). Repeated reruns reproduce the same mode (latest: job `78631572332` for `26676524314`, job `78631572710` for `26676520864`). Artifact: `main_runner_prestep_failures_20260530.txt` | restore workflow runner execution on main, then rerun closeout |
| 7 | ADDRESSED-BLOCKED | worktree not clean (`working_tree_lines=60`) | reduce to clean tree before closeout |
| 8 | ADDRESSED-BLOCKED | main parity drift confirmed by config delta: `AUTH_USER_MODEL='core.UserAccount'` present on branch but absent on clean `origin/main` (causing initial main-lane `fields.E304`) | align branch with intended release SHA |
| 9 | ADDRESSED-BLOCKED | manual authority hold item | release owner manual decision |
| 10 | ADDRESSED-BLOCKED | manual founder acceptance item | signed acceptance record |
| 11 | ADDRESSED-BLOCKED | open PR backlog remains (`open_pr_count=8`; PRs `870, 869, 867, 866, 862, 861, 860, 859`) | close or merge backlog to target |
| 12 | ADDRESSED-BLOCKED | no fresh deploy proof in this run | deploy merged release and capture build_sha |
| 13 | RESOLVED | listed DONE in source canon | none |
| 14 | ADDRESSED-BLOCKED | dependency-review/dependency-audit jobs still red on active PRs, and sampled failure mode remains runner pre-step abort (`steps=[]`, `runner_id=0`) rather than in-job audit findings; evidence includes rerun in `pr_runner_prestep_failures_20260530.txt` | restore runner execution on PR lanes, then rerun backend dependency audit workflows |
| 15 | ADDRESSED-BLOCKED | dependency scan jobs (`Node - npm audit`, `Python - pip-audit`) fail pre-step with no runner allocation (`steps=[]`, `runner_id=0`) despite local clean artifacts; repeated reruns of run `26676516965` reproduce same failure (latest jobs `78631573409`, `78631573415`) in `pr_runner_prestep_failures_20260530.txt` | restore runner execution on PR lanes, then rerun dependency scan workflows |
| 16 | ADDRESSED-BLOCKED | main CI matrix remains non-green with infrastructure-like pre-step job failures (no executed steps; no runner attached) on scheduled workflows, and repeated reruns continue to reproduce the same failure pattern across both scheduled main workflows. Artifact: `main_runner_prestep_failures_20260530.txt` | stabilize main gate set |
| 17 | ADDRESSED-BLOCKED | no new PyJWT fixed-advisory transition event captured | monitor advisory and remove ignores when applicable |
| 18 | ADDRESSED-BLOCKED | no new flask-cors fixed-advisory transition event captured | monitor advisory and remove ignores when applicable |
| 19 | ADDRESSED-BLOCKED | load-test scope decision still governance-level | decide release-critical scope boundary |
| 20 | RESOLVED | backend pip-audit artifact: audit-artifacts/runtime-release-closure/20260418_070051/backend_pip_audit_final_20260530.json | none |
| 21 | RESOLVED | loadtest pip-audit artifact: audit-artifacts/runtime-release-closure/20260418_070051/loadtest_pip_audit_20260530.json | none |
| 22 | RESOLVED | frontend npm audit artifact: audit-artifacts/runtime-release-closure/20260418_070051/frontend_npm_audit_20260530.json | none |
| 23 | RESOLVED | root requirements delegates to backend requirements (`requirements.txt` contains `-r backend/requirements.txt`) | none |
| 24 | RESOLVED | fix dry-run artifact: audit-artifacts/runtime-release-closure/20260418_070051/backend_pip_audit_fix_dryrun_20260530.json | none |
| 25 | RESOLVED | listed DONE in source canon | none |
| 26 | RESOLVED | listed DONE in source canon | none |
| 27 | RESOLVED | listed DONE in source canon | none |
| 28 | RESOLVED | tenant artifact: audit-artifacts/runtime-release-closure/20260418_070051/tenant_isolation_pytest_artifact_20260530.txt | none |
| 29 | RESOLVED | tenant boundary matrix run passed (`46 passed, 1 skipped`) with evidence in `audit-artifacts/runtime-release-closure/20260418_070051/tenant_boundary_matrix_20260530.txt` | none |
| 30 | RESOLVED | finance-sensitive and write-path tenant tests included in tenant boundary matrix (`test_tenant_isolation_writes.py`) and passed | none |
| 31 | RESOLVED | cross-tenant and object-level permission surfaces revalidated in tenant boundary matrix (`test_object_level_permissions.py`) | none |
| 32 | RESOLVED | role-override and escalation boundary revalidated (`test_role_escalation.py`) | none |
| 33 | RESOLVED | invalid-tenant header handling revalidated (`tests/test_tenant_header_required.py`) | none |
| 34 | RESOLVED | nonexistent/invalid tenant UUID handling revalidated (`tests/test_tenant_header_validate_school.py`) | none |
| 35 | RESOLVED | auth token proof sweep passed (`11 passed`) with evidence in `audit-artifacts/runtime-release-closure/20260418_070051/auth_token_proof_sweep_20260530.txt` | none |
| 36 | RESOLVED | backend deploy check and settings posture sweep captured in `docs/release/BACKEND_AUTH_SECURITY_SWEEP_20260530.md` with no permissive CORS/debug failure signal | none |
| 37 | RESOLVED | on clean main-lane worktree, generated pending migrations for `home_academy`, `subscriptions`, `spiritual_life` and reran `makemigrations --check --dry-run` to `No changes detected` (artifacts: `main_lane_makemigrations_postgen_check_20260530.txt`, `main_lane_generated_migration_manifest_20260530.txt`) | none |
| 38 | RESOLVED | main-lane `manage.py check` rerun clean (0 issues) after AUTH_USER_MODEL fix; artifact: `main_lane_manage_check_20260530.txt` | closed |
| 39 | RESOLVED | listed DONE in source canon | none |
| 40 | RESOLVED | verify:full manifest and raw log captured in docs/release/FRONTEND_VERIFICATION_EVIDENCE_20260530.md | none |
| 41 | RESOLVED | bundle warning disposition documented in docs/release/FRONTEND_VERIFICATION_EVIDENCE_20260530.md | none |
| 42 | RESOLVED | frontend API contracts and navigation verification passed (`verify:api-contracts`, `verify:navigation`) with artifacts in runtime closure folder | none |
| 43 | ADDRESSED-BLOCKED | local release route smoke rerun passed (`frontend_release_routes_local_20260530.txt`), but post-deploy auth golden path still not rerun against deployed target | run post-deploy golden auth smoke |
| 44 | ADDRESSED-BLOCKED | local release a11y smoke rerun passed (`frontend_release_a11y_local_20260530.txt`), but post-deploy accessibility smoke still not rerun against deployed target | run post-deploy accessibility smoke |
| 45 | RESOLVED | role routing proof passed in verify:full (`ui:proof:nav`, `ui:proof:matrix-pack-3`) | none |
| 46 | RESOLVED | contract suite and shell/backend parity passed (`test:contracts`, `check:shell-backend-contract-parity`) | none |
| 47 | RESOLVED | playwright retention and reproducibility policy documented in docs/release/FRONTEND_VERIFICATION_EVIDENCE_20260530.md | none |
| 48 | RESOLVED | final signoff checklist now points to frontend verification evidence | none |
| 49 | RESOLVED | listed DONE in source canon | none |
| 50 | RESOLVED | listed DONE in source canon | none |

## Net Closure Summary (Top 50)

- RESOLVED: 35
- ADDRESSED-BLOCKED: 15

## Fresh Runtime Safety Recheck Completed In This Run

- backend dependency hardening applied in backend/requirements.txt
- backend pip-audit final result: no known vulnerabilities
- frontend npm audit result: no known vulnerabilities
- backend manage.py check: pass
- tenant isolation smoke (`--nomigrations`): 7 passed
- tenant/auth boundary matrix (`--nomigrations`): 46 passed, 1 skipped
