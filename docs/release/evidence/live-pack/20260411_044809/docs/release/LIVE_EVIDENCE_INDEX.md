# LIVE EVIDENCE INDEX

Generated UTC: 2026-04-11T07:27:30.8844687Z

## Summary
- evidence count: 5
- action count: 3
- high priority actions: 2
- medium priority actions: 1
- local branches: 9
- workflows: 53
- backend apps: 91
- modules: 9

## Evidence Index
- repo_baseline | phase1_live_repo_baseline.json | status=READY | detail=Repo baseline generated
- release_truth | phase2_release_truth_mismatches.csv | status=ACTION | detail=Mismatch count: 1
- backend_verification | phase4_backend_verification_and_django_proof.json | status=READY | detail=manage_check_ok=True; showmigrations_ok=True
- module_proof | phase5_module_proof_matrix.csv | status=READY | detail=Module proof rows: 9
- branch_cleanup | phase3_branch_cleanup_candidates.csv | status=ACTION | detail=Delete candidate count: 66

## Source
- docs/release/live-audit/phase6/phase6_evidence_index.csv
