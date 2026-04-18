# LIVE FINAL RELEASE GATE

Generated UTC: 2026-04-11T08:25:33.7964897Z

## Overall
- overall score: 87
- overall status: NEAR_READY
- checklist percent: 78
- high priority actions: 2
- medium priority actions: 1

## Gate Rows
- release_truth | score=85 | status=PASS
- backend_verification | score=100 | status=PASS
- module_proof | score=93 | status=PASS
- runtime_api | score=50 | status=ACTION
- frontend_dashboard | score=80 | status=PASS
- reporting_export | score=100 | status=PASS
- action_register | score=76 | status=PASS

## High Priority Blockers
- refresh_release_truth_docs | owner=release | evidence=docs/release/live-audit/phase2/phase2_release_truth_mismatches.csv
- module_proof_release_controls | owner=module_owner | evidence=docs/release/live-audit/phase5/phase5_module_proof_matrix.csv

## Source
- docs/release/LIVE_RELEASE_GATE_STATUS.md
- docs/release/LIVE_ACTION_REGISTER.md
