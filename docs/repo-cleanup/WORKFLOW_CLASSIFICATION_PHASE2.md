# Workflow Classification — Phase 2

Generated: Phase 2 cleanup pass
Branch: `chore/github-cleanup-phase2-workflows-prs`
Total workflows surveyed: 54

## Classification Labels

| Label | Meaning |
|---|---|
| `KEEP_CANONICAL` | Authoritative workflow; must not be removed |
| `KEEP_EXCEPTION` | Valid unique purpose, not a duplicate |
| `MERGE_INTO_CANONICAL` | Duplicate; function covered by a canonical workflow |
| `REMOVE_NOW` | Safe to delete: dead branch, zero-logic static check, or fully superseded |
| `REMOVE_LATER` | Phase-specific artifact; safe to remove after current phase ships |
| `REVIEW_REQUIRED` | Unclear ownership or overlap; requires human decision before removal |

---

## Classification Table

| File | Name | Classification | Rationale |
|---|---|---|---|
| `azure-drift-watchdog.yml` | Azure Drift Watchdog | `KEEP_CANONICAL` | Scheduled Azure infra drift detection; unique, no overlap |
| `backend-gate.yml` | backend-gate | `KEEP_CANONICAL` | Canonical backend push/PR gate on main; maps to required check |
| `backend-shell-seeded-proof.yml` | Backend Shell Seeded Proof | `REVIEW_REQUIRED` | Seeded DB proof; unclear if superseded by `ci.yml` or `proof-ceremony.yml` |
| `backend-shell-write-and-lifecycle-proof.yml` | Backend Shell Write And Lifecycle Proof | `REVIEW_REQUIRED` | Lifecycle proof; similar to above — overlaps with `proof-ceremony.yml` |
| `ci-meta-gate-authoring.yml` | ci-meta-gate-authoring | `KEEP_CANONICAL` | Runs `check_no_pr_job_if.py` + `check_workflow_step_names.py` on workflow/CI changes; unique governance value |
| `ci.yml` | CI - Tests and Checks | `KEEP_CANONICAL` | **Primary gate**: `verify-immutable-tags` + `test` jobs on push/PR to main; governance-critical |
| `codeql.yml` | CodeQL Security Analysis | `KEEP_CANONICAL` | GitHub Advanced Security SAST; scheduled + on main |
| `contract-gate.yml` | contract-gate | `KEEP_CANONICAL` | API contract validation gate on main PRs; unique |
| `crown-magus0-gate.yml` | crown-magus0-gate | `KEEP_CANONICAL` | Multi-layer audit gate: backend, secret, frontend, dep, pytest; comprehensive on main |
| `dashboards-build-gate.yml` | dashboards-build-gate | `KEEP_CANONICAL` | Frontend dashboard build gate on main PRs |
| `demo-contract-freeze.yml` | demo-contract-freeze | `KEEP_EXCEPTION` | Tier-1 hash-lock check scoped to `rc/**` only; distinct from main gate |
| `demo-reset-smoke.yml` | Demo Reset + Smoke | `MERGE_INTO_CANONICAL` | Combines `demo-reset.yml` + smoke; dispatch-only; redundant alongside `demo-reset.yml` + `dev-smoke.yml` |
| `demo-reset.yml` | Demo Reset | `KEEP_CANONICAL` | Canonical manual demo environment reset (dispatch-only) |
| `demo-surface-gate.yml` | demo-surface-gate | `REMOVE_NOW` | 18-line static PowerShell reachability check; superseded by `contract-gate.yml` and `phase3-demo-proof-pack.yml` |
| `dependency-audit.yml` | Dependency Audit | `KEEP_CANONICAL` | Canonical pip-audit + npm-audit on push/PR; clear output job names |
| `dependency-review.yml` | Dependency Review | `KEEP_CANONICAL` | GitHub native dependency review on PRs (separate from audit; uses GitHub Action) |
| `dependency-scan.yml` | Dependency Scan | `MERGE_INTO_CANONICAL` | `safety` + `pip-audit` + `node-audit` on push/PR — overlaps with `dependency-audit.yml`; the `safety` job has `continue-on-error: true` making it informational only; consolidate into `dependency-audit.yml` |
| `deploy-dashboard.yml` | Deploy Dashboard (Production) | `KEEP_CANONICAL` | Canonical frontend dashboard deploy on push to main |
| `deploy-dev.yml` | Dev Deploy | `KEEP_CANONICAL` | Canonical dev deploy on push to `rc/**` |
| `deploy-integrity-proof.yml` | deploy-integrity-proof | `REVIEW_REQUIRED` | Post-deploy SHA verification (dispatch-only); may overlap with `proof-ceremony-after-prod.yml` |
| `deploy-prod-dispatch.yml` | Production Deploy (Dispatch v2) | `KEEP_CANONICAL` | Manual/repository_dispatch prod deploy trigger; distinct from tag-triggered `deploy-prod.yml` |
| `deploy-prod.yml` | Production Deploy | `KEEP_CANONICAL` | **Primary prod deploy**: tag-triggered (`prod-deploy-*`), environment: production |
| `dev-smoke-azure-dev.yml` | Azure DEV Smoke (Deterministic) | `KEEP_EXCEPTION` | Deterministic Azure DEV smoke (dispatch-only) with specific env vars; distinct from local `dev-smoke.yml` |
| `dev-smoke.yml` | DEV Smoke - Golden Path | `KEEP_CANONICAL` | Canonical golden-path DEV smoke (dispatch-only) |
| `frontend-shell-certification.yml` | Frontend Shell Certification | `KEEP_EXCEPTION` | Frontend shell certification proof; distinct from build gates |
| `gradebookro-ui-gate.yml` | gradebookro-ui-gate | `REVIEW_REQUIRED` | 28-line gate for gradebook read-only UI; unclear if still active or superseded by `proof-gradebook.yml` |
| `lockdown-golden-path-gate.yml` | Lockdown Golden Path Gate | `KEEP_CANONICAL` | Comprehensive lockdown gate (328 lines) for main; checks golden path + immutable-tags |
| `migration-lock-gate.yml` | migration-lock-gate | `KEEP_CANONICAL` | Blocks PRs that add unapproved migrations; critical data integrity gate |
| `msgraph-smoke.yml` | MS Graph Smoke Test (OIDC) | `REMOVE_NOW` | **Hardcoded** to dead branch `stabilization-20260116-spine`; that branch no longer exists in canon; dispatch still works but no automatic value |
| `ops-reset-dev.yml` | OPS - Reset DEV Demo | `MERGE_INTO_CANONICAL` | Single-curl DEV reset with school_id input; function covered by `demo-reset.yml` with more complete impl |
| `phase1-gate.yml` | phase1-gate | `REMOVE_LATER` | Phase 1 static contract gate; phase 1 is shipped — can be retired after Phase 2 PR merges |
| `phase3-demo-proof-pack.yml` | Phase3 Demo Proof Pack Gate | `REMOVE_LATER` | 17-line Phase 3 static gate; Phase 3 is shipped |
| `phase3-runtime-proof.yml` | Phase3 Runtime Proof Ceremony | `REMOVE_LATER` | Phase 3 runtime proof; superseded by general `proof-ceremony.yml` pattern |
| `phase4-gradebook-demo-proof.yml` | Phase4 Gradebook Demo Proof | `REMOVE_LATER` | Phase 4 gradebook demo; superseded by `proof-gradebook.yml` |
| `prod-health-watch.yml` | Production Health Watch | `KEEP_CANONICAL` | Scheduled prod health monitoring; distinct from one-time proof ceremonies |
| `prod-integrity-proof.yml` | prod-integrity-proof | `REVIEW_REQUIRED` | 119-line dispatch+schedule integrity proof; may overlap with `proof-ceremony-after-prod.yml` |
| `proof-ceremony-after-prod.yml` | proof-ceremony-after-prod | `KEEP_CANONICAL` | **Auto-runs** after prod deploy workflows succeed via `workflow_run`; critical post-deploy assertion |
| `proof-ceremony-prod.yml` | proof-ceremony-prod | `KEEP_EXCEPTION` | Manual post-deploy proof with explicit tag + API base URL inputs; distinct from auto version |
| `proof-ceremony.yml` | Proof Ceremony | `KEEP_CANONICAL` | **Required check for `main`** per `ruleset_main.json`; must not be removed |
| `proof-gradebook.yml` | Proof — Gradebook (UI + API) | `KEEP_EXCEPTION` | Dedicated gradebook proof with UI + API assertions; runs on self-hosted runner |
| `pytest-gate.yml` | pytest-gate | `KEEP_CANONICAL` | Standalone pytest gate on push/PR to main; job name `pytest-gate` used in check contexts |
| `rc-build-sha-proof.yml` | RC Build-SHA Health Proof | `KEEP_EXCEPTION` | RC-phase SHA proof; required for RC promotion confidence |
| `rc-gate.yml` | rc-gate | `KEEP_CANONICAL` | Comprehensive RC branch gate: backend, frontend build, static UI gates |
| `rc-promotion-gate.yml` | rc-promotion-gate | `KEEP_CANONICAL` | RC → main promotion gate (blocking on main PRs from rc branches) |
| `rc-runbook.yml` | rc-runbook | `REVIEW_REQUIRED` | RC runbook workflow (push/PR on all branches); may be documentation-only or low-value |
| `rc-tier1-deployed-smoke.yml` | rc-tier1-deployed-smoke | `KEEP_EXCEPTION` | Post-RC-deploy tier-1 smoke against live env; distinct from gate workflows |
| `routes-gate.yml` | routes-gate | `KEEP_CANONICAL` | URL routes contract gate on main PRs |
| `secret-scan.yml` | secret-scan | `KEEP_CANONICAL` | Gitleaks secret scan on push/PR to main/develop |
| `shell-backend-contract-parity.yml` | Shell Backend Contract Parity | `KEEP_EXCEPTION` | Shell-to-backend parity check; distinct contract surface |
| `spine-audit.yml` | Spine Audit (Canon Guard) | `KEEP_CANONICAL` | Canon-layer audit on push/PR to main; guards spine integrity |
| `system-health.yml` | Crown System Health Gate | `REVIEW_REQUIRED` | 112-line dispatch health gate; may overlap with `prod-health-watch.yml` |
| `tests.yml` | Tests | `MERGE_INTO_CANONICAL` | Runs `pytest` on self-hosted runner on push to main/spine/**; **fully duplicated** by `ci.yml` which also runs tests on push/PR to main |
| `ui-proof-gate.yml` | UI Proof Gate | `REVIEW_REQUIRED` | 51-line UI smoke on PR/dispatch to main; may overlap with `ui-proof-gates.yml` |
| `ui-proof-gates.yml` | UI Proof — Dashboard Gates | `KEEP_CANONICAL` | Canonical dashboard UI gates (student, parent, executive personas) on main PRs |
| `ui-shell-gate.yml` | ui-shell-gate | `KEEP_CANONICAL` | Frontend shell gate on push/PR to main |

---

## Summary Counts

| Classification | Count |
|---|---|
| KEEP_CANONICAL | 26 |
| KEEP_EXCEPTION | 9 |
| MERGE_INTO_CANONICAL | 4 |
| REMOVE_NOW | 2 |
| REMOVE_LATER | 4 |
| REVIEW_REQUIRED | 9 |
| **Total** | **54** |

---

## REMOVE_NOW Candidates (Action Required This Phase)

These two workflows are safe to delete immediately:

| File | Reason |
|---|---|
| `msgraph-smoke.yml` | Hardcoded to deleted branch `stabilization-20260116-spine`; no current gate value |
| `demo-surface-gate.yml` | 18-line static PowerShell check; logic fully superseded by `contract-gate.yml` |

## REMOVE_LATER Candidates (Schedule for Phase 3)

| File | Condition for Removal |
|---|---|
| `phase1-gate.yml` | After Phase 1 PR queue is cleared and phase 1 contracts are validated in main |
| `phase3-demo-proof-pack.yml` | After Phase 3 milestones confirmed merged to main |
| `phase3-runtime-proof.yml` | After Phase 3 confirmed shipped |
| `phase4-gradebook-demo-proof.yml` | After Phase 4 gradebook milestone confirmed merged |

## MERGE_INTO_CANONICAL Candidates (Phase 3 Consolidation Work)

| Source | Merge Target | Notes |
|---|---|---|
| `demo-reset-smoke.yml` | `demo-reset.yml` | Add optional smoke step to `demo-reset.yml` as `workflow_dispatch` input |
| `dependency-scan.yml` | `dependency-audit.yml` | Consolidate `safety` check as optional step; remove `continue-on-error` |
| `ops-reset-dev.yml` | `demo-reset.yml` | Unify school_id input; single DEV reset workflow |
| `tests.yml` | `ci.yml` | `tests.yml` pytest job is fully covered by `ci.yml` test job |
