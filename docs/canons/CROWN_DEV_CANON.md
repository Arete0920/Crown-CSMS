# CROWN_DEV_CANON.md
**Crown2026 Local Dev Golden Path (VS Code + GitHub)**
Last updated: 2026-04-16  
Owner: TC / Crown Team

---

## Purpose
This document is the single source of truth for starting, validating, troubleshooting, and committing Crown2026 local development.  
If you follow this exactly, you will not spend hours repeating the same problems.

---

## Non-Negotiables (Read This First)
1. **Two terminals only** in VS Code:
   - Terminal A: **BACKEND**
   - Terminal B: **FRONTEND**
2. Use **127.0.0.1** everywhere (avoid `localhost` when debugging).
3. Never "restart everything" blindly. **Check ports first**.
4. When something breaks, do **one thing**: follow the **Decision Tree** below. No improvising.
5. Make changes in **small commits**. If you break something, **revert fast**.

---

## Repo Location (Canonical)
Repo root:
```
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr
```

Backend:
```
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\backend
```

Frontend (dashboards):
```
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\frontend\dashboards
```

Python (canonical):
```
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\venv\Scripts\python.exe
```

---

## Ports (Canonical)
- Backend Django: **127.0.0.1:8000**
- Frontend Vite: **127.0.0.1:3000**

> If you choose to use a different port, document it and update this canon.
> Otherwise, treat these as fixed.

---

## VS Code Setup (Do Once)
1. Open VS Code → **File → Open Folder…**
   - Select: `C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr`
2. Open Terminal → New Terminal twice.
3. Rename terminals:
   - `BACKEND`
   - `FRONTEND`

---

## Golden Path: Start Backend (Always the Same)
**BACKEND terminal:**
```powershell
cd C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\backend
$env:DJANGO_SETTINGS_MODULE="crown_api.settings"
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

### Backend Health Check (Required)
Run in any PowerShell:
```powershell
curl.exe -i http://127.0.0.1:8000/health/ | Select-Object -First 10
```

Expected:
- HTTP/1.1 200 OK
- JSON body (ok/status)

**If health is not 200, stop. Do NOT start frontend yet.**

---

## Golden Path: Start Frontend (Always the Same)
**FRONTEND terminal:**
```powershell
cd C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\frontend\dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

### Frontend Check (Required)
```powershell
curl.exe -i http://127.0.0.1:3000/ | Select-Object -First 10
```

Expected:
- HTTP/1.1 200 OK

---

## Browser Golden Path

Use Edge or Chrome (either is fine).

Open:
- http://127.0.0.1:3000/
- http://127.0.0.1:3000/gradebook

### Dev JWT Panel (Dev Only)
In development, you may need to login after a restart. That is normal.

Credential handling:
- Do not store credentials in this canon.
- Load local dev credentials from `local.secrets.ps1` (not committed), then authenticate via the Dev JWT panel.
- Keep demo usernames, passwords, and tenant identifiers in local secret storage only.

Canonical storage keys:
- `auth_token`
- `school_id`

---

## STOP Doing These (They Cause the 2-Hour Loop)

- Do not repeatedly run `taskkill /F /IM node.exe` unless you've checked ports first.
- Do not repeatedly run `taskkill /F /IM python.exe` unless you've checked ports first.
- Do not guess whether something is running—confirm with `netstat`.
- Do not edit multiple files to "try things." Make one change, verify, commit.
- Do not use both `localhost` and `127.0.0.1` randomly. When stuck, use `127.0.0.1`.

---

## Port Checks (Use Every Time)

### Check Backend
```powershell
netstat -ano | findstr ":8000"
```

### Check Frontend
```powershell
netstat -ano | findstr ":3000"
```

**Interpretation:**
- No output → nothing is listening (server is not running).
- LISTENING → something owns the port; if the browser fails, it might be crashed or wrong host binding.

### Kill by PID (Preferred)
If netstat returns a PID, kill that PID:
```powershell
taskkill /PID <PID> /F
```

---

## Decision Tree (No Guessing)

### Symptom: Browser shows ERR_CONNECTION_REFUSED
1. Check port listening: `netstat -ano | findstr ":3000"`
2. If no output → start frontend.
3. If LISTENING → open http://127.0.0.1:3000/ (not localhost).

### Symptom: Blank white page (but 3000 responds)
1. This is almost always a Vite compile error.
2. Look at FRONTEND terminal output.
3. Fix the exact file/line shown.
4. Restart Vite.

### Symptom: Gradebook shows "missing JWT token"
1. That is expected after restarts in dev.
2. Use Dev JWT panel to login.
3. Confirm localStorage keys are `auth_token` and `school_id`.

### Symptom: API works in PowerShell but browser fails
1. Verify frontend origin and backend CORS settings.
2. Verify API_BASE is correct on the debug strip.
3. Verify requests include:
   - `Authorization: Bearer …`
   - `X-School-Id: …`

### Symptom: /gradebook shows 500 for a .jsx file
1. That means frontend module compilation failed, not Django.
2. Read the Vite terminal error. Fix the syntax/import issue.

---

## GitHub Workflow (Stops Backtracking)

### Always branch for changes
From repo root:
```powershell
cd C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr
git checkout -b fix/<short-name>
```

---

## Tagging (Canonical)
All repo tagging MUST use these scripts. Manual tags are forbidden.

- `scripts/tag_spine.ps1`
- `scripts/tag_freeze.ps1`
- `scripts/tag_gate.ps1`

## Tagging Doctrine (Canonical)

All Git tags MUST be created via these scripts only:

scripts/tag_spine.ps1

scripts/tag_gate.ps1

scripts/tag_freeze.ps1

Manual tags are forbidden (GitHub UI, git tag, IDE tooling, etc.).

Tags are part of the audit trail. Any tag not created by these scripts is non-canonical and must be deleted.

Preconditions enforced by scripts:

Must be inside a Git repo

Must be on main

Working tree must be clean

Local main must match origin/main

Tags must not already exist

Tags must be annotated and include canonical metadata (type, tag, branch, sha, utc, note)

Intended use:

tag_spine.ps1 → engineering milestone tags

tag_gate.ps1 → Gate pass tags (gate-#...)

tag_freeze.ps1 → freeze tags (freeze-YYYY-MM-DD-<label>)

### Small commits only
After each checkpoint works:
```powershell
git status
git add -A
git commit -m "<area>: <what changed>"
```

### Push when stable
```powershell
git push -u origin fix/<short-name>
```

### If you break something: revert fast
```powershell
git log --oneline -5
git revert <commit_hash>
```

**Do not keep "trying fixes" for 60 minutes. Revert and re-apply smaller.**

---

## Create Two Helper Scripts (Do Once)

Create a folder (if missing):
```
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\scripts
```

### scripts/dev-backend.ps1
```powershell
cd C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\backend
$env:DJANGO_SETTINGS_MODULE="crown_api.settings"
C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

### scripts/dev-frontend.ps1
```powershell
cd C:\\Users\\JMega\\OneDrive\\Desktop\\Crown2026_deploypr\frontend\dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

**Usage:**
- Run `.\scripts\dev-backend.ps1` in BACKEND terminal
- Run `.\scripts\dev-frontend.ps1` in FRONTEND terminal

---

## "Am I Healthy?" Checklist (Daily)

✅ Backend:
- `curl http://127.0.0.1:8000/health/` returns 200

✅ Frontend:
- `curl http://127.0.0.1:3000/` returns 200

✅ Gradebook:
- Page loads
- Sections appear after login
- No blank page
- Token stored in `auth_token`, school in `school_id`

---

## Canonical Debug Rules

1. **When stuck: port check → terminal output → minimal fix → verify → commit**
2. **Never do: "random restarts + random edits"**
3. **If you feel lost: stop and return to the Decision Tree above.**

---

_This canon is live. Update it when the path changes, commit the change._

---

## Environment Variable Canon (Prod)

| Variable | Value | Notes |
|---|---|---|
| `CROWN_ENV` | `prod` | **Canonical** env discriminator. Used by `health_views`, `system_views`, `settings._env_is_prod()` |
| `ENVIRONMENT` | `prod` | Legacy. Still guards `ops_views._dev_ops_enabled()`. Must stay set. |
| `DJANGO_DEBUG` | `false` | Must be set explicitly in Azure — do not rely on sniffing |
| `TENANT_HEADER_REQUIRED` | `true` | Must be set explicitly in Azure |
| `CROWN_DEMO_MODE` | (unset or `false`) | Only active demo flag. `DEMO_MODE` is inert — do not use |
| `CROWN_OPS_SECRET` | (unset) | Safe to leave unset in prod — dev-env gate fires first |
| `DEV_OPS_SECRET` | (unset) | **Must not be set in prod**. Dev/staging only |

**Canonical order of precedence** in `_env_is_prod()`: `CROWN_ENV` → `DJANGO_ENV` → `ENVIRONMENT` → `APP_ENV`.
Do not add new usages of the legacy vars. New code reads `CROWN_ENV` only.

---

## Dev-Ops Endpoint Policy

### `system_views.py` — dev-only, 403 in prod

All three are gated by `_is_dev_env()` (checks `CROWN_ENV`/`DJANGO_ENV`) **before** any secret is evaluated.
With `CROWN_ENV=prod`, they hard-stop at 403 and `CROWN_OPS_SECRET` is never consulted.

| Path | Guard | Prod behavior |
|---|---|---|
| `POST /api/v1/system/demo-reset/` | `_is_dev_env()` | 403 |
| `GET /api/v1/system/diagnose-db-tables/` | `_is_dev_env()` | 403 |
| `POST /api/v1/system/fix-schema-drift/` | `_is_dev_env()` | 403 |

### `ops_views.py` — dev-only, 404 in prod

Gated by `_dev_ops_enabled()` (checks `DEV_OPS_SECRET` + `settings.ENVIRONMENT == "dev"`).
404 (not 403) — existence is obscured. Do not set `DEV_OPS_SECRET` in prod.

| Path | Guard | Prod behavior |
|---|---|---|
| `POST /api/v1/system/ensure-ci-user/` | `_dev_ops_enabled()` | 404 |
| `POST /api/v1/system/demo-school/` | `_dev_ops_enabled()` | 404 |

### Prod-allowed admin endpoints

| Path | Guard | Notes |
|---|---|---|
| `GET /api/v1/system/seed-status/` | `IsAdminUser` | Intentionally prod-visible. Admin auth required. No dev-only gate. |

---

## Director Router: Superuser Fallback

`/director/` routes authenticated users by persona group or session.
Superusers and staff with no persona set are routed to `financial_aid_director` (primary demo persona).
This is intentional — it prevents the admin account from 403-ing during demos.
