> SUPERSEDED — HISTORICAL RECORD ONLY
>
> Archived: 2026-07-24
> Former path: `docs/repo-cleanup/CLEANUP_SUMMARY_PHASE2.md`
> Current governing authority: `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`
> Do not use as a current workflow, branch-protection, pull-request, release, or completion census.

# Cleanup Summary — Phase 2

Generated: Phase 2 cleanup pass
Branch: `chore/github-cleanup-phase2-workflows-prs`

---

## What Phase 2 Did

Phase 2 focused on three objectives:
1. **Workflow classification and reduction** — Survey all 54 workflows, label each, and safely remove the clear dead-weight
2. **Required checks governance documentation** — Map what checks actually block merges vs. what is advisory
3. **PR triage** — Assess all 16 open PRs and define a clear merge order

---

## Workflow Changes

### Removed (2 files)

| File | Reason |
|---|---|
| `.github/workflows/msgraph-smoke.yml` | Hard-coded to `stabilization-20260116-spine` — a dead branch from Jan 2026; no current gate value |
| `.github/workflows/demo-surface-gate.yml` | 18-line static PowerShell reachability check; superseded by `contract-gate.yml` |

### New Documentation Files

| File | Purpose |
|---|---|
| `docs/repo-cleanup/WORKFLOW_CLASSIFICATION_PHASE2.md` | Classification of all 54 workflows with KEEP/REMOVE/MERGE labels |
| `docs/repo-cleanup/WORKFLOW_TRIGGER_MAP_PHASE2.md` | Trigger, branch, environment, and gate-signal for every workflow |
| `docs/repo-cleanup/REQUIRED_CHECKS_MAP_PHASE2.md` | Branch protection status, required check mapping, and recommendations |
| `docs/repo-cleanup/PR_TRIAGE_PHASE2.md` | Triage of all 16 open PRs with priority merge order |
| `docs/repo-cleanup/GOVERNANCE_GAPS_PHASE2.md` | 10 identified governance gaps with severity ratings |
| `docs/repo-cleanup/CLEANUP_SUMMARY_PHASE2.md` | This file |
| `docs/repo-cleanup/PHASE3_RECOMMENDATIONS.md` | Concrete recommendations for Phase 3 |

---

## Workflow Inventory After Phase 2

| Classification | Count | Note |
|---|---|---|
| KEEP_CANONICAL | 26 | Active canonical workflows, preserved |
| KEEP_EXCEPTION | 9 | Legitimate one-offs, preserved |
| MERGE_INTO_CANONICAL | 4 | Listed for Phase 3 consolidation work |
| REMOVE_NOW | 2 | **Removed this phase** |
| REMOVE_LATER | 4 | Listed for Phase 3 when phases complete |
| REVIEW_REQUIRED | 9 | Human review required before action |
| **Total before** | **54** | |
| **Removed** | **2** | |
| **Total after** | **52** | |

---

## Key Findings Surfaced

1. **Only one required check exists on `main`** — `proof-ceremony` is the sole mandatory gate.
   All other gates (tests, migration lock, secrets, CodeQL) are advisory only.

2. **That required check runs on a single self-hosted runner** — `crown-runner` going offline
   halts all merges to main.

3. **Duplicate test runs** — `ci.yml` and `tests.yml` both run pytest on the same runner for
   the same branches; neither is a required check.

4. **7 workflows run on every push with no branch filter** — consuming runner minutes on
   irrelevant branches.

5. **16 open PRs, none with labels** — including 2 robotic (copilot-agent) PRs that have
   never been reviewed by a human.

---

## What Phase 2 Did NOT Do

- Did NOT modify any workflow content (only removed two dead files)
- Did NOT change `ruleset_main.json` or branch protection
- Did NOT merge or close any open PRs
- Did NOT touch the `REMOVE_LATER` or `MERGE_INTO_CANONICAL` workflows
- Did NOT alter any deployment or application configuration
