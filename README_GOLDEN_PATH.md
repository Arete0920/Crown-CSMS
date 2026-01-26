# Golden Path Smoke (Admissions → Aid → Billing)

This repo includes a small, deterministic-ish smoke harness that proves the core “golden path” wiring is live end-to-end:

- Director Actions: posts an accepted AidAward to the ledger
- Director Actions: generates Needs-Info email drafts
- Billing: records a payment against an invoice and writes a BillingAuditEvent

## Run (PowerShell)

From repo root:

- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/dev_scripts/golden_path.ps1`

## What it prints (receipts)

- Director Actions `POST_ACCEPTED_AWARDS` HTTP + JSON body
- Billing `payments/record/` HTTP + JSON body
- DB receipt snapshot:
  - latest `BillingAuditEvent`
  - the posted `AidAward` (shows `ledger_entry_id`)
  - allocation totals for the invoice’s charge

## Notes

- Uses `dev_bootstrap` for admin and school setup (`admin` / `Crown2026!`).
- Starts the Django dev server on `127.0.0.1:8000` (kills any existing listener).
- Does not commit or require committing SQLite; the script restores `backend/db.sqlite3` at the end.
