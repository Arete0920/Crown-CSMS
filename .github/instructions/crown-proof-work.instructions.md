---
applyTo: "**/*"
---
# CROWN Proof Work Instructions

Use these instructions for any module, wizard, dashboard, audit, or release-readiness task.

## First Action

Read current repo truth before planning:

1. `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
2. `audit-artifacts/module-completion/current/05_completion_scorecard.md`
3. the task-specific source files and tests
4. current branch and HEAD
5. open PRs or related merged PRs if the work depends on them

Do not use memory or stale chat history as current repo truth.

## Work Order Packet

Every implementation lane starts with a short packet:

```text
WORK_ORDER=<id>
BRANCH=<branch>
HEAD=<sha>
SCOPE=<one sentence>
NON_SCOPE=<explicit exclusions>
EXPECTED_FILES=<exact paths or directories>
VALIDATION=<commands that prove the work>
REVIEW=<independent review still required yes/no>
```

## Proof Ladder

Use this order:

1. Inventory existing implementation.
2. Inventory existing tests.
3. Run baseline checks.
4. Add the smallest missing proof needed for the blocker.
5. Run focused tests.
6. Run relevant broader checks.
7. Write evidence packet.
8. Commit only scoped files.
9. Open PR with bounded claims.
10. After merge, open separate canonical reconciliation PR if scorecard/matrix needs updating.

## Claim Rules

Allowed claim examples:

- `Module 025 proof test added and passing locally.`
- `PR updates canonical scorecard only; no code changes.`
- `Wizard contract coverage is validated; full functional flow remains not certified.`

Forbidden claim examples unless independently proven:

- `production ready`
- `release ready`
- `dashboard live-data complete`
- `all wizards complete`
- `independently approved`
- `full runtime certified`

## Stop Conditions

Stop and report instead of continuing when:

- working tree is dirty before a task;
- target file ownership is unclear;
- implementation is absent and the task was proof-only;
- tests require migrations not authorized by scope;
- protected areas are touched accidentally;
- branch head moved unexpectedly;
- checks are pending, failing, cancelled, stale, or action-required.

## Evidence Packet Naming

Use:

```text
audit-artifacts/<domain>/<work-order-id>/<timestamp>/
```

Include:

- `00_prechange_packet.txt`
- `01_inventory.txt`
- `02_changed_files.txt`
- `03_validation_output.txt`
- `04_git_diff_stat.txt`
- `05_decision.md`

## Review Rule

The repo owner cannot self-approve their own work. AI assistants cannot approve their own work. Mark final approval as `INDEPENDENT_REVIEW_REQUIRED` unless an appropriate independent reviewer has completed the review.
