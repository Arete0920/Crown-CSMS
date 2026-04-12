# SHIP CANDIDATE

Generated: 2026-04-11T21:53:08

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
