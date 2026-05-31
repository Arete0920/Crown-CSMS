# Release Authority Precedence Table

Date: 2026-05-30

## Scope

This table defines which documents are allowed to make controlling go/no-go release authority statements.

## Precedence

| Rank | File | Scope | Controlling Authority |
| --- | --- | --- | --- |
| 1 | docs/CURRENT_RELEASE_STATUS.md | Repository-level current posture | YES |
| 2 | docs/release/CURRENT_RELEASE_SCORECARD_20260528.md | Canonical scorecard decision | YES |
| 3 | docs/release/P0_EXECUTION_BOARD_20260528.md | P0 baseline language only | LIMITED (must match rank 1 and 2) |
| 4 | docs/release/FULL_COMPLETION_EXECUTION_BOARD_20260530.md | Execution tracking and evidence index | NO |
| 5 | docs/release/*.md (all other files) | Historical, analysis, planning, and proof packs | NO |

## Enforcement Rules

1. Only rank 1 and rank 2 may authoritatively declare go/no-go posture.
2. Rank 3 may only mirror canonical decision language, never diverge.
3. Rank 4 and rank 5 files must not declare controlling go/no-go authority.
4. Historical files must include superseded authority notices where applicable.

## Automation

- scripts/release/verify_authority_decision_sync.ps1
- scripts/release/scan_release_claim_wording.ps1
- scripts/release/verify_release_claim_branch_sha.ps1
- scripts/release/verify_superseded_authority_watermarks.ps1
- scripts/release/verify_noncanonical_authority_claims.ps1
