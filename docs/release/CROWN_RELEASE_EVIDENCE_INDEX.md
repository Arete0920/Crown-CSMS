# CROWN Release Evidence Index

Status: HOLD / evidence consolidation in progress
Updated: 2026-06-30

## Purpose

This index tracks CROWN release evidence by source, SHA, artifact, and disposition. It is intended to prevent confusion between scaffold work, CI artifacts, sandbox proof, investor-preview proof, and release authorization.

## Current state

| Area | State | Tracker |
|---|---|---|
| Production certification crawler scaffold | Merged | PR #1215 |
| Production certification evidence workflow | Merged | PR #1218 |
| Main-branch crawler artifact verification | Pending | Issue #1217 |
| Durable evidence ledger update | Pending | This file |
| Release authority reconciliation | Pending | Future tracker |
| Same-SHA live proof | Pending | Future tracker |
| Role-based sandbox launch paths | Pending | Future tracker |
| Named cohort/scope approval | Pending | Future tracker |

## Issue #1217 closure criteria

Issue #1217 can close only after the main-branch Production Certification Evidence artifact is verified and recorded. The expected files are:

- `certification-summary.md`
- `certification-matrix.json`
- `route-results.csv`

## Artifact ledger placeholder

```text
main_sha:
workflow_name:
workflow_run_id:
artifact_name:
artifact_verified_at:
evidence_files_present:
known_limitations:
release_disposition:
```
