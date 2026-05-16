# LIVE BACKEND VERIFICATION

Generated UTC: 2026-05-14T03:42:51.6117827Z

## Command Results
- python --version: True
- django import/version: True
- manage.py check: True
- manage.py check --deploy: True
- manage.py showmigrations: True

## Backend Inventory
- backend app count: 86
- apps with models.py: 74
- apps with urls.py: 54
- apps with tests: 59
- backend test file count: 223

## Backend Module Snapshot
- academic_year_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- academics | models=True | urls=True | tests=50 | last_commit=2026-05-01T13:13:34-04:00
- academics_assignments | models=False | urls=False | tests=0 | last_commit=
- academics_curriculum | models=False | urls=False | tests=0 | last_commit=
- academics_gradebook | models=False | urls=False | tests=0 | last_commit=
- academics_lesson_plans | models=False | urls=False | tests=0 | last_commit=
- academics_ro | models=True | urls=True | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- admissions | models=True | urls=False | tests=0 | last_commit=2026-04-03T17:38:43Z
- advancement | models=True | urls=True | tests=22 | last_commit=2026-04-18T06:19:41-04:00
- aftercare | models=True | urls=True | tests=10 | last_commit=2026-04-18T06:19:41-04:00
- aid | models=True | urls=False | tests=14 | last_commit=2026-04-18T06:19:41-04:00
- analytics | models=True | urls=False | tests=4 | last_commit=2026-04-18T06:19:41-04:00
- applications | models=True | urls=False | tests=18 | last_commit=2026-03-15T18:49:11-04:00
- athletics | models=True | urls=False | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- attendance | models=False | urls=False | tests=0 | last_commit=
- attendance_codes_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- attendance_rules_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- audit | models=True | urls=False | tests=0 | last_commit=2026-02-15T19:30:03-05:00
- bell_schedule_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- billing | models=True | urls=False | tests=27 | last_commit=2026-04-18T06:19:41-04:00
- billing_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- board_oversight | models=True | urls=True | tests=18 | last_commit=2026-04-18T06:19:41-04:00
- classroom | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- comms | models=True | urls=True | tests=0 | last_commit=2026-04-21T01:09:05-04:00
- comms_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-25T02:27:38-04:00
- core | models=True | urls=False | tests=18 | last_commit=2026-05-05T06:57:08-04:00
- course_catalog_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- crown_api | models=True | urls=True | tests=150 | last_commit=2026-05-12T20:13:55-04:00
- curricula | models=True | urls=True | tests=6 | last_commit=2026-03-11T22:03:18-04:00
- curriculum | models=True | urls=True | tests=0 | last_commit=2026-03-11T22:03:18-04:00
- discipline | models=True | urls=False | tests=0 | last_commit=2026-04-25T02:27:38-04:00
- documents | models=False | urls=False | tests=0 | last_commit=
- enrollment_conversion_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- enrollment_period_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- executive360 | models=False | urls=False | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- facops | models=True | urls=False | tests=6 | last_commit=2026-03-11T22:03:18-04:00
- fee_schedule_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- finance | models=True | urls=False | tests=14 | last_commit=2026-04-18T06:19:41-04:00
- finance_setup | models=True | urls=True | tests=10 | last_commit=2026-04-18T06:19:41-04:00
- financial_aid | models=True | urls=True | tests=26 | last_commit=2026-04-18T06:19:41-04:00
- financial_aid_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- governance | models=False | urls=True | tests=0 | last_commit=2026-04-21T01:09:05-04:00
- grade_scale_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- grade_weights_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- gradebook | models=True | urls=True | tests=38 | last_commit=2026-04-18T06:19:41-04:00
- gradebook_setup_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- graduation | models=True | urls=True | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- guardian_household_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- households | models=True | urls=True | tests=19 | last_commit=2026-04-18T06:19:41-04:00
- hr | models=True | urls=True | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- imports | models=False | urls=False | tests=0 | last_commit=
- integrations | models=True | urls=True | tests=16 | last_commit=2026-04-21T01:09:05-04:00
- integrations_real | models=True | urls=True | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- invoice_run_wizard | models=True | urls=True | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- journal | models=True | urls=False | tests=6 | last_commit=2026-02-25T17:57:39-05:00
- ledger | models=True | urls=False | tests=46 | last_commit=2026-04-18T06:19:41-04:00
- msauth | models=False | urls=True | tests=0 | last_commit=2026-04-18T06:19:41-04:00
- onboarding | models=True | urls=True | tests=10 | last_commit=2026-04-18T06:19:41-04:00
- outreach | models=True | urls=False | tests=6 | last_commit=2026-04-18T06:19:41-04:00
- parent360 | models=False | urls=False | tests=4 | last_commit=2026-04-18T06:19:41-04:00

## Artifact Paths
- docs/release/live-audit/phase4/phase4_python_version.txt
- docs/release/live-audit/phase4/phase4_django_version.txt
- docs/release/live-audit/phase4/phase4_manage_check.txt
- docs/release/live-audit/phase4/phase4_manage_check_deploy.txt
- docs/release/live-audit/phase4/phase4_showmigrations.txt
- docs/release/live-audit/phase4/phase4_url_surface_scan.txt
- docs/release/live-audit/phase4/phase4_backend_app_inventory.csv
- docs/release/live-audit/phase4/phase4_backend_test_inventory.csv
