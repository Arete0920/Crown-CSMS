# Crown Deep Audit README

## Purpose
Create one authoritative audit pack that shows where Crown stands across:
- Core
- Modules
- Add-ons
- dashboards
- wizards
- pages
- APIs
- routes
- models
- services
- tests
- workflows
- docs
- infra helpers

## Expected Outputs
- MASTER_PLATFORM_INVENTORY.csv
- CORE_INVENTORY.csv
- MODULE_INVENTORY.csv
- ADDON_INVENTORY.csv
- DASHBOARD_WIZARD_PAGE_INVENTORY.csv
- API_ROUTE_CONTRACT_INVENTORY.csv
- MODEL_SERVICE_INVENTORY.csv
- TEST_CI_DOC_INVENTORY.csv
- TODO_SCAN.csv
- PLACEHOLDER_SCAN.csv
- ROUTE_RISK_SCAN.csv
- WORKFLOW_RISK_SCAN.csv
- MODULE_COMPLETION_MATRIX.csv
- KEEP_REWRITE_DROP_MATRIX.csv
- FINAL_AUDIT_SCORECARD.md
- FINAL_EXECUTIVE_AUDIT_SUMMARY.md

## Run Order
1. 00_bootstrap_deep_audit.ps1
2. 01_inventory_all.ps1
3. 02_static_scans.ps1
4. 03_runtime_checks.ps1
5. 04_generate_status_book.ps1
6. 05_open_outputs.ps1

## Rule
Do not change product scope while the audit is in flight.
