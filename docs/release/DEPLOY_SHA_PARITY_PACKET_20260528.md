# Deploy SHA Parity Packet - 2026-05-28

Purpose: authoritative parity evidence between repository SHAs and latest captured deployed runtime SHA evidence.

## Git SHA Snapshot (captured 2026-05-28)

- Local branch HEAD: `9920f22b06ed9d60cf8966703552b3ce726cb845`
- `origin/main`: `d793766b6640d88a4bfdb87c999f429e06cd87ec`
- Ahead/behind (`git rev-list --left-right --count origin/main...HEAD`): `50 0`

## Latest Captured Deployed Runtime SHA Evidence (from repository artifacts)

- Runtime health evidence file: `audit-artifacts/release-certification/20260513_223241/02_health.json`
- Runtime integrity evidence file: `audit-artifacts/release-certification/20260513_223241/02_integrity.json`
- Captured deployed runtime `build_sha`: `0b20581b4b4c0d03be9e9022893303804626d81f`
- Captured deploy workflow metadata in evidence body:
  - `deploy_workflow`: `Production Deploy`
  - `deploy_run_id`: `25741580560`
  - `prod_deploy_tag`: `prod-deploy-20260512`

## Parity Evaluation

- `deployed_runtime_build_sha` vs `origin/main`: MISMATCH (parity not proven)
- `deployed_runtime_build_sha` vs `local HEAD`: MISMATCH (parity not proven)
- Repository-wide deploy parity closure status: OPEN

## Latest Runner Execution

- Runner: `scripts/release/44_capture_deploy_sha_parity.ps1`
- Execution timestamp (UTC): `2026-05-29T01:11:48.6895887Z`
- Output artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_011148.md`
- Output artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_011148.json`
- Result: `parity_status=OPEN`, `matches_approved_release_sha=false`, `matches_local_head_sha=false`, `evidence_count=3`

## Decision Impact

- This packet confirms why repository-level posture remains CONDITIONAL GO.
- Unrestricted GO cannot be claimed until deploy target/runtime SHA parity is re-verified against the approved release SHA.

## Required Closure Commands (next proof run)

1. Run the parity capture runner:
  - Live endpoint mode: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthUrl <health-url> -IntegrityUrl <integrity-url> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`
  - Offline artifact mode: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthJsonPath <path-to-02_health.json> -IntegrityJsonPath <path-to-02_integrity.json> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`
2. Review generated artifacts in:
  - `docs/release/live-audit/deploy-sha-parity/`
3. Promote latest generated parity result into this packet and `docs/CURRENT_RELEASE_STATUS.md`.
