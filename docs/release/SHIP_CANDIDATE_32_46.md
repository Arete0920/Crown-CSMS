# SHIP CANDIDATE 32Ã¢â‚¬â€œ46

Generated: 2026-04-11T22:16:22

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_32_46_TO_GREEN.md
- docs/release/RELEASE_ENV_MATRIX.md

Exit checks:
- release_patch_guard.json shows duplicate insertions normalized
- release_package_readiness.json present
- route_catalog.json present
- workflow_preflight.json green
- seed_fixture_parity.json green
- route contract pytest green
- auth golden path and accessibility smoke green
- compuwerx sandbox artifact present
