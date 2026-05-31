# SHIP CANDIDATE

> Superseded Authority Notice (2026-05-29)
>
> This document is historical and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-04-12T01:10:29

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_16_31_TO_GREEN.md

Exit criteria:
- pytest phase2 green
- frontend smoke green
- mock_seed_scan shows 0 hits or all hits intentionally remediated
- release-closeout status endpoint green
- transcript / report-card / discipline / board PDF endpoints return 200
