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

## Gate 1C: Auth Hardening + Tenant Proof (WhoAmI)

**Tag:** `gate1c-auth-tenant-proof` (to be created after merge)

**Purpose:** Verify default-deny auth, unskippable tenant enforcement, and whoami proof endpoint.

**Tests Run:**
```powershell
cd $env:USERPROFILE\OneDrive\Desktop\Crown2026
& ".\.venv\Scripts\python.exe" -m pytest backend/crown_api/tests/test_gate1c_auth_tenant_proof.py -v
```

**Expected Results:**
- 10/10 Gate 1C tests PASS (auth proof, tenant guard, whoami endpoint)

**Manual Proof Commands:**
```powershell
# 1. Verify whoami requires authentication (401 without auth)
curl http://127.0.0.1:8000/api/system/whoami/

# 2. Login and get access token
$loginResp = curl -X POST http://127.0.0.1:8000/api/auth/login/ `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"admin@heritage.test\",\"password\":\"crown123\"}' | ConvertFrom-Json
$token = $loginResp.access

# 3. Verify whoami with auth returns full session state
curl http://127.0.0.1:8000/api/system/whoami/ `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: <school-uuid>"

# Expected whoami response:
# {
#   "ok": true,
#   "user": {"id": "...", "email": "admin@heritage.test", "is_staff": true, "role": "admin", "school_id": "..."},
#   "tenant": {"resolved_school_id": "...", "resolution_source": "header", "header_present": true},
#   "override": {"school_override_id": "..." or null},
#   "build": {"build_sha": "local-dev", "env": "dev"}
# }
```

**CI Status:** Should be 9/9 checks GREEN

**What it tests:**
- DEFAULT_PERMISSION_CLASSES: IsAuthenticated (default-deny)
- Whoami endpoint requires JWT auth (401 without token)
- Whoami returns: user (id, email, is_staff, role), tenant (resolved school), override (if staff), build_sha
- TenantRequiredMixin enforces tenant on ViewSets (400 if missing)
- Build SHA exposed in settings and whoami response

**Definition of Done:**
- All Gate 1C tests PASS
- Whoami endpoint requires auth (401 without token)
- Whoami returns all required fields (user, tenant, override, build)
- CI pytest check GREEN

---

## Gate 1D — Authoritative Journal Ledger Core (Double-Entry)

**Canonical Tag:** `gate1d-ledger-core`
**Canonical Commit:** `aa569002`

### Proof: Repo + Tag
```powershell
git fetch origin
git show -s --oneline --decorate gate1d-ledger-core
git tag --points-at aa569002
```

**Expected Output:**
```
aa569002 (tag: gate1d-ledger-core) gate1d: add authoritative double-entry journal (models + service + invariants)
gate1d-ledger-core
```

### Proof: Journal Invariants (Local)
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test journal
```

**Expected Output:**
```
Found 8 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........
----------------------------------------------------------------------
Ran 8 tests in <X>s

OK
Destroying test database for alias 'default'...
```

**Expected Results:**
- All journal invariant tests PASS
- No failures

### Proof: Full Test Suite (Local)
```powershell
.\.venv\Scripts\python.exe manage.py test
```

**Expected Output:**
- Full suite PASS (0 failures)

**What it tests:**
- GLAccount model (chart of accounts, tenant-scoped, hierarchical)
- JournalEntry model (immutable, locked by default, no delete)
- JournalLine model (debit XOR credit, tenant validation, no delete)
- post_journal_entry service (single write path, atomic, balanced)
- Invariants:
  - Balanced entries succeed
  - Unbalanced entries fail
  - Single-line entries fail
  - Negative values fail
  - Cross-tenant accounts fail
  - Locked entries cannot be modified
  - Locked entries cannot be deleted
  - Atomic rollback on failure

**Definition of Done:**
- 8/8 journal invariant tests PASS
- Full test suite GREEN (no regressions)
- CI pytest check GREEN

---

## Gate 2A — AR → GL Integration (Charges/Payments Auto-Post to Journal)

**Canonical Tag:** `gate2a-ar-gl-integration`
**Canonical Commit:** `e1431f159d65e2961a73198cab5ce214a0ddaa61`

### Proof: Repo + Tag
```powershell
git fetch origin
git show -s --oneline --decorate gate2a-ar-gl-integration
git tag --points-at e1431f159d65e2961a73198cab5ce214a0ddaa61
```

**Expected Output:**
```
e1431f15 (tag: gate2a-ar-gl-integration) gate2a: post journal entries for charges and payments (idempotent) (#192)
gate2a-ar-gl-integration
```

### Proof: AR Posting Tests (Local)
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest backend/ledger/tests/test_ar_posts_to_journal.py -v
```

**Expected Output:**
```
============================== test session starts ==============================
platform win32 -- Python 3.x.x, pytest-x.x.x
collected 5 items

backend/ledger/tests/test_ar_posts_to_journal.py::ARPostsToJournalTestCase::test_canonical_gl_accounts_are_created PASSED [ 20%]
backend/ledger/tests/test_ar_posts_to_journal.py::ARPostsToJournalTestCase::test_charge_creation_posts_one_balanced_journal_entry PASSED [ 40%]
backend/ledger/tests/test_ar_posts_to_journal.py::ARPostsToJournalTestCase::test_idempotent_posting_no_duplicate_on_resave PASSED [ 60%]
backend/ledger/tests/test_ar_posts_to_journal.py::ARPostsToJournalTestCase::test_payment_creation_posts_one_balanced_journal_entry PASSED [ 80%]
backend/ledger/tests/test_ar_posts_to_journal.py::ARPostsToJournalTestCase::test_void_charge_does_not_post PASSED [100%]

============================== 5 passed in X.XXs ===============================
```

**Expected Results:**
- 5/5 tests PASS

**Note:**
- Charge creation posts balanced journal entry: DR AR / CR Revenue
- Payment creation posts balanced journal entry: DR Cash / CR AR
- Posting is idempotent via JournalEntry(reference_type, reference_id)
- Implemented via Django signals to cover all call sites

**What it tests:**
- post_charge_to_journal signal: Charge creation → DR Accounts Receivable / CR Tuition Revenue
- post_payment_to_journal signal: Payment creation → DR Cash / CR Accounts Receivable
- Idempotency: Resaving Charge/Payment does not create duplicate entries
- Void charges: is_void=True charges do not post to journal
- Canonical GL accounts: Lazy-creates 1000 Cash, 1100 AR, 4000 Revenue per school
- System user: crown-system user created for automated postings
- Tenant enforcement: Validates School.objects.filter(id=instance.school_id).first()

**Definition of Done:**
- 5/5 AR posting tests PASS
- Full test suite GREEN (233/233 pass)
- CI pytest check GREEN

---

## Future Smoke Tests

(Additional gates to be added as development continues)

---

## Rehearsal Reset (run before every rehearsal or demo)

```powershell
# 1. Kill stale servers
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Sync + verify
cd "$env:USERPROFILE\OneDrive\Desktop\Crown2026"
git checkout main; git pull --ff-only

# 3. Backend checks
cd backend
python manage.py migrate --check
python manage.py seed_curriculum_vertical_slice --school-id 19801b59-8c05-4c84-9312-5d792e4e839d

# 4. Start backend (background)
Start-Process python -ArgumentList "manage.py runserver 127.0.0.1:8000 --noreload"

# 5. Start frontend (new terminal)
cd "$env:USERPROFILE\OneDrive\Desktop\Crown2026\frontend\dashboards"
npx vite --host 127.0.0.1 --port 3000
```

---

## Quick Proof Commands (3 checks, <30 seconds)

Run after servers start to confirm everything is live:

```powershell
# 1. Backend health
Invoke-RestMethod http://127.0.0.1:8000/api/health/
# Expected: {"status":"ok", ...}

# 2. Demo token mint
$r = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/dev/token/ -Method POST `
  -ContentType "application/json" -Headers @{"X-Demo-Key"="CrownDemoKey!2026"} `
  -Body '{"persona":"STAFF"}'
$token = $r.access
# Expected: JWT string

# 3. Key endpoint per slice
# Academics
Invoke-RestMethod http://127.0.0.1:8000/api/academics/sections/ `
  -Headers @{"Authorization"="Bearer $token"}
# Expected: 2 sections (ENG-101, MATH-101)

# Billing
Invoke-RestMethod http://127.0.0.1:8000/api/health/
# Expected: status ok (billing runs through same server)
```

**Definition of Done:** All 3 commands return expected data, no 401/404/500.

---

**Last Updated:** 2026-02-18 (Academics polish merged, demo tag locked)

---

## Rollback Anchor

If anything breaks during demo prep, restore to the last known-good state:

```powershell
git checkout demo-2026-02-18-academics-polish
```

**Tag:** `demo-2026-02-18-academics-polish`
**Commit:** `2c6bd258`
**Contains:** PRs #211–#215 (billing fix, curriculum backend, UI pages, student picker + demo tools, seed Decimal fix)
**Verified:** 82 backend tests, frontend build clean, 3 academics routes live, 9/9 CI green

---

## Dependency Freeze Policy

**No new frontend or backend dependencies until after the demo** unless fixing a hard CI or runtime failure.

Forbidden frontend imports (enforced by CI):
- `@mui/icons-material` — not installed; use Unicode characters instead
- `@material-ui/icons` — legacy; not installed
