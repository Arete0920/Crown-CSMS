# Governance Gaps — Phase 2

Generated: Phase 2 cleanup pass  
Branch: `chore/github-cleanup-phase2-workflows-prs`

This document records all identified CI/CD governance gaps discovered during the Phase 2 audit.
All findings are based on observed evidence (workflow files, `ruleset_main.json`, PR states).
No fixes are applied in this document — see `PHASE3_RECOMMENDATIONS.md` for actions.

---

## Gap 1: Single Required Check — Inadequate Branch Gate

**Severity: HIGH**

`ruleset_main.json` configures exactly one required status check:

```json
{ "context": "proof-ceremony" }
```

At present, passing `proof-ceremony` is the only CI requirement to merge to `main`.
The following high-impact workflows run on main PRs but are **advisory only**:

| Workflow | Job | Risk if skipped |
|---|---|---|
| `ci.yml` | `test` | Broken tests merge silently |
| `pytest-gate.yml` | `pytest-gate` | Duplicate risk with above |
| `backend-gate.yml` | `backend-gate` | Backend import errors ignored |
| `migration-lock-gate.yml` | `gate` | Unapproved migrations land in main |
| `routes-gate.yml` | `routes-gate` | Broken URL routing ships |
| `secret-scan.yml` | `secret-scan` | Credential leaks not blocked |
| `contract-gate.yml` | `contract-gate` | API contract drift ships |
| `codeql.yml` | `analyze` | SAST vulnerabilities admitted |
| `dependency-audit.yml` | `backend-pip-audit` | Known-CVE deps merge |

**Impact:** Any one of these workflows failing will not block a PR from merging with one approval.

---

## Gap 2: Required Check Runs on Self-Hosted Runner — Single Point of Failure

**Severity: HIGH**

The only required check (`proof-ceremony`) runs on:

```
runs-on: [self-hosted, linux, x64, crown-runner]
```

If the `crown-runner` is offline, **all PRs to main will stall indefinitely** — no merge is possible
until the runner comes back online. There is no fallback to `ubuntu-latest`.

Additionally:
- `ci.yml` job `test` also runs on `crown-runner`
- `tests.yml` job `pytest` also runs on `crown-runner`

**Impact:** Single runner failure halts all CI activity for main branch merges.

---

## Gap 3: Duplicate Test Execution — `ci.yml` vs `tests.yml`

**Severity: MEDIUM**

Both `ci.yml` and `tests.yml` run pytest on the self-hosted runner on push/PR to main.
The `tests.yml` also triggers on `spine/**` branches (which `ci.yml` does not cover), but for
`main` the runs are fully duplicated:

- `ci.yml`: `test` job — push/PR to main, self-hosted runner
- `tests.yml`: `pytest` job — push/PR to main (and spine/**), self-hosted runner

Neither is configured as a required check, so both are advisory. The duplication wastes runner
minutes and can confuse the checks UI with two "passed/failed" signals for the same work.

---

## Gap 4: Dependency Security Workflows Overlap — `dependency-audit.yml` vs `dependency-scan.yml`

**Severity: MEDIUM**

Two workflows independently run Python dependency vulnerability checks:

| Workflow | Jobs | Tool |
|---|---|---|
| `dependency-audit.yml` | `backend-pip-audit`, `frontend-npm-audit` | pip-audit, npm audit |
| `dependency-scan.yml` | `python-safety`, `python-pip-audit`, `node-audit` | safety, pip-audit, node audit |

The `python-pip-audit` job in `dependency-scan.yml` runs the same tool as `dependency-audit.yml`.
The `python-safety` job uses `safety check` with `continue-on-error: true`, making it informational.

The overlap produces redundant CI runs on every push to main/develop without any additional
blocking value beyond what `dependency-audit.yml` already provides.

---

## Gap 5: `proof-ceremony.yml` — Required Check May Not Pass on Feature Branches

**Severity: MEDIUM**

`proof-ceremony.yml` is the only required check. It runs `proof-ceremony` on PRs to main.
The job uses `self-hosted, linux, x64, crown-runner` and depends on environment variables
including `CROWN_PASSWORD` secret.

If the `CROWN_PASSWORD` secret is missing or wrong, or if the self-hosted runner lacks
the required Postgres service, the required check will fail — blocking all merges.
There is no documented procedure for diagnosing or bypassing a stuck required check.

---

## Gap 6: Unfiltered Noisy Workflows

**Severity: LOW**

The following 7 workflows have no branch filter and run on **every** push and PR in the repository:

- `backend-shell-seeded-proof.yml`
- `backend-shell-write-and-lifecycle-proof.yml`
- `frontend-shell-certification.yml`
- `rc-gate.yml`
- `rc-runbook.yml`
- `rc-tier1-deployed-smoke.yml`
- `tests.yml`

This means every feature branch push incurs CI runs for RC-phase gates, shell certification,
and smoke tests. Runner minutes are consumed for pushes to `chore/**`, `docs/**`, and other
low-impact branches.

---

## Gap 7: Phase-Specific Workflows Still Active on main PRs

**Severity: LOW**

Four workflows representing completed project phases still run on every main PR:

| Workflow | Original Phase | Status |
|---|---|---|
| `phase1-gate.yml` | Phase 1 | Shipped |
| `phase3-demo-proof-pack.yml` | Phase 3 | Shipped |
| `phase3-runtime-proof.yml` | Phase 3 | Shipped |
| `phase4-gradebook-demo-proof.yml` | Phase 4 | Shipped |

These create stale check entries in the PR Checks UI. Users see passed checks for phases that
have no ongoing relevance, making it harder to quickly assess PR readiness.

---

## Gap 8: `rc-runbook.yml` Fires on All Branches Without Clear Purpose

**Severity: LOW**

`rc-runbook.yml` triggers on push/PR to all branches with no filter. Inspecting the workflow reveals
a `runbook` job. The purpose (documentation, script runner, or governance check) is unclear from
the file name alone. If it is just a utility workflow and not a gate, it should be dispatch-only.

---

## Gap 9: Open Copilot-Agent PRs Unreviewed

**Severity: LOW (process gap)**

Two PRs created by `copilot-swe-agent` (#635, #636) are open with `REVIEW_REQUIRED` status
and have never been reviewed by a human maintainer. Copilot-agent PRs can modify governance
files (branch protection, `.github/` configs) in ways that are hard to reverse.
No documented review SLA or owner assignment exists for agent-created PRs.

---

## Gap 10: `proof-ceremony` Context Name Collision Risk

**Severity: LOW**

The required check context name `proof-ceremony` is also emitted by `proof-ceremony.yml`'s
job named `proof-ceremony`. There is currently a single `proof-ceremony` source.

However, if any other workflow defines a job also named `proof-ceremony`, it would satisfy
the required check even if the canonical `proof-ceremony.yml` fails. This is a
context-collision risk if workflow names or job names are reorganized carelessly.

---

## Risk Register Summary

| Gap | Severity | Category |
|---|---|---|
| 1 — Single required check (advisory-only gates) | HIGH | Branch Protection |
| 2 — Required check on single self-hosted runner | HIGH | Infra Resilience |
| 3 — Duplicate pytest runs (ci.yml vs tests.yml) | MEDIUM | Workflow Sprawl |
| 4 — Overlapping dependency scan workflows | MEDIUM | Workflow Sprawl |
| 5 — Required proof-ceremony fragility | MEDIUM | CI Reliability |
| 6 — Unfiltered noisy workflows | LOW | Runner Cost / Noise |
| 7 — Stale phase-gate workflows on main PRs | LOW | PR UX |
| 8 — rc-runbook.yml purpose unclear | LOW | Workflow Hygiene |
| 9 — Unreviewed copilot-agent PRs | LOW | Process |
| 10 — proof-ceremony context collision risk | LOW | Security |
