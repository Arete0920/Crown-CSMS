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

## Future Smoke Tests

### Gate 1B: Tenant Enforcement
(To be added after Issue #180)

### Gate 1C: Financial Ledger
(To be added after Issue #181)

---

**Last Updated:** 2026-02-17 (Gate 1A complete)
