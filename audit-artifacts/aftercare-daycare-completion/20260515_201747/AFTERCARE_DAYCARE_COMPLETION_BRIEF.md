# Aftercare / Daycare Completion Brief

Generated: 2026-05-15T20:20:36.3293800-04:00
Branch: feature/aftercare-daycare-completion-20260515_201747

## Product Name
Public-facing: Daycare / Aftercare / Extended Care

## Code Name
aftercare

## Rule
Do not create a duplicate daycare backend app. Complete the existing aftercare module.

## Required completion outcomes

### Backend
- Verify and complete AftercareProgramConfig.
- Verify and complete AftercareEnrollment.
- Verify and complete AftercarePickupContact.
- Verify and complete AftercareAttendance.
- Verify and complete AftercareIncident.
- Keep tenant scoping through school_id / school_fk.
- Keep student references tied to existing student truth.
- Preserve existing /api/aftercare/ URL architecture.
- Add only missing migrations required for safe fields.
- Add or complete tests.

### API
Required endpoints:
- /api/aftercare/config/
- /api/aftercare/wizard/setup/
- /api/aftercare/enrollments/
- /api/aftercare/students/<student_id>/pickup-contacts/
- /api/aftercare/roster/today/
- /api/aftercare/attendance/checkin/
- /api/aftercare/attendance/checkout/
- /api/aftercare/incidents/
- /api/aftercare/parent/<student_id>/
- /api/aftercare/board/summary/

### Frontend
- Keep aftercareApi.js.
- Complete AftercareRosterPage.jsx.
- Complete AftercareSetupWizard.jsx.
- Complete AftercareBoardCard.jsx.
- Add missing route/nav registration only through existing routing/nav patterns.
- Public UI label may say Daycare / Aftercare / Extended Care.

### Permissions
- Admin: config/enrollment/full management.
- Aftercare staff: roster, check-in/out, pickup contacts, incidents.
- Parent: own child read-only summary only.
- Board/admin: board summary.
- No teacher default access unless explicitly allowed by existing permission model.

### Required proof
- Django check PASS.
- Migration drift PASS.
- Backend tests PASS or no-test gap explicitly documented.
- Frontend build PASS.
- API/route search proves all required endpoints.
- Frontend search proves all required pages/API client.
- Evidence summary generated.
