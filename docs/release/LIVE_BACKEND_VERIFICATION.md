# LIVE BACKEND VERIFICATION

Generated UTC: 2026-04-21T05:14:59.9422682Z

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
- apps with tests: 58
- backend test file count: 222

## Backend Module Snapshot
- academic_year_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- academics | models=True | urls=True | tests=38 | last_commit=2026-04-18T15:21:56Z
- academics_assignments | models=False | urls=False | tests=0 | last_commit=
- academics_curriculum | models=False | urls=False | tests=0 | last_commit=
- academics_gradebook | models=False | urls=False | tests=0 | last_commit=
- academics_lesson_plans | models=False | urls=False | tests=0 | last_commit=
- academics_ro | models=True | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- admissions | models=True | urls=False | tests=0 | last_commit=2026-04-03T17:38:43Z
- advancement | models=True | urls=True | tests=17 | last_commit=2026-04-14T06:58:59Z
- aftercare | models=True | urls=True | tests=8 | last_commit=2026-04-14T06:58:59Z
- aid | models=True | urls=False | tests=11 | last_commit=2026-04-11T21:39:44-04:00
- analytics | models=True | urls=False | tests=3 | last_commit=2026-04-18T20:25:56Z
- applications | models=True | urls=False | tests=14 | last_commit=2026-03-15T18:49:11-04:00
- athletics | models=True | urls=False | tests=5 | last_commit=2026-04-13T20:14:25-04:00
- attendance | models=False | urls=False | tests=0 | last_commit=
- attendance_codes_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- attendance_rules_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- audit | models=True | urls=False | tests=0 | last_commit=2026-02-15T19:30:03-05:00
- bell_schedule_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- billing | models=True | urls=False | tests=20 | last_commit=2026-04-11T21:39:44-04:00
- billing_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- board_oversight | models=True | urls=True | tests=14 | last_commit=2026-04-13T20:14:25-04:00
- classroom | models=True | urls=True | tests=5 | last_commit=2026-04-12T05:59:58Z
- comms | models=True | urls=True | tests=0 | last_commit=2026-04-19T00:53:56-04:00
- comms_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- core | models=True | urls=False | tests=14 | last_commit=2026-04-19T00:53:56-04:00
- course_catalog_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- crown_api | models=True | urls=True | tests=111 | last_commit=2026-04-20T09:22:17Z
- curricula | models=True | urls=True | tests=5 | last_commit=2026-04-12T05:59:58Z
- curriculum | models=True | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- discipline | models=True | urls=False | tests=0 | last_commit=2026-04-12T05:59:58Z
- documents | models=False | urls=False | tests=0 | last_commit=
- enrollment_conversion_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- enrollment_period_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- executive360 | models=False | urls=False | tests=0 | last_commit=2026-04-12T05:59:58Z
- facops | models=True | urls=False | tests=5 | last_commit=2026-04-12T05:59:58Z
- fee_schedule_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- finance | models=True | urls=False | tests=11 | last_commit=2026-04-13T19:06:34-04:00
- finance_setup | models=True | urls=True | tests=8 | last_commit=2026-04-12T05:59:58Z
- financial_aid | models=True | urls=True | tests=20 | last_commit=2026-04-12T05:59:58Z
- financial_aid_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- governance | models=False | urls=True | tests=0 | last_commit=2026-04-20T17:27:06Z
- grade_scale_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- grade_weights_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- gradebook | models=True | urls=True | tests=29 | last_commit=2026-04-13T18:03:15-04:00
- gradebook_setup_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- graduation | models=True | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- guardian_household_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- households | models=True | urls=True | tests=15 | last_commit=2026-04-15T06:04:51-04:00
- hr | models=True | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- imports | models=False | urls=False | tests=0 | last_commit=
- integrations | models=True | urls=True | tests=11 | last_commit=2026-04-19T00:53:56-04:00
- integrations_real | models=True | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- invoice_run_wizard | models=True | urls=True | tests=5 | last_commit=2026-04-13T20:35:54-04:00
- journal | models=True | urls=False | tests=5 | last_commit=2026-02-25T17:57:39-05:00
- ledger | models=True | urls=False | tests=35 | last_commit=2026-04-13T21:03:33-04:00
- msauth | models=False | urls=True | tests=0 | last_commit=2026-04-12T05:59:58Z
- onboarding | models=True | urls=True | tests=8 | last_commit=2026-04-13T20:02:09-04:00
- outreach | models=True | urls=False | tests=5 | last_commit=2026-04-13T20:14:25-04:00
- parent360 | models=False | urls=False | tests=3 | last_commit=2026-04-12T18:44:54-04:00

## Artifact Paths
- docs/release/live-audit/phase4/phase4_python_version.txt
- docs/release/live-audit/phase4/phase4_django_version.txt
- docs/release/live-audit/phase4/phase4_manage_check.txt
- docs/release/live-audit/phase4/phase4_manage_check_deploy.txt
- docs/release/live-audit/phase4/phase4_showmigrations.txt
- docs/release/live-audit/phase4/phase4_url_surface_scan.txt
- docs/release/live-audit/phase4/phase4_backend_app_inventory.csv
- docs/release/live-audit/phase4/phase4_backend_test_inventory.csv
