# Persona Journey Certification Matrix (2026-05-30)

Purpose: explicit certification state for top journey personas.

| persona | primary_routes | certification_status | evidence | owner |
| --- | --- | --- | --- | --- |
| student | /student, /student/dashboard | PARTIAL | frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx | student-platform |
| parent | /parent, /parent/dashboard, /parent/attendance | PARTIAL | frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx | family-platform |
| teacher | /teacher, /teacher/dashboard, /teacher/attendance | PARTIAL | frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx | academics-platform |
| registrar | registrar dashboard + enrollment wizards | PARTIAL | frontend/dashboards/src/routes/wizardRouteAccess.test.jsx | registrar-platform |
| finance | billing/finance dashboards + billing wizard | PARTIAL | frontend/dashboards/src/tests/wizardFlowContracts.test.js | finance-platform |
| admissions | admissions dashboard + enrollment conversion wizard | PARTIAL | backend/tests/test_release_security_readiness_contracts.py | admissions-platform |
| school_admin | school-admin dashboard + setup wizard routes | PARTIAL | frontend/dashboards/src/routes/wizardRouteAccess.test.jsx | admin-platform |
| board_member | school-board dashboard | PARTIAL | frontend/dashboards/src/config/dashboardRegistry.test.js | governance-platform |
