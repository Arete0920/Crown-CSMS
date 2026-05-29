# CROWN Judgment Day Release Gauntlet Runbook

> Authority Scope Notice (2026-05-29)
>
> This file is an operational runbook and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-05-01T13:54:10

## Purpose
This is the harshest release readiness gate for CROWN. It is designed to kill weak release candidates before schools, sandbox testers, or customers experience failures.

## Automatic NO-GO Conditions
Any one of these is a production NO-GO:
- tenant leak
- role bypass
- real secret exposed
- broken login
- broken billing reconciliation
- frontend unavailable
- backend unavailable
- backend live SHA mismatch
- frontend build SHA mismatch
- deployment workflow failed
- database migration corruption
- backup cannot restore
- unresolved P0 blocker
- unexecuted tenant/RBAC runtime proof

## Scoring
Total score: 1000 points
- Repo hygiene: 50
- Local validation: 100
- Security secret scan: 100
- Tenant isolation static scan: 75
- RBAC static scan: 50
- UI/routes/dashboard/wizard static scan: 100
- Deployment integrity read-only probe: 100
- Browser smoke: 100
- Safe load probe: 50
- Required runtime proof matrix: 175
- Evidence/operations completeness: 100

## Score Bands
- 950-1000: Production GO candidate
- 900-949: Release candidate, minor fixes only
- 800-899: Strong but not production-final
- 700-799: Major hardening required
- Below 700: Not release-ready

## Evidence Folder
C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_131601

## Required Manual Proof Matrix
C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_131601\60_required_runtime_proof_matrix.csv
