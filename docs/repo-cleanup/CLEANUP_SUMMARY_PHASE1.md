# Cleanup Summary Phase 1

## Scope

Phase 1 performed safe repository root reorganization with inventory-first discipline.
No workflow files were deleted in this pass.
No runtime application code was modified for cleanup.

## What Moved

### moved to `docs/audit/`

- `DEEP_DIVE_ANALYSIS.md`
- `_CLEAN_PREVIEW.txt`
- `_audit_test_run.txt`
- `_required_check_mapping.json`
- `_required_check_mapping_after.json`
- `_required_check_mapping_clean.json`
- `branch_protection.json`
- `hex_audit.txt`
- `hex_audit_output.txt`

### moved to `docs/demo/`

- `CONTINGENCY_CURRICULUM_DEMO.md`
- `DEMO_CHECKLIST.md`
- `DEMO_FLOW.md`
- `DEMO_SCRIPT.md`
- `DEMO_SCRIPT_CURRICULUM_SEGMENT.md`
- `DEMO_SURFACE_WIRING_SPEC.md`
- `PRE_DEMO_VERIFICATION.md`
- `PROOF_ACADEMICS_ROSTER.md`
- `PROOF_DEMO_SMOKE_FEB16.md`
- `PROOF_DEV_SMOKE_SUCCESS_20260209.md`
- `PROOF_UI_ACADEMICS_ROSTER_DRAWER.md`
- `README_CURRICULUM_DEMO_PREP.md`
- `RUNSHEET_CURRICULUM_DEMO.md`

### moved to `docs/ops/`

- `CI_USER_PROVISIONING.md`
- `COPILOT_GUARDRAILS.md`
- `COPILOT_TASK_PROTOCOL.md`
- `INTEGRATION_GUIDE.md`
- `README_DIRECTOR_ACTIONS.md`
- `README_GOLDEN_PATH.md`
- `ROTATE_SECRETS.md`

### moved to `docs/status/`

- `DELIVERABLES.md`
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `MASTER_SUMMARY.md`
- `PROJECT_COMPLETE.md`
- `RELEASE_PACKET_v0.4.0-rc1.commands.txt`
- `RELEASE_PACKET_v0.4.0-rc1.md`
- `VERIFICATION_REPORT.md`

### moved to `docs/canons/`, `docs/specs/`, `docs/maps/`

- Canons: `CROWN_DEV_CANON.md`, `SPINE_DEFINITION_OF_DONE.md`, `TENANT_ISOLATION_CANON.md`
- Specs: `DASHBOARDS_PHASE_A_SPEC.md`, `DIRECTOR_FRAMEWORK_CONTRACT.md`, `GRADES_PAYLOAD_SPEC.md`
- Maps: `CROWN_MAGUS_SPRINT_MAP.md`, `FILE_INDEX.md`, `LANE2_BILLING_MAP.txt`, `LANE3_ATTENDANCE_MAP.txt`

### moved to `scripts/demo/` and `scripts/ops/`

- Demo scripts: `DEMO_PROOF_REHEARSAL.ps1`, `demo_reset.ps1`, `proof_dev_gradebook_final.ps1`
- Ops scripts: `PRE_DEMO_RESET_AND_SEED.ps1`, `PRE_DEMO_VERIFICATION.ps1`, `RUN_PROOF_NO_MANUAL_CLEANUP.ps1`, `RUN_RESET_AND_BOOT_TWICE.ps1`, `_azure_endpoint_probe.ps1`, `golden_path.ps1`, `run_migrations_dev.ps1`, `run_migrations_remote.ps1`, `runall.ps1`, `runmigrate.ps1`, `runseed.ps1`, `runserver.ps1`, `test_azure_smoke.ps1`

### moved to `artifacts/archive/`

- `TEST_LOCAL_API.txt`
- `dummy.txt`
- `jwt_claims.txt`
- `login.json`
- `pr_body.txt`
- `prod_appsettings_before.json`
- `test_login.json`

## What Stayed at Root and Why

- Runtime/build essentials stayed: `.github/`, `backend/`, `frontend/`, `contracts/`, `scripts/`, `services/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `manage.py`, `README.md`, `CODEOWNERS`, security/config files.
- Ambiguous or potentially active files were intentionally not moved in this pass (for safety).

## Manual Review Items (Not Moved)

- Root artifacts/directories with ambiguous ownership or active usage signals:
  - `.venv/`, `.vscode/`, `.pytest_cache/`
  - `AUDIT_PACK_*/`
  - `BUYER_POSITIONING_NOTES.md`
  - `CROWN_MAGUS_COVERAGE_MATRIX.md`
  - `DJANGO_CRASHES_ANALYSIS.md`
  - `PHASE1_BUILD_ORDER.md`
  - `seed_a535.py`, `seed_a535_clean.py`
  - `core_shadowed/`, `crown2026_config/`
  - `_required_check_normalization.diff`, `ruleset_*.json`, `schools_prod.txt`, `temp_ops_views_tail.txt`

## Safe Follow-Up Pass

Moved additional root helper scripts into `scripts/ops/root_legacy/`:

- `_list_urls.py`
- `check_a535_dupes.py`
- `clean_a535_admissions.py`
- `d3_smoke_tests.py`
- `fetch_real_payload.py`
- `get_grades_payload.py`
- `phase2_verification.py`
- `proof_b2_render.py`
- `verify_api_routing.py`
- `verify_invoices_schema.py`
- `verify_seed.py`
- `hex_audit.ps1`

## Workflow Cleanup Recommendations for Phase 2

- Use `WORKFLOW_INVENTORY_PHASE1.md` and `WORKFLOW_REDUCTION_PLAN.md` as the source of truth.
- Keep canonical governance workflows active; consolidate duplicate proof/gate workflows.
- Archive demo/ceremony workflows only after branch-protection and owner validation.
- Avoid destructive removal until required checks are remapped and stable.

## PR Cleanup Recommendations for Phase 2

- Apply `PR_TRIAGE_PLAN.md` categories to all open PRs.
- Reduce active PR set to 0-3, close stale/superseded work, and enforce tighter merge discipline.
