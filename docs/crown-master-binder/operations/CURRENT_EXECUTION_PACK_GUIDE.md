# CROWN Execution Pack Guide

Generated: 2026-05-01T02:33:33

## Current State

- This is GO for non-Azure execution.
- This is NOT production GO.
- Production remains blocked until Azure post-deploy proof, runtime proof, UI proof, and final Judgment Day rerun all pass.

## Open In This Order

1. 99_EXECUTION_CONTROL_SUMMARY.md
2. 05_EXECUTION_STATUS_BOARD.csv
3. DEV125_TENANT_RUNTIME_PACKET.md
4. DEV15_RBAC_RUNTIME_PACKET.md
5. DEV23_WORKFLOW_RUNTIME_PACKET.md
6. DEV4_UI_POLISH_PACKET.md
7. AZURE_POST_DEPLOY_PACKET.md
8. QA_FINAL_RERUN_PACKET.md

## Team Packet Map

| Team | Packet | Evidence Sheet |
|---|---|---|
| Dev 1 / Dev 2 / Dev 5 | DEV125_TENANT_RUNTIME_PACKET.md | 10_TENANT_RUNTIME_EVIDENCE.csv |
| Dev 1 / Dev 5 | DEV15_RBAC_RUNTIME_PACKET.md | 11_RBAC_RUNTIME_EVIDENCE.csv |
| Dev 2 / Dev 3 | DEV23_WORKFLOW_RUNTIME_PACKET.md | 12_WORKFLOW_RUNTIME_EVIDENCE.csv |
| Dev 4 | DEV4_UI_POLISH_PACKET.md | 20_UI_DASHBOARD_ROUTE_EVIDENCE.csv and 30_UI_CLEANUP_BOARD.csv |
| Azure / DevOps | AZURE_POST_DEPLOY_PACKET.md | audit-artifacts/post-azure-live-proof/<timestamp>/POST_AZURE_LIVE_PROOF.csv |
| Dev 5 / QA Release | QA_FINAL_RERUN_PACKET.md | Fresh Judgment Day rerun output |

## Generated Proof Boards

- 21_RBAC_PROOF_MATRIX.csv
- 22_RUNTIME_PROOF_MATRIX.csv
- 23_TENANT_PROOF_MATRIX.csv
- 30_UI_CLEANUP_BOARD.csv

## Capture Scripts

- scripts/execution/250_capture_runtime_proof.ps1
- scripts/execution/260_capture_ui_cleanup.ps1
- scripts/execution/270_post_azure_live_proof.ps1
