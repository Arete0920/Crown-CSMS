# dashboard-certification-center - Permission Proof

Status: collected
Date: 2026-06-19

## Tests executed

Command:
- C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr/venv/Scripts/python.exe -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_dashboard_certification_center_staff_user_receives_summary_payload backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_dashboard_certification_center_non_staff_user_is_forbidden backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_require_authentication backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked -q

Result:
- 6 passed in 178.62s

## Permission outcomes captured in run output

- Staff user on dashboard-certification-center summary endpoint: HTTP 200
- Non-staff user on dashboard-certification-center summary endpoint: HTTP 403
- Unauthenticated requests to Batch 0 keyed summary routes: HTTP 401

## Primary source tests

- backend/crown_api/tests/test_dashboard_snapshot_summary_api.py:131
- backend/crown_api/tests/test_dashboard_snapshot_summary_api.py:147
- backend/crown_api/tests/test_dashboard_snapshot_summary_api.py:175
