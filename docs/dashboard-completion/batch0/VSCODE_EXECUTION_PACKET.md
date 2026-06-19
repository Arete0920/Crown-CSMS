# Batch 0 VS Code Execution Packet

Status: execution packet only. This file does not certify dashboards.

## Branch

`feat/dashboard-batch0-evidence-prep-20260619`

## Dashboards

- `dashboard-certification-center`
- `release-reliability`
- `compliance-audit`

## Required local checks

Run from a clean worktree.

1. Confirm branch and clean status.
2. Inspect dashboard route/component/API references.
3. Capture render proof for each Batch 0 dashboard.
4. Capture permission proof for allowed and denied roles.
5. Capture tenant isolation proof.
6. Capture screenshot or trace artifact.
7. Capture redacted payload sample.
8. Record independent review status as pending unless a separate reviewer has reviewed it.

## Stop rules

Stop if any check requires unrelated backend changes, release status changes, matrix promotion, or self-approval.

## Expected status after this packet

Dashboards may move from unprepared to evidence-in-progress, but they remain not certified until full proof and independent review exist.
