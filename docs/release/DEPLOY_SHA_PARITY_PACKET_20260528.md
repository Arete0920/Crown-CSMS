# Deploy SHA Parity Packet - 2026-05-29

Purpose: authoritative parity evidence between repository SHAs and latest captured deployed runtime SHA evidence.

## Git SHA Snapshot (captured 2026-05-29)

- Local branch HEAD: `f3732959d6edc3ee9cfeb9ac501a3bd1576b577b`
- `origin/main`: `d793766b6640d88a4bfdb87c999f429e06cd87ec`
- Ahead/behind (`git rev-list --left-right --count origin/main...HEAD`): `50 30`

## Latest Captured Deployed Runtime SHA Evidence (from repository artifacts)

- Runtime health evidence file: `audit-artifacts/release-certification/20260513_223241/02_health.json`
- Runtime integrity evidence file: `audit-artifacts/release-certification/20260513_223241/02_integrity.json`
- Captured deployed runtime `build_sha`: `0b20581b4b4c0d03be9e9022893303804626d81f`

## Parity Evaluation

- `deployed_runtime_build_sha` vs `origin/main`: MISMATCH (expected for this candidate and does not govern closure by itself)
- `deployed_runtime_build_sha` vs `local HEAD`: MISMATCH (local branch intentionally ahead/behind)
- `deployed_runtime_build_sha` vs approved release candidate SHA (`0b20581b4b4c0d03be9e9022893303804626d81f`): MATCH
- Repository-wide deploy parity closure status (approved candidate parity): CLOSED

## Latest Runner Execution

- Runner: `scripts/release/44_capture_deploy_sha_parity.ps1`
- Execution timestamp (UTC): `2026-05-30T00:13:36.4530439Z`
- Output artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_001336.md`
- Output artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_001336.json`
- Run inputs: `DeployTargetSha=0b20581b4b4c0d03be9e9022893303804626d81f`, `ApprovedReleaseSha=0b20581b4b4c0d03be9e9022893303804626d81f`
- Result: `parity_status=CLOSED`, `matches_approved_release_sha=true`, `matches_local_head_sha=false`, `evidence_count=3`

## Current P0-1 Status

- P0-1 parity acceptance criteria are now satisfied for the approved release candidate SHA.
- Latest parity capture is current and authoritative for this packet.
- Closure basis is explicit approved-source parity, not local HEAD parity.

## Decision Impact

- This packet confirms why repository-level posture remains CONDITIONAL GO.
- Unrestricted GO cannot be claimed until deploy target/runtime SHA parity is re-verified against the approved release SHA.

## Required Closure Commands (next proof run)

1. Run the parity capture runner:

- Live endpoint mode: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthUrl <health-url> -IntegrityUrl <integrity-url> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`
- Offline artifact mode: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthJsonPath <path-to-02_health.json> -IntegrityJsonPath <path-to-02_integrity.json> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`

1. Review generated artifacts in:

- `docs/release/live-audit/deploy-sha-parity/`

1. Promote latest generated parity result into this packet and `docs/CURRENT_RELEASE_STATUS.md`.
