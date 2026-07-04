# Superseded production school-id blocker note

Status: **SUPERSEDED / HISTORICAL**.

This artifact is retained only to document an earlier production-runtime finding. It is **not current release guidance** and must not be used as an instruction to certify the Heritage sandbox/demo lane against the old `GP School` production row.

## Superseded finding

Earlier production database inspection found that the production database reachable through `crown-api-prod` contained a `core_school` row named `GP School` and no row named `Heritage Christian Academy`.

That finding explained why a strict production-school certification path could not honestly use the Heritage school name unless the Azure/database seed state was corrected or the certification lane was explicitly switched to sandbox/demo authority.

## Current PR #1237 direction

PR #1237 no longer treats the `GP School` row as the active certification target for the investor/demo sandbox lane.

The active same-SHA certification configuration now uses the governed Heritage sandbox/demo path:

```text
CROWN_CERTIFICATION_TENANT_MODE=sandbox
CROWN_DEMO_SCHOOL_ID=19801b59-8c05-4c84-9312-5d792e4e839d
CROWN_LIVE_SCHOOL_LABEL=Heritage Christian Academy
CROWN_LIVE_SANDBOX_INVITE_ID=<GitHub secret or variable>
```

The active tenant list is narrowed to the `heritage` tenant with `schoolKey=heritage-core`.

## Do not use this old command

The earlier command below is intentionally invalidated for the current Heritage sandbox/demo certification lane and must not be followed as current guidance:

```bash
gh variable set CROWN_LIVE_SCHOOL_ID --repo tcmegahan/Crown2026 --body "156b351b-1d06-40cd-b36b-2c08150b69af"
```

Using that value would certify against the old production `GP School` row, not the current Heritage sandbox/demo scope.

## Current proof standard

The GP-school mismatch is considered resolved only when the current same-SHA Production Certification Evidence workflow passes against the active PR head and the resulting artifact shows the `heritage` tenant path without `GP School` leakage.

Until that passes, release posture remains:

```text
NO-GO / HOLD
```
