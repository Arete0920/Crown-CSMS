# SHIP CANDIDATE 47-61

Generated: 2026-04-12T01:19:59

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
