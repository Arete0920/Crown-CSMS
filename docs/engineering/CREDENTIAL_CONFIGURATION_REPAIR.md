# Credential Configuration Repair

Base: `b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1`

Branch: `fix/configured-development-credentials`

Outcome: Remove shared credential fallbacks and reject development seed operations without a configured password.

Allowed files:

- `backend/crown_api/director_views.py`
- `backend/crown_api/exports/tests/test_export_tenant_boundaries.py`
- `backend/crown_api/templates/registration/login.html`
- `backend/crown_api/tests/test_director_actions_auth_required.py`
- `backend/tests/test_reporting_exports_gate.py`
- `frontend/dashboards/tests/api/gradebook-api-proof.spec.ts`
- `frontend/dashboards/tests/api/wizard-contract.spec.ts`
- `frontend/dashboards/tests/ui/demo-audit.spec.ts`
- `frontend/dashboards/tests/ui/gradebook-ui-proof.spec.ts`
- `scripts/manual_api_check.py`
- `scripts/manual_api_check2.py`
- `scripts/manual_api_check3.py`
- `scripts/ops/run_migrations_remote.ps1`
- `scripts/release-certification/00_run_release_certification.ps1`
- `scripts/release-certification/03_run_playwright_and_golden_path.ps1`
- `tools/dev_scripts/golden_path.ps1`
- `docs/engineering/CREDENTIAL_CONFIGURATION_REPAIR.md`

Forbidden: all other paths; no changes to tenant permissions, accounting, migrations, deployment targets, or enforcement thresholds.

Validation: Run director authorization tests including missing/blank-password cases; run Django system check; parse changed Python; inspect proof-tool environment configuration. Browser and Azure execution remain NOT VERIFIED.

Rollback: revert this isolated PR. Restoring old credential defaults is unsafe; disable the development seed endpoint instead when rolling back its behavior.

Decision owner: repository owner. Automated checks are not independent human review. Main integration and deployed behavior are not verified by this document.
