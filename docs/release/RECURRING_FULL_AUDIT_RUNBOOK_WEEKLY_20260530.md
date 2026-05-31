# Recurring Full Audit Runbook (Weekly)

Purpose: enforce weekly full-audit execution until all certification lanes remain continuously green.

## Cadence
- Frequency: weekly (once every 7 days).
- Trigger: scheduled runbook execution by release owner.
- Stop condition: explicit release authority closure note stating recurring audits no longer required.

## Required Commands
1. Candidate proof gate:
   - `pwsh -NoProfile -File scripts/release/verify_promotion_gate_critical_matrices.ps1`
2. Full 15-phase verification:
   - `pwsh -NoProfile -File scripts/release/verify_all_15_phases.ps1`
3. Final ship decision refresh:
   - `pwsh -NoProfile -File scripts/release/phase15_final_ship_decision_and_completion.ps1`

## Required Evidence Artifacts
- `docs/release/live-audit/phase15/phase15_final_ship_decision_and_completion.json`
- `docs/release/live-audit/phase15/phase15_final_ship_decision_and_completion.md`
- Latest `docs/release/live-audit/hosted-ci/hosted_ci_candidate_*.json`
- Latest `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_*.json`
- Latest `docs/release/live-audit/protected-spine/protected_spine_candidate_sha_packet_*.json`

## Fail-Closed Rules
- If any required command fails, release remains blocked.
- If hosted CI snapshot is missing or has zero passing candidate-bound runs, release remains blocked.
- If deploy parity is open, release remains blocked.
- If protected-spine packet is not passing, release remains blocked.
