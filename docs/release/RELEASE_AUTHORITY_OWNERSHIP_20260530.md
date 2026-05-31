# Release Authority Ownership Map

Date: 2026-05-30
Purpose: explicit ownership metadata for all controlling release authority artifacts.

| Artifact | Owner | Backup Owner | Review Cadence | Change Approval |
| --- | --- | --- | --- | --- |
| docs/CURRENT_RELEASE_STATUS.md | Solo release owner | Solo engineering owner | Per material release-state change | Release owner signoff |
| docs/release/CURRENT_RELEASE_SCORECARD_20260528.md | Solo release owner | Solo QA owner | Per material release-state change | Release owner signoff |
| docs/release/P0_EXECUTION_BOARD_20260528.md | Solo release owner | Solo operations owner | Daily while P0 lane active | Release owner signoff |
| docs/release/RELEASE_AUTHORITY_PRECEDENCE_TABLE_20260530.md | Solo release owner | Solo operations owner | Weekly | Release owner signoff |
| docs/release/FULL_COMPLETION_EXECUTION_BOARD_20260530.md | Solo release owner | Solo QA owner | Daily while closure program active | Release owner signoff |
| scripts/release/verify_authority_decision_sync.ps1 | Solo engineering owner | Solo release owner | On validator updates | Release owner signoff |
| scripts/release/verify_authority_files_on_main.ps1 | Solo engineering owner | Solo release owner | On validator updates | Release owner signoff |
| scripts/release/verify_release_claim_branch_sha.ps1 | Solo engineering owner | Solo release owner | On validator updates | Release owner signoff |
| scripts/release/verify_noncanonical_authority_claims.ps1 | Solo engineering owner | Solo release owner | On validator updates | Release owner signoff |
| scripts/release/verify_canonical_status_metadata.ps1 | Solo engineering owner | Solo release owner | On validator updates | Release owner signoff |

Integrity notes:
- Owner values are role-oriented and stable for solo execution mode.
- Any ownership transfer requires a change-control log entry in docs/release/RELEASE_AUTHORITY_CHANGE_CONTROL_LOG_20260530.md.
