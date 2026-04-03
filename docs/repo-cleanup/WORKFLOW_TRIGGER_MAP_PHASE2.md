# Workflow Trigger Map — Phase 2

Generated: Phase 2 cleanup pass  
Branch: `chore/github-cleanup-phase2-workflows-prs`

This table maps every workflow to its triggers, affected branches, environment coupling,
and branch-protection relevance signal. Use this to understand what fires when and
which workflows block merges to `main`.

Legend — Trigger abbreviations:
- `PR` = pull_request
- `PUSH` = push  
- `DISP` = workflow_dispatch
- `SCHED` = schedule (cron)
- `CALL` = workflow_call
- `WF_RUN` = workflow_run (fires after another workflow)
- `REPO_DISP` = repository_dispatch

Legend — Gate Signal:
- `BLOCKS_MAIN` = job name is a required check configured in branch protection
- `MAIN_PR` = runs on PRs targeting main but not currently a required check
- `NON_GATE` = does not run on main PRs (deploy, dispatch, smoke, etc.)

---

## Trigger Map

| File | Triggers | Push Branches | PR Branches | Environment | Gate Signal | Notes |
|---|---|---|---|---|---|---|
| `azure-drift-watchdog.yml` | DISP, SCHED | — | — | — | NON_GATE | Cron: Mon 05:00 UTC |
| `backend-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `backend-gate` |
| `backend-shell-seeded-proof.yml` | PUSH, PR, DISP | all | all | — | MAIN_PR | No branch filters |
| `backend-shell-write-and-lifecycle-proof.yml` | PUSH, PR, DISP | all | all | — | MAIN_PR | No branch filters |
| `ci-meta-gate-authoring.yml` | PR | — | all (path-filtered) | — | MAIN_PR | Paths: `.github/workflows/**`, `tools/ci/**` |
| `ci.yml` | PUSH, PR | main | main | — | MAIN_PR | Jobs: `verify-immutable-tags`, `test` |
| `codeql.yml` | PUSH, PR, SCHED | main, develop | main, develop | — | MAIN_PR | Cron: weekly |
| `contract-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Jobs: `contract-gate`, `source-contracts` |
| `crown-magus0-gate.yml` | PUSH, PR, DISP | `"main"` | `"main"` | — | MAIN_PR | 5 jobs; comprehensive audit |
| `dashboards-build-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `dashboards-build-gate` |
| `demo-contract-freeze.yml` | PUSH, PR | `rc/**` | `rc/**` | — | NON_GATE | Scoped to rc/** only |
| `demo-reset-smoke.yml` | DISP | — | — | — | NON_GATE | No branch context |
| `demo-reset.yml` | DISP | — | — | — | NON_GATE | No branch context |
| `demo-surface-gate.yml` | PR, DISP | — | `"main"` | — | MAIN_PR | **REMOVE_NOW** |
| `dependency-audit.yml` | PUSH, PR | main, develop | main | — | MAIN_PR | Jobs: `backend-pip-audit`, `frontend-npm-audit` |
| `dependency-review.yml` | PR | — | all | — | MAIN_PR | GitHub Action; all PRs |
| `dependency-scan.yml` | PUSH, PR, SCHED | main, chore/**, feat/**, fix/** | main | — | MAIN_PR | Cron: Mon 06:00 UTC; overlaps `dependency-audit.yml` |
| `deploy-dashboard.yml` | PUSH | main | — | — | NON_GATE | Tag: `dashboard-deploy-*` trigger inferred |
| `deploy-dev.yml` | PUSH, DISP | `rc/**` | — | dev | NON_GATE | Push to rc/** |
| `deploy-integrity-proof.yml` | DISP | — | — | — | NON_GATE | Manual dispatch only |
| `deploy-prod-dispatch.yml` | DISP, REPO_DISP | — | — | production | NON_GATE | Manual/API triggered |
| `deploy-prod.yml` | PUSH | tags: `prod-deploy-*` | — | production | NON_GATE | Tag-triggered only |
| `dev-smoke-azure-dev.yml` | DISP | — | — | dev | NON_GATE | Azure DEV target |
| `dev-smoke.yml` | DISP | — | — | — | NON_GATE | Local golden-path smoke |
| `frontend-shell-certification.yml` | PUSH, PR, DISP | all | all | — | MAIN_PR | No branch filters |
| `gradebookro-ui-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `gate` (28 lines) |
| `lockdown-golden-path-gate.yml` | PUSH, PR, DISP | main | main | — | MAIN_PR | 328 lines; `changes` + `lockdown-gate` jobs |
| `migration-lock-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `gate` |
| `msgraph-smoke.yml` | PUSH, PR, DISP | `stabilization-20260116-spine` | `stabilization-20260116-spine` | — | NON_GATE | **REMOVE_NOW** — dead branch |
| `ops-reset-dev.yml` | DISP | — | — | dev | NON_GATE | Manual DEV reset |
| `phase1-gate.yml` | PR, DISP | — | `"main"` | — | MAIN_PR | **REMOVE_LATER** |
| `phase3-demo-proof-pack.yml` | PR, DISP | — | main | — | MAIN_PR | **REMOVE_LATER** |
| `phase3-runtime-proof.yml` | PR, DISP | — | main | — | MAIN_PR | **REMOVE_LATER** |
| `phase4-gradebook-demo-proof.yml` | PR, DISP | — | all | — | MAIN_PR | **REMOVE_LATER** |
| `prod-health-watch.yml` | DISP, SCHED | — | — | — | NON_GATE | Cron scheduled |
| `prod-integrity-proof.yml` | DISP, SCHED | — | — | — | NON_GATE | Cron scheduled |
| `proof-ceremony-after-prod.yml` | WF_RUN | — | — | — | NON_GATE | Fires after `deploy-prod.yml` / `deploy-prod-dispatch.yml` success |
| `proof-ceremony-prod.yml` | DISP | — | — | — | NON_GATE | Manual with inputs (tag + api_base) |
| `proof-ceremony.yml` | PUSH, PR, DISP | release/**, stabilize/** | main, release/**, stabilize/** | — | **BLOCKS_MAIN** | `proof-ceremony` job = **sole required check in ruleset_main.json** |
| `proof-gradebook.yml` | PR, DISP | — | main | — | MAIN_PR | Self-hosted runner |
| `pytest-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `pytest-gate` |
| `rc-build-sha-proof.yml` | PUSH, DISP | all | — | — | NON_GATE | No PR trigger |
| `rc-gate.yml` | PUSH, PR | all | all | — | MAIN_PR | No branch filter; runs everywhere |
| `rc-promotion-gate.yml` | PR | — | `"main"` | — | MAIN_PR | Main PR required gate |
| `rc-runbook.yml` | PUSH, PR | all | all | — | MAIN_PR | No branch filter — fires on all branches |
| `rc-tier1-deployed-smoke.yml` | PUSH, PR, DISP | all | all | — | NON_GATE | Smoke against live env |
| `routes-gate.yml` | PUSH, PR | `"main"` | `"main"` | — | MAIN_PR | Job: `routes-gate` |
| `secret-scan.yml` | PUSH, PR | main, develop | main, develop | — | MAIN_PR | Gitleaks |
| `shell-backend-contract-parity.yml` | PUSH, PR, DISP | main | main | — | MAIN_PR | Parity check |
| `spine-audit.yml` | PUSH, PR | main | main | — | MAIN_PR | Job: `spine-audit` |
| `system-health.yml` | DISP | — | — | — | NON_GATE | Manual dispatch |
| `tests.yml` | PUSH, PR | main, spine/** | all | — | MAIN_PR | Self-hosted runner; duplicates `ci.yml` (**MERGE_INTO_CANONICAL**) |
| `ui-proof-gate.yml` | PR, DISP | — | main | — | MAIN_PR | Job: `ui-smoke` |
| `ui-proof-gates.yml` | PR, DISP | — | main | — | MAIN_PR | Job: `dashboard-ui-gates` |
| `ui-shell-gate.yml` | PUSH, PR | main | main | — | MAIN_PR | Job: `ui-shell-gate` |

---

## High-Risk Observations

### 1. Only One Required Check Configured
`ruleset_main.json` has a single required status check:

```
context: "proof-ceremony"
```

This means **every other MAIN_PR workflow is advisory-only** — they run on PRs but do not block merges.
A failing `backend-gate`, `pytest-gate`, `migration-lock-gate`, or `codeql` will NOT block a merge to main.

### 2. Unfiltered Branch Triggers (Noise Generators)
These workflows trigger on **all** push/PR events with no branch filter:

- `backend-shell-seeded-proof.yml` — all branches, all PRs
- `backend-shell-write-and-lifecycle-proof.yml` — all branches, all PRs
- `frontend-shell-certification.yml` — all branches, all PRs
- `rc-gate.yml` — all branches, all PRs
- `rc-runbook.yml` — all branches, all PRs
- `rc-tier1-deployed-smoke.yml` — all branches, all PRs
- `tests.yml` — all PRs (push filtered to main/spine/**)

These consume runner minutes and create noise in the checks UI without being required.

### 3. Stale Branch Reference
`msgraph-smoke.yml` fires automatically on push/PR to `stabilization-20260116-spine`.
That branch is a closed stabilization window from January 2026 and is not an active branch.

### 4. Self-Hosted Runner Dependency
The following workflows require `self-hosted, linux, x64, crown-runner`:
- `ci.yml` (job: `test`)
- `proof-ceremony.yml` (job: `proof-ceremony`) — **this is the required check**
- `tests.yml` (job: `pytest`)

If the crown-runner is offline, the **only required check** (`proof-ceremony`) will stall indefinitely.
