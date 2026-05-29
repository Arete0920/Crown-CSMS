# CROWN Finance and Tuition File-Level Execution Map (2026-05-28)

## Objective
Translate the finance superiority program into concrete backend and frontend file targets for implementation with minimal ambiguity.

## Core Backend Targets
### Finance domain
- backend/finance/models.py
- backend/finance/services.py
- backend/finance/api_views.py
- backend/finance/api_urls.py
- backend/finance/serializers.py
- backend/finance/permissions.py
- backend/finance/tests/test_finance_services.py
- backend/finance/tests/test_finance_api.py
- backend/finance/tests/test_finance_tenant.py

### Billing and fee setup domain
- backend/fee_schedule_wizard/models.py
- backend/fee_schedule_wizard/services.py
- backend/fee_schedule_wizard/views.py
- backend/fee_schedule_wizard/serializers.py
- backend/fee_schedule_wizard/tests/test_views.py
- backend/finance_setup/models.py
- backend/finance_setup/services.py
- backend/finance_setup/wizard_api.py
- backend/finance_setup/tests/test_finance_setup_api_numeric_validation.py
- backend/finance_setup/tests/test_finance_setup_locking.py

### Financial aid domain
- backend/financial_aid/models.py
- backend/financial_aid/services.py
- backend/financial_aid/api.py
- backend/financial_aid/serializers.py
- backend/financial_aid/permissions.py
- backend/financial_aid/scoping.py
- backend/financial_aid/need_index.py

### Admissions and enrollment handoff domain
- backend/applications/views_admissions.py
- backend/admissions/views_enroll.py
- backend/enrollment_period_wizard/services.py
- backend/enrollment_period_wizard/views.py

## Core Frontend Targets
### Parent and billing experiences
- frontend/dashboards/src/pages/BillingDashboard.jsx
- frontend/dashboards/src/pages/ParentApplicationFeePaymentPage.jsx
- frontend/dashboards/src/pages/ParentFinancialAidPreparationPage.jsx
- frontend/dashboards/src/pages/ParentLifecycleStatusCenterPage.jsx
- frontend/dashboards/src/features/parentJourney/ParentJourneyOverviewPage.jsx
- frontend/dashboards/src/features/parentJourney/parentJourneyState.js

### Finance and board experiences
- frontend/dashboards/src/pages/SchoolAdministratorDashboard.jsx
- frontend/dashboards/src/pages/BoardDashboard.jsx
- frontend/dashboards/src/pages/SchoolBoardDashboard.jsx
- frontend/dashboards/src/components/FinanceKPI.jsx
- frontend/dashboards/src/components/board/BoardKpiTile.jsx

### Wizard and API wiring
- frontend/dashboards/src/pages/BillingWizard.jsx
- frontend/dashboards/src/pages/wizards/FinanceSetupWizard.jsx
- frontend/dashboards/src/api/finance.js
- frontend/dashboards/src/api/financialAid.js
- frontend/dashboards/src/api/financial_aid_wizard.js
- frontend/dashboards/src/api/billing_wizard.js
- frontend/dashboards/src/api/financeSetupApi.js

### Shared shell consistency
- frontend/dashboards/src/components/launch/CrownLaunchShell.jsx
- frontend/dashboards/src/components/launch/CrownPageHeader.jsx
- frontend/dashboards/src/components/crown-dashboard/CrownDashboardCommunicationsStrip.jsx
- frontend/dashboards/src/components/crown-dashboard/CrownDashboardDataTruthStatus.jsx
- frontend/dashboards/src/features/dashboards/RoleDashboard.tsx
- frontend/dashboards/src/features/dashboards/crown-dashboard.css

## Test and Contract Targets
- frontend/dashboards/src/tests/personaDashboardCertification.test.jsx
- frontend/dashboards/src/tests/dashboardCardContract.test.jsx
- frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx
- frontend/dashboards/src/routes/financeRouteAccess.test.jsx
- frontend/dashboards/src/routes/wizardRouteAccess.test.jsx
- frontend/dashboards/src/tests/apiContractRegistry.test.js

## Workstream to File Mapping
### WS1 Parent Financial Home
Backend:
- backend/finance/services.py
- backend/finance/api_views.py
Frontend:
- frontend/dashboards/src/pages/BillingDashboard.jsx
- frontend/dashboards/src/features/parentJourney/ParentJourneyOverviewPage.jsx

### WS2 Finance Command Center
Backend:
- backend/finance/services.py
- backend/finance/api_views.py
Frontend:
- frontend/dashboards/src/pages/SchoolAdministratorDashboard.jsx
- frontend/dashboards/src/components/FinanceKPI.jsx

### WS3 Tuition Builder Wizard
Backend:
- backend/fee_schedule_wizard/services.py
- backend/finance_setup/services.py
Frontend:
- frontend/dashboards/src/pages/BillingWizard.jsx
- frontend/dashboards/src/pages/wizards/FinanceSetupWizard.jsx

### WS4 Financial Aid Workspace
Backend:
- backend/financial_aid/services.py
- backend/financial_aid/api.py
Frontend:
- frontend/dashboards/src/api/financialAid.js
- frontend/dashboards/src/api/financial_aid_wizard.js
- frontend/dashboards/src/pages/ParentFinancialAidPreparationPage.jsx

### WS5 A/R Aging Dashboard
Backend:
- backend/finance/services.py
Frontend:
- frontend/dashboards/src/pages/BillingDashboard.jsx
- frontend/dashboards/src/pages/SchoolAdministratorDashboard.jsx

### WS6 Reconciliation Workspace
Backend:
- backend/finance/services.py
- backend/finance/models.py
Frontend:
- frontend/dashboards/src/pages/BillingDashboard.jsx
- frontend/dashboards/src/api/finance.js

### WS7 Family Statement Page
Backend:
- backend/finance/api_views.py
- backend/finance/services.py
Frontend:
- frontend/dashboards/src/pages/ParentLifecycleStatusCenterPage.jsx

### WS8 Board Finance Dashboard
Backend:
- backend/finance/services.py
Frontend:
- frontend/dashboards/src/pages/BoardDashboard.jsx
- frontend/dashboards/src/pages/SchoolBoardDashboard.jsx

## Sequencing Rules
1. Start each workstream with backend tests and fixtures.
2. Add API contracts second.
3. Add UI wiring third.
4. Run role and route guards before merge.
5. Update runtime-release evidence packet after each merged slice.

## Exit Criteria per Workstream
- API responses are deterministic and tenant-safe.
- Permission model is enforced and tested.
- UI reflects backend truth (no optimistic fake states).
- Exports and reports are validated when applicable.
- Persona contract tests remain green.
