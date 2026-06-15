# Wizard Certification Matrix (2026-05-30)

Purpose: explicit inventory of wizard surfaces and certification state.

Authority note: this matrix is aligned to current source proof. `frontend/dashboards/src/routes/wizard-manifest.js` inventories 28 wizard slugs, `backend/crown_api/wizard_registry.py` registers matching backend wizard routes, and `frontend/dashboards/src/tests/wizardFlowContracts.test.js` validates `_wizard.js` API flow adapters for create session, step mutation, session continuity, commit, and verify contracts.

Scope limitation: `FLOW_CONTRACT_VALIDATED` means route/API adapter contract validation only. It does not certify full end-to-end functional wizard completion, production readiness, visual QA, role-by-role runtime walkthroughs, or independent governance approval. Full wizard functional-flow closure requires reproduced evidence and independent review before release signoff.

| wizard_slug | certification_status | evidence | owner |
| --- | --- | --- | --- |
| onboarding | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/onboarding_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| reenrollment | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/reenrollment_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| billing-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/billing_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| aid-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/financial_aid_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| scheduling-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/scheduling_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| comms-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/comms_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| section-assign-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/section_assign_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| bell-schedule-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/bell_schedule_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| gradebook-setup-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/gradebook_setup_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| attendance-rules-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/attendance_rules_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| enrollment-conversion-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/enrollment_conversion_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| invoice-run-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/invoice_run_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| staff-onboarding-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/staff_onboarding_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| fee-schedule-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/fee_schedule_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| academic-year-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/academic_year_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| enrollment-period-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/enrollment_period_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| grade-scale-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/grade_scale_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| term-structure-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/term_structure_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| section-scheduler-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/section_scheduler_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| staff-setup-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/staff_setup_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| course-catalog-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/course_catalog_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| room-setup-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/room_setup_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| promotion-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/promotion_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| student-import-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/student_import_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| guardian-household-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/guardian_household_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| section-staffing-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/section_staffing_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| attendance-codes-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/attendance_codes_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
| grade-weights-wizard | FLOW_CONTRACT_VALIDATED | frontend/dashboards/src/api/grade_weights_wizard.js; frontend/dashboards/src/tests/wizardFlowContracts.test.js | wizard-owner-tbd |
