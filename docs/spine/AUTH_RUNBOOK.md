# AUTH_RUNBOOK (Non-Canonical)

**Purpose:** Practical operational guidance for obtaining JWTs and establishing tenant context during DEV/DEMO debugging and smoke testing demonstrated in the Spine docs.

> **NON-CANONICAL NOTICE**
> This runbook is allowed to contain implementation detail (current endpoints, UI helpers, sample commands).
> Do **not** copy/paste this content into canonical checklists. Canonical gates live in:
> - `docs/spine/DAILY_EXECUTION_CHECKLIST.md`

**Last verified:** 2026-02-05  
**Repo anchor commit:** `2094b884`  
**Backend auth primitives:** SimpleJWT `TokenObtainPairView` + `TokenRefreshView`

---

## Scope and safety

- This document is for **DEV/DEMO** operations and debugging.
- **Never** store or document real credentials, passwords, or secrets in this repo.
- Use **least privilege** accounts appropriate to the scenario and tenant.

---

## Tenant context model (why you see 403)

Protected endpoints require the request to resolve a **tenant** / school context via `get_request_school_id()` in `households/scoping.py`.

**Derivation order (single source of truth):**

1. **Staff/superuser header override** (for cross-school testing):
   - `X-School-Id` (canonical) via `request.META["HTTP_X_SCHOOL_ID"]`
   - `X-Crown-School-Id` (legacy alias) via `request.META["HTTP_X_CROWN_SCHOOL_ID"]`
   - Only honored for `is_staff=True` or `is_superuser=True`
   - Invalid UUID → `HTTP 400` "Invalid X-School-Id"
   - Valid UUID, nonexistent school → `HTTP 404` "School not found"

2. **User attributes** (primary for non-staff):
   - `user.school_id` (direct attribute)
   - `user.school.id` (relation fallback)

3. **Middleware fallback** (if middleware attaches it):
   - `request.school_id`

4. **Failure mode:**
   - Most endpoints use `required=False` mode
   - When tenant can't be derived → returns `None` → endpoint returns:
     - `HTTP 403` with body: `{"detail":"school_id could not be derived for request"}`

**Common causes of 403 tenant guard:**
- Unauthenticated requests (no JWT)
- User has no `school_id` attribute set
- Staff using invalid/nonexistent `X-School-Id` header
- Token valid but user not associated with any school

---

## Current JWT endpoints (verified 2026-02-05, commit `2094b884`)

### Canonical v1 (preferred)
- `POST /api/v1/auth/token/` (obtain access + refresh)
- `POST /api/v1/auth/token/refresh/` (refresh access token)

### Root-level (direct / legacy-compatible)
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`

> Note: `/api/` routes may also resolve through v1 aliasing depending on wiring. Prefer the explicit `/api/v1/...` paths for stability.

### Django session auth (admin / browser flows)
- `/accounts/login/`
- `/accounts/logout/`

---

## Token acquisition paths

### Path A: DevJwtPanel (UI helper) — when available
If the DEV UI includes a JWT helper panel, use it to:
- authenticate
- view current access token
- copy token into `$TOKEN` for smoke tests

> UI availability is environment-dependent. Treat it as a convenience, not a dependency.

### Path B: Obtain a JWT via API (curl.exe)
Use PowerShell `curl.exe` (not `curl`) to avoid alias behavior.

#### 1) Obtain token (v1 preferred)
```powershell
$BASE="https://crown-api-dev.azurewebsites.net"

# Provide credentials interactively or via secure local means.
# DO NOT commit credentials or write them into docs.
$BODY='{"username":"<YOUR_USERNAME>","password":"<YOUR_PASSWORD>"}'

curl.exe -sS -X POST "$BASE/api/v1/auth/token/" `
  -H "Content-Type: application/json" `
  -d $BODY
```

Expected response shape (example):
```json
{"access":"<ACCESS_JWT>","refresh":"<REFRESH_JWT>"}
```

#### 2) Refresh token
```powershell
$REFRESH_BODY='{"refresh":"<REFRESH_JWT>"}'

curl.exe -sS -X POST "$BASE/api/v1/auth/token/refresh/" `
  -H "Content-Type: application/json" `
  -d $REFRESH_BODY
```

---

## Calling protected endpoints with JWT

Set your token:
```powershell
$TOKEN="<ACCESS_JWT>"
```

Example call:
```powershell
curl.exe -sS -H "Authorization: Bearer $TOKEN" `
  -H "Accept: application/json" `
  "$BASE/api/billing/invoices/"
```

Expected outcomes:
- **200 OK** with JSON payload if user + tenant context are valid
- **403 Forbidden** if tenant cannot be derived or user lacks permissions

---

## X-School-Id header guidance (when needed)

Some endpoints or middleware configurations may support/require explicitly providing a school/tenant header.

Header name:
```
X-School-Id: <SCHOOL_UUID>
```

Example:
```powershell
$SCHOOL_ID="<SCHOOL_UUID>"

curl.exe -sS -H "Authorization: Bearer $TOKEN" `
  -H "X-School-Id: $SCHOOL_ID" `
  -H "Accept: application/json" `
  "$BASE/api/billing/invoices/"
```

**CORS note:** Custom headers may trigger browser preflight requests. If you see browser-only failures, validate CORS settings for allowed headers and origins.

---

## Common failure modes (fast triage)

### 401 Unauthorized
- Missing/invalid/expired JWT
- Wrong `Authorization` header format
- **Fix:** Obtain a fresh access token; confirm `Authorization: Bearer <token>`.

### 403 Forbidden (tenant guard)
- `school_id could not be derived for request`
- User not associated with tenant/school
- Missing tenant header/claim
- **Fix:** Use a user tied to the target school; add tenant header if required by that endpoint/middleware.

### 404 Not Found
- Route not deployed
- Wrong base URL or wrong path (v1 vs non-v1)
- **Fix:** Verify `$BASE`, confirm `/api/health/` `build_sha`, then re-check route path.

### CORS / preflight failures (browser)
- Missing allowed origin
- Missing allowed header (e.g., `X-School-Id`)
- Mixed scheme/host mismatch
- **Fix:** Compare with `curl.exe` behavior (no CORS). If curl works but browser fails, it's CORS.

### PowerShell curl alias
- `curl` in PowerShell may be an alias for `Invoke-WebRequest`
- **Fix:** use `curl.exe`.

---

## Escalation / diagnostics

- **Confirm current build:** `GET /api/health/` and inspect `build_sha`
- **For deployment conflicts (OneDeploy 409),** follow the canonical drill in:
  - `docs/spine/DAILY_EXECUTION_CHECKLIST.md`
- Check App Service logs / Deployment Center logs for deployment anomalies
- Use correlation IDs / request IDs where available in logs to trace requests
