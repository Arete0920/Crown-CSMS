# CROWN Current Release Status

Date: 2026-05-30
Purpose: Single canonical authority for repository-level release posture.

## Canonical Authority

1. This file is the canonical repository-level release authority.
2. Current scorecard authority is `docs/release/CURRENT_RELEASE_SCORECARD_20260528.md`.
3. `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md` remains authoritative for its scoped release-governance slice only.
4. Operational/planning docs (including `PRIORITY_*_TO_GREEN` and execution-program plans) are non-authoritative unless explicitly designated here.

## Current Decision

Repository-wide decision (approved release slice): UNRESTRICTED GO.

Decision meaning:

- All P0 release-gate criteria are complete with linked evidence.
- Approved release slice is cleared for unrestricted GO.
- Entire platform roadmap scope remains not fully complete and is tracked separately in scorecard scope disclosures.

## Current Proof Snapshot (2026-05-30)

Backend proof status: PASS.

- `python backend/manage.py check` -> PASS.
- `pytest backend/applications/tests/test_admissions_endpoints.py -q -s` -> PASS (`24 passed`).
- `pytest backend/aftercare -q` -> PASS (`17 passed`).

Tenant/RBAC proof status: PASS.

- `pytest backend/tests/test_tenant_isolation.py -q` -> PASS (`7 passed`).

Frontend proof status: PASS.

- `npm run build` (frontend/dashboards) -> PASS.
- `npm run test -- --run` (frontend/dashboards) -> PASS (`37 passed` files, `341 passed` tests, `1 skipped` file).

Deploy SHA parity status: CLOSED (approved candidate SHA parity).

- Current local HEAD: `970fd2f55e77b62c30fe37059bd35fff756060cd`.
- Current `origin/main`: `d22fabb685f501928ecc39b8732e2b6ac86cea49`.
- Git parity delta (`origin/main...HEAD`): `52 39`.
- See `docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md` for captured deployed runtime SHA evidence and parity evaluation.
- Latest parity run artifact (md): `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_001336.md`
- Latest parity run artifact (json): `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_001336.json`
- Latest parity run was executed with explicit `DeployTargetSha` and `ApprovedReleaseSha` equal to `0b20581b4b4c0d03be9e9022893303804626d81f`.
- Result: `parity_status=CLOSED`, `matches_approved_release_sha=true`, `matches_local_head_sha=false`.

Protected-spine runtime/policy gate status: CLOSED (candidate-linked).

- Authoritative runtime packet stamp: `20260529_195922`.
- Runtime packet artifacts:
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_195922.json`
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_195922.md`
- Runtime packet result: `blocked=false`, `proof_runner_failures=0`, `product_test_failures=0`.
- Policy gate artifacts:
  - `docs/release/live-audit/protected-spine/protected_spine_authoritative_packet_policy_delta_20260529_2009.md`
  - `docs/release/live-audit/protected-spine/protected_spine_policy_gate_workflow_remediation_20260529_201142.md`
- Policy gate rerun results:
  - `Workflow policy checks passed.`
  - `Public surface policy gate PASSED`.
- Candidate SHA linkage:
  - parity packet references approved candidate SHA `0b20581b4b4c0d03be9e9022893303804626d81f` and is CLOSED (`deploy_sha_parity_20260530_001336`).
- Historical blockers are retained in dated live-audit artifacts and are superseded by the authoritative green packet and remediation reruns above.

Operational readiness status: UNRESTRICTED GO (approved release slice).

- Proven green for validated backend/frontend/tenant slices above.
- Final unrestricted-go decision packet is published and linked below.
- SOLOMON status is now ACTIVE, COMPLETED, and INTEGRATED for its approved scope under `docs/solomon/SOLOMON_ACTIVE_COMPLETION_INTEGRATION_20260529.md`.
- Fresh SOLOMON integration evidence: `132 passed in 86.57s` for onboarding + solomon backend slices via:
   - `python -u -m pytest backend/onboarding/tests/test_solomon_services.py backend/solomon/tests/test_adapters.py backend/solomon/tests/test_api.py backend/solomon/tests/test_governance_signals.py backend/solomon/tests/test_models.py backend/solomon/tests/test_review_queue.py backend/solomon/tests/test_scaffold.py -q -x --nomigrations`.
- This SOLOMON status transition remains scope-limited and does not change whole-platform roadmap completion posture.

Final unrestricted-go decision packet:

- `docs/release/FINAL_UNRESTRICTED_GO_DECISION_PACKET_20260530.md`

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

## Closure Record For Approved Release Slice Unrestricted GO

Execution board for these closure items:

- `docs/release/P0_EXECUTION_BOARD_20260528.md`

1. COMPLETE - Deploy target SHA parity evidence is published for approved release candidate commit `0b20581b4b4c0d03be9e9022893303804626d81f`.
   Current parity packet: `docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md`.
   Latest closure artifact: `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260530_001336.json`.
2. COMPLETE - Authority hygiene convergence is in place; legacy GO/PARTIAL/FAIL docs are marked historical/scope-limited and point to this canonical status source.
3. COMPLETE - Protected-spine runtime/policy gate is green on approved candidate SHA linkage.
4. COMPLETE - Canonical status and scorecard are synchronized for final gate decision.

## Language Guardrail

Allowed now:

- "Approved release slice is UNRESTRICTED GO; whole-platform roadmap scope remains separately tracked and not yet complete."

Not allowed now:

- "Repository is complete across all roadmap modules."
- "Whole-platform delivery scope is fully complete."
