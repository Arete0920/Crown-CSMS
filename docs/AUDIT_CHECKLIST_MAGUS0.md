# Crown Magus 0 — Trust-Nothing Audit Checklist

> **Purpose:** Pre-merge / pre-demo / pre-release human gate.  
> **Automated companion:** `tools/audit/CROWN_MAGUS0_AUDIT.ps1`  
> **Gate workflow:** `.github/workflows/crown-magus0-gate.yml`  
> **Last updated:** 2026-02-28 — secret scan gate fixed (PRs #488 #489); tag `magus0-gate-green-2026-02-28` @ `5041c574`

Mark every item `[x]` before signing off. Any unchecked `[ ]` = BLOCK.

---

## P0 — Data Leak / Auth Break (block release)

### Tenant Safety
- [ ] Every read/write API endpoint that touches school data enforces `X-School-Id` via `get_request_school_id(request, required=True)`
- [ ] No `.objects.get()` / `.objects.filter()` on tenant-scoped models without `school_id=` binding (AST tripwire: `tools/verify_backend_gate.py --tenant-checks-only`)
- [ ] Cross-tenant attempt returns `403` or `404`, NEVER data from another school
- [ ] `TENANT_HEADER_REQUIRED` is `True` in production settings
- [ ] `RequireTenantMiddleware` exempt list is minimal (only `/api/platform/`, `/api/health/`, `/api/auth/`, `/api/integrity/`)

### Authentication & RBAC
- [ ] JWT validation is active; expired/missing tokens return `401`
- [ ] Token refresh path tested: expired access token + valid refresh → new access token
- [ ] Role matrix confirmed:
  - `board` → read-only dashboards; no write endpoints
  - `admin` (school-level) → full CRUD within own school
  - `teacher` → grades/attendance for own sections only
  - `parent/student` → own records only
  - `platform admin` (`IsAdminUser`) → cross-tenant ops endpoints only
- [ ] Object ownership: parent A cannot read parent B's student records
- [ ] Teacher cannot read another teacher's private notes / sections
- [ ] Director actions (`POST /api/director/actions/`) requires `IsAuthenticated` + role check

### Secrets / Config
- [ ] `DEBUG = False` in production settings
- [ ] No `CORS_ALLOW_ALL_ORIGINS = True` (automated: settings scan)
- [ ] `ALLOWED_HOSTS` does not contain `*` in production
- [ ] `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True` in production
  - [x] Secret scan: zero hits for AWS keys, OpenAI keys, Stripe live keys, private key material in tracked files — **verified 2026-02-28; scanner self-hit fixed in PRs #488 #489**
- [ ] No `.env` files tracked in git
- [ ] `local.secrets.ps1` is in `.gitignore`

---

## P1 — Auth Break / Integrity Failure (block demo/release)

### Financial / Ledger Invariants
- [ ] Payment posting is idempotent (double POST with same idempotency key = single ledger entry)
- [ ] Void/reversal produces balanced ledger state (debit == credit after reversal)
- [ ] Every financial mutation has an audit log entry (`AuditLog` or `AuditEvent`)
- [ ] No financial write endpoint is accessible without explicit school_id scoping

### Admissions → Enrollment → Billing Flow
- [ ] Application creates candidate record scoped to correct school
- [ ] Enrollment converts candidate to student AND triggers billing setup
- [ ] Aid recommendations do not bypass approval workflow
- [ ] "Empty seat" recommendations respect approval gate

### Wizard Registry Completeness
- [ ] `tools/verify_backend_gate.py` tenant gate passes (no unscoped wizard endpoints)
- [ ] Wizard discovery test passes: `backend/tests/test_wizard_discovery.py`
- [ ] Wizard contract test passes: `backend/tests/test_wizard_contract.py`
- [ ] Every wizard step has:
  - [ ] Backend endpoint (URL in `show_urls` output)
  - [ ] Frontend route registered
  - [ ] At least one test
  - [ ] Permission declaration
  - [ ] Demo/seed data path

### Subscriptions & Entitlements
- [ ] `seed_plans` command produces 3 plans (smart_start, next_level, all_access) and 17 features
- [ ] `EntitlementGate` wraps all subscription-gated pages
- [ ] `RequiresEntitlement` permission class used on restricted views
- [ ] `GET /api/v1/subscriptions/me/entitlements/` requires `IsAuthenticated` + school header
- [ ] `GET /api/v1/subscriptions/ops/<school_id>/` requires `IsAdminUser`

### Communications
- [ ] No cross-tenant message threads possible (school_id scoped on all message queries)
- [ ] No PII included in notification payloads sent to third-party providers
- [ ] Email send failures are logged (not silently swallowed)
- [ ] SMS feature properly gated via `RequiresEntitlement("comms.sms")`

### CI/CD Gates
- [ ] `backend-gate` (compile + checks + migration drift + tenant tripwire) passes
- [ ] `pytest-gate` passes
- [x] `secret-scan` passes — **2026-02-28, PR #488 #489**
- [x] `dashboards-build-gate` passes — **2026-02-28, 1974 modules, 0 errors**
- [ ] `migration-lock-gate` passes
- [ ] `contract-gate` passes
- [x] `crown-magus0-gate` passes — **2026-02-28, all 4 jobs green @ 5041c574**
- [ ] Required checks in branch protection match the list above (no bypasses)

### DB / Migrations
- [ ] `python manage.py makemigrations --check --dry-run` exits 0
- [ ] `python manage.py migrate` from zero completes without errors (tested on fresh SQLite)
- [ ] No "silent mismatch" detected (showmigrations shows all `[X]` applied)
- [ ] Downgrade policy documented: explicit "not supported for MVP; restore from backup"

---

## P2 — Operational Reliability (schedule before next release)

### Observability
- [ ] `/api/health/` returns `{status: "ok", build_sha: "<sha>"}` in production
- [ ] `/api/integrity/` returns build SHA matching the deployed tag
- [ ] Error tracking (Sentry or App Insights) is wired and receiving events
- [ ] All 5xx errors generate a trackable trace ID in response and log

### Rate Limiting & Security Headers
- [ ] `X-Frame-Options: DENY` or `SAMEORIGIN` set
- [ ] `X-Content-Type-Options: nosniff` set
- [ ] `Strict-Transport-Security` header present in production
- [ ] CSRF middleware is active and `CSRF_COOKIE_HTTPONLY = True`
- [ ] Login endpoint has brute-force protection (rate limit or lockout)

### Platform Operations
- [ ] `POST /api/platform/schools` → idempotency key prevents duplicate schools
- [ ] Provisioning job transitions: queued → running → succeeded/failed
- [ ] `ProvisioningJob.error` cleared on success
- [ ] `AuditEvent` created for every platform-level action

---

## P3 — UX / Polish (nice-to-have before GA)

- [ ] All `EntitlementGate` fallback states show useful upgrade prompt (not blank screen)
- [ ] `SubscriptionManagerPage` accessible only to platform admins
- [ ] Wizard steps show validation errors inline (not silent failure)
- [ ] Demo/seed data covers all 7 roles for Heritage school scenario

---

## Sign-off

| Role | Name | Date | Sign |
|------|------|------|------|
| Engineering Lead | | | |
| Security Reviewer | | | |
| QA | | | |
| Product Owner | | | |

**Attach before tagging release:**
- `artifacts/audit/CrownMagus0/audit-<timestamp>/SUMMARY.txt`
- `artifacts/audit/CrownMagus0/audit-<timestamp>/audit.log`
- `artifacts/audit/CrownMagus0/audit-<timestamp>/django-migrations.txt`
- `artifacts/audit/CrownMagus0/audit-<timestamp>/secret-scan.txt`
- `artifacts/audit/CrownMagus0/audit-<timestamp>/dep-python.txt`
- `artifacts/audit/CrownMagus0/audit-<timestamp>/dep-node.txt`
