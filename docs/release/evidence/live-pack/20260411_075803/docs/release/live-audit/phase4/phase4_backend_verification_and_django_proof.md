# LIVE BACKEND VERIFICATION

Generated UTC: 2026-04-11T08:51:35.1367318Z

## Command Results
- python --version: True
- django import/version: True
- manage.py check: True
- manage.py check --deploy: True
- manage.py showmigrations: True

## Backend Inventory
- backend app count: 91
- apps with models.py: 78
- apps with urls.py: 64
- apps with tests: 68
- backend test file count: 248

## Backend Module Snapshot
- academic_year_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- academics | models=True | urls=True | tests=40 | last_commit=2026-04-09T18:04:51-04:00
- academics_assignments | models=False | urls=False | tests=0 | last_commit=
- academics_curriculum | models=False | urls=False | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- academics_gradebook | models=False | urls=False | tests=0 | last_commit=
- academics_lesson_plans | models=False | urls=False | tests=0 | last_commit=
- academics_ro | models=True | urls=True | tests=0 | last_commit=2026-03-11T19:30:31-04:00
- admissions | models=True | urls=False | tests=8 | last_commit=2026-04-09T18:04:51-04:00
- advancement | models=True | urls=True | tests=17 | last_commit=2026-03-28T19:07:26Z
- aftercare | models=True | urls=True | tests=8 | last_commit=2026-03-15T18:49:11-04:00
- aid | models=True | urls=False | tests=14 | last_commit=2026-04-09T18:04:51-04:00
- analytics | models=True | urls=False | tests=2 | last_commit=2026-04-10T05:28:51-04:00
- applications | models=True | urls=False | tests=14 | last_commit=2026-03-15T18:49:11-04:00
- athletics | models=True | urls=False | tests=5 | last_commit=2026-03-11T22:03:18-04:00
- attendance | models=False | urls=False | tests=15 | last_commit=2026-04-09T18:04:51-04:00
- attendance_codes_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-28T05:20:02-05:00
- attendance_rules_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-27T13:30:03-05:00
- audit | models=True | urls=False | tests=0 | last_commit=2026-02-15T19:30:03-05:00
- bell_schedule_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T21:17:53-04:00
- billing | models=True | urls=False | tests=31 | last_commit=2026-04-09T18:04:51-04:00
- billing_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- board_oversight | models=True | urls=True | tests=14 | last_commit=2026-03-11T19:30:31-04:00
- classroom | models=True | urls=True | tests=5 | last_commit=2026-03-11T22:03:18-04:00
- comms | models=True | urls=True | tests=4 | last_commit=2026-04-09T18:04:51-04:00
- comms_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- compuwerx | models=False | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- core | models=True | urls=True | tests=14 | last_commit=2026-04-10T05:54:01-04:00
- course_catalog_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-27T19:58:50-05:00
- crown_api | models=True | urls=True | tests=122 | last_commit=2026-04-10T06:21:37-04:00
- curricula | models=True | urls=True | tests=5 | last_commit=2026-03-11T22:03:18-04:00
- curriculum | models=True | urls=True | tests=0 | last_commit=2026-03-11T22:03:18-04:00
- discipline | models=True | urls=True | tests=26 | last_commit=2026-04-09T18:04:51-04:00
- documents | models=True | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- enrollment | models=False | urls=False | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- enrollment_conversion_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-27T13:30:03-05:00
- enrollment_period_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- executive360 | models=False | urls=False | tests=22 | last_commit=2026-04-09T18:04:51-04:00
- facops | models=True | urls=False | tests=5 | last_commit=2026-03-11T22:03:18-04:00
- fee_schedule_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- ferpa_portal | models=False | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- finance | models=True | urls=False | tests=11 | last_commit=2026-03-14T08:34:02-04:00
- finance_setup | models=True | urls=True | tests=8 | last_commit=2026-03-14T08:34:02-04:00
- financial_aid | models=True | urls=True | tests=19 | last_commit=2026-03-15T16:04:28-04:00
- financial_aid_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T19:08:03-04:00
- governance | models=False | urls=True | tests=8 | last_commit=2026-04-10T05:54:01-04:00
- grade_scale_wizard | models=True | urls=True | tests=5 | last_commit=2026-03-11T21:17:53-04:00
- grade_weights_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-28T05:20:02-05:00
- gradebook | models=True | urls=True | tests=29 | last_commit=2026-03-11T22:03:18-04:00
- gradebook_setup_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-27T13:30:03-05:00
- graduation | models=True | urls=True | tests=0 | last_commit=2026-02-26T19:33:35-05:00
- guardian_household_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-28T05:20:02-05:00
- households | models=True | urls=True | tests=15 | last_commit=2026-03-11T22:03:18-04:00
- hr | models=True | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- imports | models=True | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00
- integrations | models=True | urls=True | tests=11 | last_commit=2026-04-09T18:04:51-04:00
- integrations_real | models=True | urls=True | tests=0 | last_commit=2026-02-23T22:19:50-05:00
- invoice_run_wizard | models=True | urls=True | tests=5 | last_commit=2026-02-27T13:30:03-05:00
- journal | models=True | urls=False | tests=5 | last_commit=2026-02-25T17:57:39-05:00
- ledger | models=True | urls=False | tests=35 | last_commit=2026-03-15T16:04:28-04:00
- messaging | models=True | urls=True | tests=0 | last_commit=2026-04-09T18:04:51-04:00

## Artifact Paths
- docs/release/live-audit/phase4/phase4_python_version.txt
- docs/release/live-audit/phase4/phase4_django_version.txt
- docs/release/live-audit/phase4/phase4_manage_check.txt
- docs/release/live-audit/phase4/phase4_manage_check_deploy.txt
- docs/release/live-audit/phase4/phase4_showmigrations.txt
- docs/release/live-audit/phase4/phase4_url_surface_scan.txt
- docs/release/live-audit/phase4/phase4_backend_app_inventory.csv
- docs/release/live-audit/phase4/phase4_backend_test_inventory.csv
