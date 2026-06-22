# Batch 5 Remaining Six Final Proof Packet

## Scope
This packet covers only the six remaining Batch 5 dashboards:

- data-migration
- integrations-automation
- revenue-operations
- summer-camp
- extended-care
- athletics-director

## Code changes in this lane

- `backend/crown_api/dashboards/views.py`
  - Adds the six remaining dashboards to strict tenant enforcement.
  - Merges supplemental Batch 5 payload builders into dashboard summary payload resolution.
- `backend/crown_api/dashboards/batch5_extra_payloads.py`
  - Adds a `summer-camp` dashboard summary payload contract.
- `backend/crown_api/tests/test_batch5_remaining_dashboard_summary_api.py`
  - Adds sample payload, authentication, explicit tenant header, same-tenant, and cross-tenant proof coverage for all six dashboards.

## Required validation commands

```bash
python -m pytest backend/crown_api/tests/test_batch5_remaining_dashboard_summary_api.py -v --nomigrations --tb=short
python backend/manage.py check
npm --prefix frontend/dashboards run test:e2e:smoke
```

## Claim boundary

This PR is a proof candidate until GitHub CI confirms the validation commands and repository gates pass on the same head SHA.

This packet does not claim:

- release/sandbox/pilot/production GO
- independent human review
- production readiness beyond dashboard internal proof scope

## Promotion condition

Promote the remaining six rows in `docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv` and `audit-artifacts/dashboard-completion/state/dashboard-certification-state.json` only after same-SHA CI settlement confirms this lane.
