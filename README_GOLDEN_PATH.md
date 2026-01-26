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

## Azure Dev Smoke (API-only)

### Why API-only?

From your laptop, you **should not** run Django shell/seed scripts against the remote DB. For Azure, this harness:

- hits `/health/`
- fetches JWT
- calls `/api/director/actions/` (`POST_ACCEPTED_AWARDS`)
- calls `/api/billing/payments/record/`

It prints receipts strictly from API responses.

### Prereqs (one-time)

Your Azure dev environment must already contain:

- a School + AcademicYear
- an ACCEPTED AidAward (ID)
- an Invoice (UUID)
- (optional) an AidApplication in NEEDS_INFO (ID)

Recommended: create a server-side management command that seeds these and prints IDs, then store them as App Settings or copy them locally.

### Run (Azure dev)

Set these env vars in your PowerShell session:

```powershell
$env:GP_SCHOOL_ID    = "PUT-SCHOOL-UUID"
$env:GP_YEAR_ID      = "PUT-YEAR-ID"
$env:GP_AID_AWARD_ID = "PUT-AID-AWARD-ID"
$env:GP_AID_APP_ID   = "PUT-AID-APP-ID"     # optional
$env:GP_INVOICE_ID   = "PUT-INVOICE-UUID"
```

Run the harness:

```powershell
cd C:\Users\JMega\OneDrive\Desktop\Crown2026
.\tools\dev_scripts\golden_path.ps1 -ApiBase "https://YOUR-DEV.azurewebsites.net" -SkipSeed
```

Expected receipts:

- Health: JSON OK
- Director Actions: HTTP 200 + `posted_count` (0 or 1)
- Billing: HTTP 201 + invoice balance goes to 0 in the response body

---

## Commit + push (exact commands)

```powershell
cd C:\Users\JMega\OneDrive\Desktop\Crown2026
git status -sb

git add tools/dev_scripts/golden_path.ps1 README_GOLDEN_PATH.md
git commit -m "Golden Path: Azure-safe ApiBase + SkipSeed"
git push

git status -sb
```

## What you do next (no guessing)

If you already have Azure IDs:

```powershell
$env:GP_SCHOOL_ID    = "..."
$env:GP_YEAR_ID      = "..."
$env:GP_AID_AWARD_ID = "..."
$env:GP_INVOICE_ID   = "..."
$env:GP_AID_APP_ID   = "..."   # optional
.\tools\dev_scripts\golden_path.ps1 -ApiBase "https://YOUR-DEV.azurewebsites.net" -SkipSeed
```

If you don’t have Azure IDs yet:

The correct next move is: add a server-side seed command (on Azure) that prints those IDs once. If you want, tell me “seed command,” and I’ll add the exact Django management command file and where to hook it.
