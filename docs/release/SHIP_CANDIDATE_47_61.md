# SHIP CANDIDATE 47-61

> Superseded Authority Notice (2026-05-29)
>
> This document is historical and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-04-12T01:46:14

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_47_61_TO_GREEN.md
- docs/release/SCHEMA_W002_PROGRESS.md
- docs/openapi/crown-openapi.yaml

Exit checks:
- schema_w002_summary.json present
- schema_function_patch_report.json present
- schema_apiview_patch_report.json present
- route catalog present
- schema gate passes against SCHEMA_W002_BUDGET.json
- py_compile passes on changed files
- spectacular export writes crown-openapi.yaml
