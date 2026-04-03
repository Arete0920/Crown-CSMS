# Root Inventory Phase 1

Generated on 2026-04-02 for branch chore/github-cleanup-phase1.

| path | type | classification | proposed destination | rationale | risk level |
|---|---|---|---|---|---|
| .dockerignore | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .editorconfig | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .env.local.example | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .git | DIR | KEEP_ROOT | (stay) | Canonical top-level directory. | low |
| .gitattributes | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .github | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .gitignore | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| .gitleaks.toml | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| .gitleaksignore | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| .pytest_cache | DIR | REVIEW_LATER | (tooling) | Tooling/system directory; do not relocate in this pass. | high |
| .venv | DIR | REVIEW_LATER | (tooling) | Tooling/system directory; do not relocate in this pass. | high |
| .vscode | DIR | REVIEW_LATER | (tooling) | Tooling/system directory; do not relocate in this pass. | high |
| AUDIT_PACK_20260330_133155 | DIR | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| AUDIT_PACK_20260330_193306 | DIR | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| AUDIT_PACK_20260330_193349 | DIR | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| BUYER_POSITIONING_NOTES.md | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| CHANGELOG.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| CI_USER_PROVISIONING.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| CODEOWNERS | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| CONTINGENCY_CURRICULUM_DEMO.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| COPILOT_GUARDRAILS.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| COPILOT_TASK_PROTOCOL.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| CROWN_DEV_CANON.md | FILE | MOVE_DOCS | docs/canons/ | Canonical doctrine/reference docs. | low |
| CROWN_MAGUS_COVERAGE_MATRIX.md | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| CROWN_MAGUS_SPRINT_MAP.md | FILE | MOVE_DOCS | docs/maps/ | Reference maps and navigation indices. | low |
| DASHBOARDS_PHASE_A_SPEC.md | FILE | MOVE_DOCS | docs/specs/ | Formal specifications and contracts. | low |
| DEEP_DIVE_ANALYSIS.md | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| DELIVERABLES.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| DEMO_CHECKLIST.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| DEMO_FLOW.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| DEMO_PROOF_REHEARSAL.ps1 | FILE | MOVE_SCRIPTS | scripts/demo/ | Demo-specific operational scripts. | low |
| DEMO_SCRIPT.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| DEMO_SCRIPT_CURRICULUM_SEGMENT.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| DEMO_SURFACE_WIRING_SPEC.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| DIRECTOR_FRAMEWORK_CONTRACT.md | FILE | MOVE_DOCS | docs/specs/ | Formal specifications and contracts. | low |
| DJANGO_CRASHES_ANALYSIS.md | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| Dockerfile | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| FILE_INDEX.md | FILE | MOVE_DOCS | docs/maps/ | Reference maps and navigation indices. | low |
| FINAL_CURRICULUM_PROOF.txt | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| GRADES_PAYLOAD_SPEC.md | FILE | MOVE_DOCS | docs/specs/ | Formal specifications and contracts. | low |
| IMPLEMENTATION_COMPLETE.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| IMPLEMENTATION_SUMMARY.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| INTEGRATION_GUIDE.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| LANE2_BILLING_MAP.txt | FILE | MOVE_DOCS | docs/maps/ | Reference maps and navigation indices. | low |
| LANE3_ATTENDANCE_MAP.txt | FILE | MOVE_DOCS | docs/maps/ | Reference maps and navigation indices. | low |
| MASTER_SUMMARY.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| PHASE1_BUILD_ORDER.md | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| PRE_DEMO_RESET_AND_SEED.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| PRE_DEMO_VERIFICATION.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| PRE_DEMO_VERIFICATION.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| PROJECT_COMPLETE.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| PROOF_ACADEMICS_ROSTER.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| PROOF_DEMO_SMOKE_FEB16.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| PROOF_DEV_SMOKE_SUCCESS_20260209.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| PROOF_UI_ACADEMICS_ROSTER_DRAWER.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| README.md | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| README_CURRICULUM_DEMO_PREP.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| README_DIRECTOR_ACTIONS.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| README_GOLDEN_PATH.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| RELEASE_PACKET_v0.4.0-rc1.commands.txt | FILE | MOVE_DOCS | docs/status/ | Release-status packet artifacts as documentation. | low |
| RELEASE_PACKET_v0.4.0-rc1.md | FILE | MOVE_DOCS | docs/status/ | Release-status packet artifacts as documentation. | low |
| ROTATE_SECRETS.md | FILE | MOVE_DOCS | docs/ops/ | Operational governance/runbook documentation. | low |
| RUNSHEET_CURRICULUM_DEMO.md | FILE | MOVE_DOCS | docs/demo/ | Demo-proof/checklist narrative documentation. | low |
| RUN_PROOF_NO_MANUAL_CLEANUP.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| RUN_RESET_AND_BOOT_TWICE.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| SECURITY.md | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| SPINE_DEFINITION_OF_DONE.md | FILE | MOVE_DOCS | docs/canons/ | Canonical doctrine/reference docs. | low |
| TENANT_ISOLATION_CANON.md | FILE | MOVE_DOCS | docs/canons/ | Canonical doctrine/reference docs. | low |
| TEST_LOCAL_API.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| VERIFICATION_REPORT.md | FILE | MOVE_DOCS | docs/status/ | Status/progress/release-tracking docs. | low |
| VERSION | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| _CLEAN_PREVIEW.txt | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| _audit_test_run.txt | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| _azure_endpoint_probe.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| _list_urls.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| _required_check_mapping.json | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| _required_check_mapping_after.json | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| _required_check_mapping_clean.json | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| _required_check_normalization.diff | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| backend | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| branch_protection.json | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| check_a535_dupes.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| clean_a535_admissions.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| contracts | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| core_shadowed | DIR | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| crown2026_config | DIR | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| curl_examples_director_actions.sh | FILE | REVIEW_LATER | (stay) | Needs manual classification. | medium |
| d3_smoke_tests.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| demo_reset.ps1 | FILE | MOVE_SCRIPTS | scripts/demo/ | Demo-specific operational scripts. | low |
| docker-compose.yml | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| docs | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| dummy.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| entrypoint.sh | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| fetch_real_payload.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| frontend | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| get_grades_payload.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| golden_path.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| hex_audit.ps1 | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| hex_audit.txt | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| hex_audit_output.txt | FILE | MOVE_DOCS | docs/audit/ | Audit evidence, diagnostics, or governance snapshot. | low |
| jwt_claims.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| local.secrets.ps1.example | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| login.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| manage.py | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| package-lock.json | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| phase2_verification.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| pr_body.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| prod_appsettings_before.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| proof_b2_render.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| proof_dev_gradebook_final.ps1 | FILE | MOVE_SCRIPTS | scripts/demo/ | Demo-specific operational scripts. | low |
| pytest.ini | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| requirements.txt | FILE | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| ruleset_main.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| ruleset_release.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| ruleset_tags.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| run_migrations_dev.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| run_migrations_remote.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| runall.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| runmigrate.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| runseed.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| runserver.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| schools_prod.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| scripts | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| seed_a535.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| seed_a535_clean.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| services | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| temp_ops_views_tail.txt | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| test_azure_smoke.ps1 | FILE | MOVE_SCRIPTS | scripts/ops/ | Operational/rehearsal scripts belong under scripts/ops. | low |
| test_login.json | FILE | MOVE_ARTIFACTS | artifacts/archive/ | Loose machine-generated or one-off data artifacts. | medium |
| tools | DIR | KEEP_ROOT | (stay) | Runtime/build/config-critical at root. | low |
| verify_api_routing.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| verify_invoices_schema.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
| verify_seed.py | FILE | MOVE_SCRIPTS | scripts/ops/ | Root helper scripts should live under scripts/ops. | medium |
