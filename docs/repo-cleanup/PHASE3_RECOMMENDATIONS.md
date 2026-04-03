# Phase 3 Recommendations

Generated: Phase 2 cleanup pass output  
Branch: `chore/github-cleanup-phase2-workflows-prs`

These recommendations are direct outputs of the Phase 2 governance audit.
They are **recommendations only** — no changes have been made.
Each item should be executed as a deliberate decision, in the order given.

---

## Track 1: Harden Branch Protection (Highest Priority)

### 1a. Add Required Status Checks to `ruleset_main.json`

The current ruleset has one required check: `proof-ceremony`. Add the following as required
checks in priority order:

**Must-add (Tier 1):**
```json
{ "context": "backend-gate" },
{ "context": "test" },
{ "context": "migration-lock-gate / gate" },
{ "context": "secret-scan" },
{ "context": "contract-gate" }
```

**Should-add (Tier 2):**
```json
{ "context": "routes-gate" },
{ "context": "spine-audit" },
{ "context": "backend-pip-audit" },
{ "context": "frontend-npm-audit" },
{ "context": "dependency-review" }
```

**Reference:** `docs/repo-cleanup/REQUIRED_CHECKS_MAP_PHASE2.md` — full context name mapping.

### 1b. Verify `proof-ceremony` Runner Resilience

Add `ubuntu-latest` fallback or a runner liveness probe to ensure the sole required check
does not block all merges when `crown-runner` is offline. Options:
- Add a GitHub-hosted runner fallback in `proof-ceremony.yml`
- Document runner restart runbook prominently in `docs/ops/`

---

## Track 2: Workflow Consolidation (Medium Priority)

### 2a. Remove Phase-Specific Workflows (REMOVE_LATER)

Once the corresponding phases are confirmed merged to main:

```bash
git rm .github/workflows/phase1-gate.yml
git rm .github/workflows/phase3-demo-proof-pack.yml
git rm .github/workflows/phase3-runtime-proof.yml
git rm .github/workflows/phase4-gradebook-demo-proof.yml
```

**Condition:** Verify phase contracts are in main before deleting. These run as non-required
checks on main PRs, so their removal will not change merge behavior.

### 2b. Merge Duplicate Workflows (MERGE_INTO_CANONICAL)

| Source | Target | Action |
|---|---|---|
| `tests.yml` | `ci.yml` | Delete `tests.yml`; `ci.yml` already covers main+tests on self-hosted runner |
| `ops-reset-dev.yml` | `demo-reset.yml` | Add optional `target` input to `demo-reset.yml`; delete `ops-reset-dev.yml` |
| `demo-reset-smoke.yml` | `demo-reset.yml` | Add optional `run_smoke` boolean input to `demo-reset.yml` |
| `dependency-scan.yml` | `dependency-audit.yml` | Add `safety` check as optional step; remove `continue-on-error`; delete `dependency-scan.yml` |

### 2c. Fix Unfiltered Workflows (NOISE REDUCTION)

Add branch filters to these 7 workflows to stop them from running on every feature branch push:

- `backend-shell-seeded-proof.yml` → add `branches: [main, "release/**"]`
- `backend-shell-write-and-lifecycle-proof.yml` → add `branches: [main, "release/**"]`
- `frontend-shell-certification.yml` → add `branches: [main, "release/**"]`
- `rc-gate.yml` → add `branches: ["rc/**", main]`
- `rc-runbook.yml` → convert to `workflow_dispatch`-only (remove auto triggers)
- `rc-tier1-deployed-smoke.yml` → convert to `workflow_dispatch`-only
- `tests.yml` → (remove entirely; covered by Track 2b above)

---

## Track 3: PR Queue Cleanup (Medium Priority)

### 3a. Close Stale PR

Close **PR #641** (`release-readiness/chore-cleanup-root`).
Superseded by `chore/github-cleanup-phase1` commit `e26a77fb`.

### 3b. Merge Release-Readiness PRs in Sequence

Merge in this order to minimize conflict risk:
1. #637 — prod-health-watch heredoc fix
2. #638 — CodeQL blocking
3. #639 — dependency-audit workflow
4. #640 — governance docs package

### 3c. Assign Reviewers to Feature PRs

Assign human reviewers to:
- #629 (financial aid complete)
- #630 (billing/CompuWerx)
- #632 (parent portal consolidation)

### 3d. Manually Review Copilot-Agent PRs

Review line-by-line before taking any action:
- #635 (branch protection enforcement)
- #636 (bulk file removal)

### 3e. Rebase and Re-Test

After the release-readiness PRs merge, rebase:
- #625 (security headers)
- #626 (audit roadmap)
- #628 (little lambs)
- #618 (deploy test contracts)

### 3f. Resolve Merge Conflicts

- #611 (security feature gate guard)
- #600 (deploy trigger hardening)

---

## Track 4: Process Governance (Low Priority)

### 4a. Add PR Labels

Create and apply labels to all open PRs:
- `feature`, `ci/cd`, `security`, `docs`, `chore`, `needs-rebase`, `needs-review`

### 4b. Document Runner Restart Runbook

Create `docs/ops/RUNNER_RESTART_RUNBOOK.md` explaining how to restart `crown-runner`
and how to diagnose when `proof-ceremony` is stuck due to runner offline.

### 4c. Establish Review SLA for Agent PRs

Document in `CONTRIBUTING.md` or `docs/ops/`:
- Copilot-agent PRs require human review within 48 hours
- No agent PR may modify `.github/` governance files without two human approvals

### 4d. Review `REVIEW_REQUIRED` Workflows

9 workflows were flagged for human review before any action. Each needs an owner to decide:

| Workflow | Question |
|---|---|
| `backend-shell-seeded-proof.yml` | Superseded by `ci.yml`? Or distinct seeded-state value? |
| `backend-shell-write-and-lifecycle-proof.yml` | Same question |
| `deploy-integrity-proof.yml` | Overlaps `proof-ceremony-after-prod.yml`? |
| `gradebookro-ui-gate.yml` | Active gate or superseded by `proof-gradebook.yml`? |
| `prod-integrity-proof.yml` | Overlaps `proof-ceremony-after-prod.yml`? |
| `rc-runbook.yml` | What does the `runbook` job actually do? |
| `system-health.yml` | Overlaps `prod-health-watch.yml`? Or distinct check target? |
| `ui-proof-gate.yml` | Overlaps `ui-proof-gates.yml`? |

---

## Phase 3 Deliverable Checklist

- [ ] `ruleset_main.json` updated with Tier 1 required checks
- [ ] Runner resilience plan documented or implemented
- [ ] `phase1-gate.yml` removed (after phase 1 confirmed in main)
- [ ] `phase3-*` workflows removed (after phase 3 confirmed in main)
- [ ] `phase4-gradebook-demo-proof.yml` removed (after phase 4 confirmed)
- [ ] `tests.yml` merged into `ci.yml` and removed
- [ ] Unfiltered workflows have branch filters added
- [ ] PR #641 closed
- [ ] PRs #637, #638, #639, #640 merged
- [ ] REVIEW_REQUIRED workflow decisions recorded
- [ ] Copilot-agent PRs reviewed or closed
