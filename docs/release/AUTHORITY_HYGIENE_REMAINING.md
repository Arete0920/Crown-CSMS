# Authority Hygiene Remaining

Generated: 2026-05-29
Last Updated: 2026-05-29 (post scope-notice pass)
Purpose: explicit residual queue after superseded/scope-notice hardening.

## Baseline Rules

- Repository-level controlling authority is only:
  - docs/CURRENT_RELEASE_STATUS.md
  - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md
- All other status-like docs are either:
  - historical snapshots (Superseded Authority Notice), or
  - operational artifacts (Authority Scope Notice).

## Current Residual Set (Review Required)

These files are remaining low-ambiguity operational/policy artifacts that may mention release process language but are not currently acting as release authority.

| File | Recommended Action | Rationale |
| --- | --- | --- |
| docs/crown-master-binder/operations/06_Communication_Rules.md (path variant under Crown_Master_Binder) | leave-as-operational (optional scope-notice) | Governance/communication rulebook, not a release decision source |
| docs/Crown_Master_Binder/05_Runbooks_and_Checklists/02_Build_Sequence.md | leave-as-operational (optional scope-notice) | Build procedure runbook |
| docs/Crown_Master_Binder/05_Runbooks_and_Checklists/03_Release_Runbook.md | leave-as-operational (optional scope-notice) | Operational release process, not decision authority |
| docs/Crown_Master_Binder/05_Runbooks_and_Checklists/12_Phase_7_Hardening_Integration_and_Release_Readiness.md | leave-as-operational (optional scope-notice) | Phase runbook snapshot |
| docs/Crown_Master_Binder/05_Runbooks_and_Checklists/13_Completion_Gate_Master_Checklist.md | leave-as-operational (optional scope-notice) | Checklist artifact, non-authoritative |
| docs/governance/SOLO_MAINTAINER_BRANCH_PROTECTION_POLICY.md | leave-as-policy | Policy document; not a release status source |
| docs/release/crown-universal-proof/CROWN_12x12_UNIVERSAL_PROOF_MATRIX.md | leave-as-operational | Evidence matrix artifact |

## Completed In This Pass

- docs/DAY2_DASHBOARD_ENDPOINTS.md (Authority Scope Notice added)
- docs/admissions/ADMISSIONS_DELIVERY_PROCESS_PLAYBOOK_20260522.md (Authority Scope Notice added)
- docs/completion/02-MODULE-ACCEPTANCE-MATRIX.md (Authority Scope Notice added)
- docs/plan/RELEASE_SIGNOFF_CHECKLIST_RC.md (Authority Scope Notice added)
- docs/release/MODULE_INVENTORY.md (Authority Scope Notice added)
- docs/release/CROWN_FINANCE_TUITION_SUPERIORITY_EXECUTION_PROGRAM_20260528.md (Authority Scope Notice added)
- docs/release/INVESTOR_DEMO_RUNBOOK.md (Authority Scope Notice added)
- docs/release/NEXT_ACTION_SUMMARY.md (Authority Scope Notice added)
- docs/release/CROWN_MASTER_PRIORITY_LADDER_DASHBOARD.md (Authority Scope Notice added)
- docs/release/PRODUCTION_RELEASE_TOP_10_REMAINING_TASKS_20260528.md (Authority Scope Notice added)
- docs/release/CROWN_MASTER_BINDER.md (Authority Scope Notice added)

## Files Intentionally Unmarked (Current Authority Artifacts)

- docs/CURRENT_RELEASE_STATUS.md
- docs/release/CURRENT_RELEASE_SCORECARD_20260528.md
- docs/release/DEPLOY_SHA_PARITY_PACKET_20260528.md

## Recommended Next Pass

1. Leave procedural/policy/runbook artifacts unchanged unless they begin being referenced as release authority in user-facing summaries.
2. Re-run residual scan after any new status/report document is introduced.
3. Close this file when residual set is explicitly accepted as non-authoritative operational/policy backlog.
