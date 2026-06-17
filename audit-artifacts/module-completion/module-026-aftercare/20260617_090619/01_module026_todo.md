# Module 026 Proof TODO

## Canonical blocker

Enrollment and activity scheduling tests required.

## Existing implementation surface

- backend/aftercare/models.py
- backend/aftercare/api.py
- backend/aftercare/services.py
- backend/aftercare/urls.py
- backend/aftercare/wizard_api.py
- backend/tests/test_51x51_evidence_026_aftercare.py
- frontend/dashboards/src/api/aftercareApi.js
- frontend/dashboards/src/pages/AftercareRosterPage.jsx
- frontend/dashboards/src/pages/wizards/AftercareSetupWizard.jsx

## Required tests to add or harden

- enrollment create/list school scoped
- day-of-week roster filtering
- inactive enrollment excluded from roster
- expired enrollment excluded from roster
- unauthorized GET/POST behavior
- forbidden non-admin POST behavior
- check-in creates attendance
- checkout computes late fee
- monthly billing idempotency
- incident creation behavior
- tenant/school isolation

## Non-scope

- no migrations unless explicitly proven necessary
- no scorecard/matrix edit in proof PR
- no dashboard live-data certification
- no deployment claim
- no independent approval claim
