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

## Azure notes (important)

### Bootstrap before each Azure smoke
On Azure, the smoke run **changes state** (e.g., invoices get paid and awards get posted).  
So for repeatable receipts, run the bootstrap command first to print **fresh GP_* IDs**:

```bash
python backend/manage.py migrate --noinput
python backend/manage.py golden_path_bootstrap
```

Then paste the printed $env:GP_* lines into your local PowerShell session and run:

```powershell
.\tools\dev_scripts\golden_path.ps1 -ApiBase "https://<your-app>.azurewebsites.net" -SkipSeed
```

If your Azure run fails, the only thing I need is the **exact console output/traceback** from `golden_path_bootstrap` (first error line is usually enough to pinpoint schema/permissions/env).

---

## Steps 13-15  Read-Only Proof (Locked)

For a deterministic, step-by-step proof of core spine health without any write operations, see [docs/spine/STEP_13_15_RUNBOOK.md](docs/spine/STEP_13_15_RUNBOOK.md).

**Summary:**

- **Step 13:** Boot + Health (`/health/`) + Auth token + Admissions summary
- **Step 14:** Auth + tenant header + Admissions drilldown (94 records seeded)
- **Step 15:** Finance summary (`/api/director/finance/summary/?school_id=<uuid>`) + Financial Aid summary + Threads

All verified  2026-02-02.

**Route drift note:** Finance endpoints are under `/api/director/` namespace, not `/api/v1/`. Validate with Django resolver if endpoints return 404.

**Future hardening:** Finance should accept X-School-Id as single tenant context (remove required school_id param) for consistency.

---

## Step 19: Freeze + Canon Lock (2026-02-03)

**Purpose:** Lock the known-good proof ceremony configuration so all future CI runs use the same deterministic stack.

**Canon Authority:** CI proof ceremony on `origin/main` is the authoritative gate. Local proof is best-effort only.

### Proof Ceremony Configuration (LOCKED)

The following configuration is now canonical for this repo. Any deviation will break CI intentionally:

| Component | Value | Reason |
|-----------|-------|--------|
| **CI Python** | `3.13` | Stable wheel availability; psycopg v3 support |
| **Database Driver** | `psycopg[binary]==3.3.2` | Python 3.13+ compatible (psycopg2-binary EOL) |
| **Seed command** | `python manage.py seed_demo_school --wipe` | Clears stale audit history; needed for fresh DB |
| **Pytest target** | `backend/tests/test_director_actions.py` | Test file location after move (Step 18) |
| **Proof ceremony** | 7/7 tests GREEN | All checks passing locally & in CI |
| **Merge commit** | `37e95f18` | PR #9 merged to main on 2026-02-03 |

### Regression Guards

If any of the above changes without explicit Step 20+ approval:

1. Python version drift → CI will fail on wheel availability
2. psycopg2-binary re-added → CI will fail with ABI mismatch (Python 3.13 incompatible)
3. seed command without `--wipe` → CI will fail on duplicate key constraints
4. pytest path hardcoded wrong → CI will fail "file not found"

### To verify this lock is in place

```powershell
cd C:\Users\JMega\OneDrive\Desktop\Crown2026

# Check CI config
Select-String -Path ".github/workflows/proof-ceremony.yml" -Pattern "python-version|psycopg|seed_demo_school|test_director_actions"

# Check requirements
Select-String -Path "backend/requirements.txt" -Pattern "psycopg"

# Verify main is at merge commit
git log --oneline main | Select-Object -First 1
```

Expected output:

- `python-version: '3.13'`
- `psycopg[binary]==3.3.2`
- `seed_demo_school --wipe`
- `backend/tests/test_director_actions.py`
- HEAD is `37e95f18...` (merge commit)

