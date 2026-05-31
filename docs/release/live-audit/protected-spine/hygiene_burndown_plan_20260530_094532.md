# Hygiene Burn-Down Plan - 20260530_094532

## Snapshot

- Branch: `release/security-runtime-governance-repair-little-lambs-full-build`
- Head at capture: `e7cade68`
- Tracked modified: `28`
- Untracked: `8`

## Noise Inventory (Grouped)

### Group A - Frontend dashboard template lane (high-volume)

- `frontend/dashboards/src/config/dashboardTemplates/activitiesAthleticsDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/attendanceDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/billingDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/communicationsDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/curriculumPDDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/extendedCareDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/facilitiesDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/financialAidDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/fineArtsDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/foodDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/gradebookDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/healthDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/hrDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/itDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/libraryMediaDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/registrarDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/safetySecurityDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/schedulingDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/studentCareDashboard.js`
- `frontend/dashboards/src/config/dashboardTemplates/transportationDashboard.js`

### Group B - Frontend routing/feature lane

- `frontend/dashboards/src/components/routing/ParentJourneyRouteGuard.jsx`
- `frontend/dashboards/src/features/learningContinuity/learningContinuityApi.js`
- `frontend/dashboards/src/features/parentJourney/ParentJourneyOverviewPage.jsx`
- `frontend/dashboards/src/pages/LearningContinuityWorkflows.jsx`

### Group C - Backend/settings lane

- `backend/crown_api/api_v1_urls.py`
- `backend/requirements.txt`

### Group D - Release docs lane (tracked)

- `docs/release/EVIDENCE_BASED_TOP_100_HARDENING_PRIORITIES_20260521.md`
- `docs/release/FINAL_SIGNOFF_CHECKLIST.md`
- `docs/release/live-audit/protected-spine/assessment_audit_scorecard_20260530_093810.md`
- `docs/release/live-audit/protected-spine/integrity_brief_20260530_094454.md`
- `docs/release/live-audit/protected-spine/integrity_checkpoint_20260530_094410.md`

### Group E - Untracked lane

- `80_runner_recovery_rerun_pack.ps1`
- `docs/release/BACKEND_AUTH_SECURITY_SWEEP_20260530.md`
- `docs/release/FRONTEND_VERIFICATION_EVIDENCE_20260530.md`
- `docs/release/TOP_50_PRIORITY_EXECUTION_LEDGER_20260530.md`
- `docs/release/live-audit/mainline-reconcile/` (directory tree)

## Controlled Execution Sequence

1. Batch 1: Release docs lane only (Group D + selected Group E docs) with single-purpose commit(s).
2. Batch 2: Backend/settings lane (Group C) with dedicated runtime regression proof.
3. Batch 3: Frontend routing/feature lane (Group B) with contracts + route proof.
4. Batch 4: Frontend template lane (Group A) with UI/contract/regression gate run.
5. Batch 5: Runner utility script lane (`80_runner_recovery_rerun_pack.ps1`) if still in scope.

## Guardrails Per Batch

- Pre-stage check: `git diff --cached --name-only` must be empty before staging each batch.
- Stage only intended paths per batch.
- Commit with path-scoped command for the exact batch files.
- Post-commit check: `git show --name-only --oneline --no-patch HEAD`.

## Completion Condition

- Unrelated noise removed or committed in controlled lanes.
- Staged scope remains deterministic for every commit.
- Governance/authority files remain synchronized during cleanup.
