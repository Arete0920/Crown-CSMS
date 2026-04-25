# Steps 13-15 — Golden Path Runbook (Locked)

**Purpose:** Deterministic read-only proof of core spine health
**Date locked:** 2026-02-02
**Status:** ✅ GREEN (all steps verified)

---

## Step 13 — Boot + Health + Auth

### 13.0 Preconditions
- Backend running locally: `http://127.0.0.1:8000`
- `$env:CROWN_PASSWORD` set in session (or: hard stop)
- Health check passes (or: stop immediately)

```powershell
$API = "http://127.0.0.1:8000"
if (-not $env:CROWN_PASSWORD) { throw "CROWN_PASSWORD is not set in this session." }
curl.exe -s -i "$API/health/" | Select-Object -First 12
```

### 13.3 Health Check
- **Endpoint:** `GET /health/` (root level, NOT `/api/v1/health/`)
- **Auth:** None required
- **Pass criterion:** HTTP 200 + `{"ok": true, "build_sha": "local-dev"}`

```powershell
curl.exe -s -i http://127.0.0.1:8000/health/ | Select-Object -First 12
```

### 13.4 Auth Token
- **Endpoint:** `POST /api/v1/auth/token/`
- **Credentials:** `head@crown-demo.local` / `demo1234` (seeded in dev)
- **Pass criterion:** HTTP 200 + token length > 0
- **IMPORTANT:** Set `$env:CROWN_PASSWORD = 'demo1234'` in session before running

```powershell
$body = @{ username="head@crown-demo.local"; password=$env:CROWN_PASSWORD } | ConvertTo-Json -Compress
$token = (Invoke-RestMethod -Uri "$API/api/v1/auth/token/" -Method Post -ContentType "application/json" -Body $body).access
$token.Length  # Expected: 277
```

### 13.5 Core Endpoint (Admissions)
- **Endpoint:** `GET /api/v1/admissions/summary/`
- **Headers:** `Authorization: Bearer $token`, `X-School-Id: a5351136-98fe-4d48-add0-fa8f62d9ceff`
- **Pass criterion:** HTTP 200 + JSON response (no 401/403/404)

```powershell
$headers = @{ Authorization = "Bearer $token"; "X-School-Id" = "a5351136-98fe-4d48-add0-fa8f62d9ceff" }
Invoke-RestMethod -Uri "$API/api/v1/admissions/summary/" -Headers $headers
```

---

## Step 14 — Auth + Tenant Header + Core Drilldown

### 14.0 Reuse Step 13 variables
- `$API`, `$token`, `$headers` are live from Step 13

### 14.1 Admissions Drilldown
- **Endpoint:** `GET /api/v1/admissions/drilldown/?limit=10&offset=0`
- **Headers:** Same (auth + tenant)
- **Pass criterion:** HTTP 200 + `total` is a number, `results` is array

```powershell
$drill = Invoke-RestMethod -Uri "$API/api/v1/admissions/drilldown/?limit=10&offset=0" -Headers $headers
$drill.total  # Expected: 94 (seeded demo data)
```

---

## Step 15 — Multi-Module Health (Finance + Aid + Communications)

### 15.1 Finance Summary
- **Endpoint:** `GET /api/director/finance/summary/?school_id=<uuid>`
- **Headers:** Same (auth + tenant)
- **Important:** Requires `school_id` query param (even with X-School-Id header)
- **Pass criterion:** HTTP 200 + `{ tuition, aid, ledger }` structure

```powershell
$SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"
Invoke-RestMethod -Uri "$API/api/director/finance/summary/?school_id=$SCHOOL_ID" -Headers $headers
```

**Route drift note:** Finance may be under `/api/director/` rather than `/api/v1/` depending on spine wiring.

### 15.2 Financial Aid Summary
- **Endpoint:** `GET /api/v1/financial-aid/summary/`
- **Headers:** Same (auth + tenant)
- **Pass criterion:** HTTP 200 + `{ academic_year, applications, awards }` structure

```powershell
Invoke-RestMethod -Uri "$API/api/v1/financial-aid/summary/" -Headers $headers
```

### 15.3 Communications Threads
- **Endpoint:** `GET /api/v1/threads/?limit=5`
- **Headers:** Same (auth + tenant)
- **Pass criterion:** HTTP 200 + `{ value: [], Count: 0 }` or similar array structure (empty is OK)

```powershell
Invoke-RestMethod -Uri "$API/api/v1/threads/?limit=5" -Headers $headers
```

---

## Future Hardening

**Finance tenant scoping:** Finance summary should accept X-School-Id as the single source of tenant context (remove required school_id param). Currently inconsistent: endpoint accepts X-School-Id header but requires school_id query param.

**Route consolidation:** Determine canonical namespace for finance endpoints (/api/director/ vs /api/v1/). Document explicitly.

---

## Stop Conditions

- ✅ If all steps 200 OK + valid JSON: **Step 13-15 GREEN**
- ❌ If any step returns non-200 or unparseable JSON: **STOP immediately. Do not debug. Log error code + body.**
- ❌ If password is unset or health fails at start: **Hard stop before proceeding.**

