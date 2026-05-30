# Home Academy Workpack 1 Summary

Generated: 2026-05-28
Status: Implemented via GitHub connector; CI/local runtime verification still required.

## Scope completed

- Added Home Academy / Homeschool Affiliation entry to the CROWN marketplace decision matrix.
- Added `docs/architecture/CROWN_HOME_ACADEMY_CANON.md`.
- Added `home_academy` as a `SchoolModule` entitlement key.
- Added Django app scaffold under `backend/home_academy/`.
- Registered `home_academy.apps.HomeAcademyConfig` in `INSTALLED_APPS`.
- Wired API v1 routes at `/api/v1/home-academy/`.
- Added initial Home Academy models and migration.
- Added serializers, admin registrations, tenant helper, API views, and eligibility services.
- Added service tests covering sports-only blocking, academic-anchor rules, school-of-record allowance, and capacity protection.

## Primary objects introduced

- `HomeAcademyProgram`
- `HomeAcademyEnrollment`
- `Offering`
- `OfferingEnrollment`
- `FinancialAidRule`
- `TranscriptPostingRule`

## Primary API surfaces introduced

- `GET/PUT /api/v1/home-academy/config/`
- `GET/POST /api/v1/home-academy/enrollments/`
- `GET/POST /api/v1/home-academy/offerings/`
- `GET/POST /api/v1/home-academy/offering-enrollments/`
- `GET /api/v1/home-academy/offerings/<offering_id>/students/<student_id>/eligibility/`
- `GET/POST /api/v1/home-academy/financial-aid-rules/`
- `GET /api/v1/home-academy/board/summary/`

## Guardrails implemented in first pass

- Sports default to two required academic courses.
- Music, drama, art, and clubs default to one required academic course.
- School-of-record and diploma-track students can satisfy academic-anchor checks for gated offerings.
- Homeschool seats are limited by released homeschool cap and physical capacity after reserved full-time seats and buffer seats.
- No released homeschool seats blocks registration.
- Transcript/diploma workflow is represented as guarded future/staging logic, not as a completed diploma issuance workflow.

## Verification required next

Run from repository root or backend context as appropriate:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
pytest backend/home_academy/tests/test_home_academy_services.py -q
```

If frontend surfaces are added later, also run the dashboard build gate.

## Not complete in this workpack

- Parent dashboard UI
- Admin dashboard UI
- Billing charge generation
- Financial-aid award application to Home Academy charges
- Attendance/check-in/check-out extension for Home Academy offerings
- Transcript staging implementation
- Graduation audit implementation
- Diploma issuance workflow
- State-specific compliance workflows
