# Required Checks Map — Phase 2

Generated: Phase 2 cleanup pass  
Branch: `chore/github-cleanup-phase2-workflows-prs`  
Evidence source: `ruleset_main.json`, `.github/workflows/`

---

## Current Branch Protection Configuration

Ruleset: `protect-main`  
Target: `refs/heads/main`  
Enforcement: `active`

### Rules Active

| Rule Type | Detail |
|---|---|
| `pull_request` | 1 required approving review; dismiss stale reviews on push |
| `required_status_checks` | **1 check** (see below); strict mode enabled |
| `deletion` | Force-delete of `main` blocked |
| `non_fast_forward` | Force-push to `main` blocked |

### Required Status Checks (Current)

| Context Name | Workflow Source | Job Name | Trigger | Runner |
|---|---|---|---|---|
| `proof-ceremony` | `proof-ceremony.yml` | `proof-ceremony` | push/PR to main | `self-hosted, linux, x64, crown-runner` |

**Critical finding:** Only **one** status check is configured as required in branch protection.
All other gates run as advisory checks. A failing `backend-gate`, `migration-lock-gate`,
`pytest-gate`, `codeql`, or `secret-scan` will NOT block a merge to main.

---

## Recommended Required Checks (Phase 3 Action)

The following workflows contain jobs that protect material production risk but are currently
advisory. These should be added to `ruleset_main.json` as required status checks in Phase 3.

### Tier 1 — Strongly Recommended (block merges to main)

| Context Name | Job Source | Workflow | Rationale |
|---|---|---|---|
| `proof-ceremony` | `proof-ceremony.yml` | `proof-ceremony` | ✅ Already required |
| `backend-gate` | `backend-gate.yml` | `backend-gate` | Blocks broken backend on main PRs |
| `test` | `ci.yml` | `ci.yml` | Full test suite on main; currently advisory |
| `pytest-gate` | `pytest-gate.yml` | `pytest-gate` | Pytest on main |
| `migration-lock-gate` (job: `gate`) | `migration-lock-gate.yml` | `migration-lock-gate` | Blocks unapproved migrations |
| `routes-gate` | `routes-gate.yml` | `routes-gate` | Blocks broken URL routing |
| `secret-scan` (job: `secret-scan`) | `secret-scan.yml` | `secret-scan` | Blocks credential leaks |
| `contract-gate` | `contract-gate.yml` | `contract-gate` | Blocks API contract breaks |

### Tier 2 — Recommended (block on main PRs)

| Context Name | Job Source | Workflow | Rationale |
|---|---|---|---|
| `analyze` (Python) | `codeql.yml` | `codeql` | SAST; currently configured with `continue-on-error` implications |
| `backend-pip-audit` | `dependency-audit.yml` | `dependency-audit` | Blocks known-vulnerable Python deps |
| `frontend-npm-audit` | `dependency-audit.yml` | `dependency-audit` | Blocks known-vulnerable Node deps |
| `dependency-review` | `dependency-review.yml` | `dependency-review` | GitHub native dep review |
| `spine-audit` | `spine-audit.yml` | `spine-audit` | Blocks canon-layer drift |
| `rc-promotion-gate` (job: `gate`) | `rc-promotion-gate.yml` | `rc-promotion-gate` | Ensures RC gate passed before promotion |

### Tier 3 — Consider Later

| Context Name | Workflow | Condition |
|---|---|---|
| `crown-magus0-gate` (multiple jobs) | `crown-magus0-gate.yml` | After magus gate is stable; adds comprehensive coverage |
| `dashboards-build-gate` | `dashboards-build-gate.yml` | After frontend stabilizes |
| `ui-shell-gate` | `ui-shell-gate.yml` | After frontend stabilizes |

---

## Check Context Name Mapping

This table maps the GitHub status check context (what appears in branch protection settings and
the Checks UI) to the workflow file and job that produces it.

| Status Check Context | Workflow File | Job Name |
|---|---|---|
| `proof-ceremony` | `proof-ceremony.yml` | `proof-ceremony` |
| `backend-gate` | `backend-gate.yml` | `backend-gate` |
| `verify-immutable-tags` | `ci.yml` | `verify-immutable-tags` |
| `test` | `ci.yml` | `test` |
| `analyze` | `codeql.yml` | `analyze` |
| `contract-gate` | `contract-gate.yml` | `contract-gate` |
| `source-contracts` | `contract-gate.yml` | `source-contracts` |
| `backend-audit` | `crown-magus0-gate.yml` | `backend-audit` |
| `secret-audit` | `crown-magus0-gate.yml` | `secret-audit` |
| `frontend-audit` | `crown-magus0-gate.yml` | `frontend-audit` |
| `dep-audit` | `crown-magus0-gate.yml` | `dep-audit` |
| `pytest-audit` | `crown-magus0-gate.yml` | `pytest-audit` |
| `dashboards-build-gate` | `dashboards-build-gate.yml` | `dashboards-build-gate` |
| `freeze` | `demo-contract-freeze.yml` | `freeze` |
| `demo-surface-static-gate` | `demo-surface-gate.yml` | `demo-surface-static-gate` |
| `backend-pip-audit` | `dependency-audit.yml` | `backend-pip-audit` |
| `frontend-npm-audit` | `dependency-audit.yml` | `frontend-npm-audit` |
| `dependency-review` | `dependency-review.yml` | `dependency-review` |
| `gate` (gradebook) | `gradebookro-ui-gate.yml` | `gate` |
| `changes` | `lockdown-golden-path-gate.yml` | `changes` |
| `lockdown-gate` | `lockdown-golden-path-gate.yml` | `lockdown-gate` |
| `gate` (migration) | `migration-lock-gate.yml` | `gate` |
| `pytest-gate` | `pytest-gate.yml` | `pytest-gate` |
| `backend-gates` | `rc-gate.yml` | `backend-gates` |
| `frontend-build` | `rc-gate.yml` | `frontend-build` |
| `ui-static-gates` | `rc-gate.yml` | `ui-static-gates` |
| `gate` (rc-promotion) | `rc-promotion-gate.yml` | `gate` |
| `routes-gate` | `routes-gate.yml` | `routes-gate` |
| `secret-scan` | `secret-scan.yml` | `secret-scan` |
| `parity` | `shell-backend-contract-parity.yml` | `parity` |
| `spine-audit` | `spine-audit.yml` | `spine-audit` |
| `pytest` | `tests.yml` | `pytest` |
| `ui-smoke` | `ui-proof-gate.yml` | `ui-smoke` |
| `dashboard-ui-gates` | `ui-proof-gates.yml` | `dashboard-ui-gates` |
| `ui-shell-gate` | `ui-shell-gate.yml` | `ui-shell-gate` |

---

## Governance Gap: Advisory-Only Protection

As of Phase 2, the branch protection for `main` relies on a single required check
(`proof-ceremony`) and 1 approving review. The following security/integrity gaps exist:

1. **No required test check** — broken tests merge silently
2. **No required migration gate** — unapproved migrations merge silently
3. **No required secret scan** — credential leaks are advisory only
4. **No required CodeQL gate** — SAST findings are informational only
5. **No required contract check** — API contract drift is advisory only

See `GOVERNANCE_GAPS_PHASE2.md` for full risk register.
