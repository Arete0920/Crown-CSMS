# CROWN Current Release Status

Date: 2026-05-29
Purpose: Single canonical authority for repository-level release posture.

## Canonical Authority

1. This file is the canonical repository-level release authority.
2. Current scorecard authority is `docs/release/CURRENT_RELEASE_SCORECARD_20260528.md`.
3. `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md` remains authoritative for its scoped release-governance slice only.
4. Operational/planning docs (including `PRIORITY_*_TO_GREEN` and execution-program plans) are non-authoritative unless explicitly designated here.

## Current Decision

Repository-wide decision: CONDITIONAL GO.

Decision meaning:

- Backend and frontend proof lanes are green for currently validated slices.
- Repository-wide unrestricted GA language is still blocked pending full authority hygiene convergence and deploy parity closure.

## Current Proof Snapshot (2026-05-29)

Backend proof status: PASS.

- `python backend/manage.py check` -> PASS.
- `pytest backend/applications/tests/test_admissions_endpoints.py -q -s` -> PASS (`24 passed`).
- `pytest backend/aftercare -q` -> PASS (`17 passed`).

Tenant/RBAC proof status: PASS.

- `pytest backend/tests/test_tenant_isolation.py -q` -> PASS (`7 passed`).

Frontend proof status: PASS.

- `npm run build` (frontend/dashboards) -> PASS.
- `npm run test -- --run` (frontend/dashboards) -> PASS (`37 passed` files, `341 passed` tests, `1 skipped` file).

Deploy SHA parity status: PARTIAL / NOT YET CLOSED.

- Current local HEAD: `6f2ee509e471d5c79b89194882c86206be186d0b`.
- Current `origin/main`: `d793766b6640d88a4bfdb87c999f429e06cd87ec`.
- Git parity delta (`origin/main...HEAD`): `50 11`.
- See `docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md` for captured deployed runtime SHA evidence and parity evaluation.
- Latest parity run artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_022049.json`.
- Current runtime/deploy target parity for latest local commit is not yet evidenced in this authority stack.

Operational readiness status: CONDITIONAL.

- Proven green for validated backend/frontend/tenant slices above.
- Still requires final reconciliation across legacy authority docs and explicit deploy parity proof to promote to unrestricted GO.
- SOLOMON strategy and execution artifacts are tracked separately under `docs/solomon/` and do not alter this release authority posture.

## Superseded Authority Labels

These files are historical and not controlling current repository-level release authority:

| File | Historical label | Superseded by |
| --- | --- | --- |
| `docs/release/LIVE_SHIP_DECISION.md` | SHIP | This file + `docs/release/CURRENT_RELEASE_SCORECARD_20260528.md` |
| `docs/release/LIVE_RELEASE_GATE_STATUS.md` | RELEASE_READY/PASS | This file + `docs/release/CURRENT_RELEASE_SCORECARD_20260528.md` |
| `docs/release/LIVE_FINAL_RELEASE_GATE.md` | historical gate snapshot | This file |
| `docs/release/LIVE_15_PHASE_COMPLETION.md` | historical SHIP snapshot | This file |
| `docs/release/FINAL_15_PHASE_VERIFICATION.md` | historical RELEASE_READY/SHIP verification snapshot | This file |
| `docs/release/SHIP_CANDIDATE.md` | historical SHIP candidate snapshot | This file |
| `docs/release/SHIP_CANDIDATE_32_46.md` | historical SHIP candidate snapshot | This file |
| `docs/release/SHIP_CANDIDATE_47_61.md` | historical SHIP candidate snapshot | This file |
| `docs/release/HANDOFF_2026-05-04.md` | historical NO-GO handoff snapshot | This file |
| `docs/release/INTEGRITY_HOLD_PROGRESS.md` | historical integrity-hold tracker snapshot | This file |
| `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md` | historical hosted-CI handoff snapshot | This file |
| `docs/release/LIVE_RUNTIME_GOVERNANCE_PR_SUMMARY_20260526.md` | historical PR summary snapshot | This file |
| `docs/release/LIVE_RELEASE_TRUTH.md` | historical truth packet | This file |
| `docs/KNOWN_LIMITATIONS.md` | historical NO-GO-era snapshot | This file |
| `docs/PUBLIC_REPO_STATUS.md` | historical PARTIAL status snapshot | This file |
| `docs/ACTUAL_STATUS_TODAY.md` | historical conditional-go hardening snapshot | This file |
| `docs/crown-master-binder/operations/JUDGMENT_DAY_CURRENT_SUMMARY.md` | historical operational NO-GO summary snapshot | This file |
| `docs/crown-master-binder/operations/CURRENT_EXECUTION_CONTROL_SUMMARY.md` | historical operational execution snapshot | This file |
| `docs/crown-master-binder/operations/BLOCKER_EXECUTION_BOARD.md` | historical operational blocker board snapshot | This file |
| `docs/crown-master-binder/operations/JUDGMENT_DAY_RUNBOOK.md` | historical operational gauntlet runbook snapshot | This file |
| `docs/crown-master-binder/operations/DEV5_QA_RELEASE_PROMPT.md` | historical operational QA/release prompt snapshot | This file |
| `docs/crown-master-binder/runbooks/CURRENT_AZURE_POST_DEPLOY_PACKET.md` | historical operational post-deploy packet snapshot | This file |
| `docs/status/PROJECT_COMPLETE.md` | historical feature-completion snapshot | This file |
| `docs/status/VERIFICATION_REPORT.md` | historical feature-verification snapshot | This file |
| `docs/completion/06-PRODUCTION-CERTIFICATION-CHECKLIST.md` | historical production certification checklist snapshot | This file |
| `docs/completion/07-INVESTOR-READINESS-CHECKLIST.md` | historical investor readiness checklist snapshot | This file |
| `docs/completion/02-MODULE-ACCEPTANCE-MATRIX.md` | historical module acceptance matrix snapshot | This file |
| `docs/audit/reports/EXEC_BOARD_REPORT.md` | historical executive board report snapshot | This file |
| `docs/DAY2_DASHBOARD_ENDPOINTS.md` | historical API operations reference snapshot | This file |
| `docs/admissions/ADMISSIONS_DELIVERY_PROCESS_PLAYBOOK_20260522.md` | historical admissions delivery playbook snapshot | This file |
| `docs/plan/RELEASE_SIGNOFF_CHECKLIST_RC.md` | historical RC signoff checklist snapshot | This file |

## Closure Required Before Unrestricted Repository-Wide GO

Execution board for these closure items:

- `docs/release/P0_EXECUTION_BOARD_20260528.md`

1. Publish explicit deploy target SHA parity evidence for the current head or approved release commit.
   Current parity packet: `docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md`.
   Runner (live mode): `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthUrl <health-url> -IntegrityUrl <integrity-url> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`.
   Runner (artifact mode): `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthJsonPath <path-to-02_health.json> -IntegrityJsonPath <path-to-02_integrity.json> -DeployTargetSha <deploy-run-sha> -ApprovedReleaseSha <approved-sha> -FailOnOpen`.
2. Complete authority hygiene convergence so legacy GO/PARTIAL/FAIL docs are non-ambiguous and clearly historical.
3. Keep this file and `docs/release/CURRENT_RELEASE_SCORECARD_20260528.md` synchronized for every material release-state change.

## Language Guardrail

Allowed now:

- "Validated slices are green; repository-level posture is CONDITIONAL GO pending final parity and authority convergence."

Not allowed now:

- "Repository is unrestricted GA-ready across all lanes."
- "All deployment targets are parity-verified for latest head."
