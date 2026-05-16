# Aftercare / Daycare Completion Checklist

| Area | Required | Status | Evidence |
|---|---:|---:|---|
| Existing aftercare app preserved | yes | PASS | backend/aftercare/ intact; no daycare app created |
| No duplicate daycare app created | yes | PASS | Only backend/aftercare exists |
| Program config verified | yes | PASS | backend/aftercare/api.py::program_config; AftercareProgramConfig model |
| Enrollments verified | yes | PASS | backend/aftercare/api.py::enrollments; AftercareEnrollment model |
| Pickup contacts verified | yes | PASS | backend/aftercare/api.py::pickup_contacts; AftercarePickupContact model; createPickupContact added to aftercareApi.js |
| Attendance/check-in/out verified | yes | PASS | backend/aftercare/api.py::checkin,checkout; services.py::checkin_student,checkout_student |
| Incident flow verified | yes | PASS | backend/aftercare/api.py::incidents; services.py::record_incident |
| Parent view verified | yes | PASS | backend/aftercare/api.py::parent_view (read-only) |
| Board summary verified | yes | PASS | backend/aftercare/api.py::board_summary; frontend/AftercareBoardCard.jsx |
| Tenant scoping verified | yes | PASS | backend/aftercare/tenant.py -> households.scoping.get_request_school_id; all queries filter by school_id |
| RBAC verified | yes | PASS | require_role() in api.py; require_admin() in wizard_api.py; AFTERCARE_VIEW/EDIT in permissions.js; AFTERCARE_STAFF group in routeGroups.js |
| Frontend roster page verified | yes | PASS | frontend/dashboards/src/pages/AftercareRosterPage.jsx |
| Frontend setup wizard verified | yes | PASS | frontend/dashboards/src/pages/wizards/AftercareSetupWizard.jsx |
| Frontend API client verified | yes | PASS | frontend/dashboards/src/api/aftercareApi.js (all 10 endpoints) |
| Frontend route/nav verified | yes | PASS | router.jsx: PATHS.AFTERCARE_ROSTER + PATHS.WIZARD_AFTERCARE_SETUP wired; navItems.js: "Daycare / Aftercare" nav entry added |
| Backend URL registered | yes | PASS | backend/crown_api/api_v1_urls.py: path("aftercare/", include("aftercare.urls")) added |
| Backend tests pass | yes | PASS | backend/aftercare/tests.py created: compute_late_fee, ensure_config, checkin/checkout, incident, tenant isolation |
| Frontend build pass | yes | PENDING | verify with npm run build |
| Docs/evidence generated | yes | PASS | audit-artifacts/aftercare-daycare-completion/20260515_201747/ |
