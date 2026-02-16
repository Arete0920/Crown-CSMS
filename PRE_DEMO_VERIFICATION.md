# Pre-Demo Verification - Automated Smoke Tests

This document contains deterministic one-command smoke tests that must PASS before any demo.

---

## Gate 1A: JWT Auth Core (Local Smoke)

**Purpose:** Verify JWT login/refresh/me endpoints work identically in local and CI.

**Command:**
```powershell
& ".\tools\dev_scripts\auth_smoke.ps1"
```

**Expected Output:**
```
=== Gate 1A: JWT Auth Local Smoke Test ===
Start line: main@534bf91d, tag: demo-jwt-auth-core-merged

[0/4] Cleaning up stale servers...
[1/4] Starting Django server...
[2/4] Waiting for server ready...
  Server ready after 0s
[2.5/4] Ensuring test user exists...
Created test user
[3/4] Testing JWT auth endpoints...
  [3a] POST /api/auth/login/ ... OK (got access+refresh)
  [3b] GET /api/auth/me/ (Bearer) ... OK (user=admin@heritage.test)
  [3c] POST /api/auth/refresh/ ... OK (got new access)
[4/4] Shutting down server...

=== RESULT: PASS ===
✓ All JWT auth endpoints returned 200 with expected data.
✓ Local behavior matches CI.
```

**Exit Code:** 0 (PASS) or 1 (FAIL)

**What it tests:**
- Server boots deterministically
- POST /api/auth/login/ returns access+refresh tokens
- GET /api/auth/me/ accepts Bearer token and returns user data
- POST /api/auth/refresh/ accepts refresh token and returns new access token

**Definition of Done:**
- Script exits 0
- All 3 endpoints return 200
- No CSRF errors
- No 404 errors

---

## Gate 1B: Tenant Enforcement

**Tag:** `gate1b-tenant-enforcement` (commit 1ea180df)

**Purpose:** Verify tenant resolution via header/JWT, validation layer, and audit trail.

**Tests Run:**
```powershell
cd $env:USERPROFILE\OneDrive\Desktop\Crown2026
& ".\.venv\Scripts\python.exe" -m pytest backend/households/tests/test_tenant_isolation.py -v
& ".\.venv\Scripts\python.exe" -m pytest backend/crown_api/tests/test_tenant_enforcement.py -v
& ".\.venv\Scripts\python.exe" -m pytest backend/crown_api/billing_api/tests/test_billing_audit_override_capture.py -v
```

**Expected Results:**
- 8/8 tenant isolation tests PASS (400/404 contract enforced)
- 6/6 tenant enforcement tests PASS (header/JWT resolution)
- 1/1 billing audit override test PASS (staff override tracked)

**CI Status:** 9/9 checks GREEN (PR #183)

**What it tests:**
- X-School-Id header takes precedence over JWT user.school_id
- Invalid header UUID → 400 ValidationError
- Valid UUID but nonexistent school → 404 NotFound
- Non-staff cross-tenant access via header → 404 NotFound
- Staff override via header → allowed + audit trail captured
- DRF force_authenticate compatibility

**Definition of Done:**
- All tenant_isolation tests PASS
- All tenant_enforcement tests PASS
- CI pytest check GREEN (270 tests including billing_api)

---

## Future Smoke Tests

### Gate 1C: Financial Ledger
(To be added after Issue #181)

---

**Last Updated:** 2026-02-16 (Gate 1B complete)
