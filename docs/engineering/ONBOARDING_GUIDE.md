# Crown Engineering Onboarding Guide

Welcome to Crown. This doc gets you from zero to productive in one day.

---

## Repo Setup (30 minutes)

```powershell
# 1. Clone
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026

# 2. Create virtual environment at repo root
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Install frontend dependencies
cd frontend/dashboards
npm install
cd ../..

# 5. Configure local secrets
cp local.secrets.ps1.example local.secrets.ps1
# Edit local.secrets.ps1 with your dev credentials

# 6. Run migrations
& ".venv\Scripts\python.exe" backend\manage.py migrate

# 7. Start backend dev server
& ".venv\Scripts\python.exe" backend\manage.py runserver 127.0.0.1:8000 --noreload

# 8. Start frontend dev server (separate terminal)
cd frontend/dashboards
npm run dev
```

---

## Branch Strategy

| Branch | Purpose | Protection |
|---|---|---|
| `main` | Production source of truth | Protected: 1 approval + all CI checks |
| `feature/<name>` | All new work | Open |
| `hotfix/<name>` | Critical prod fixes | Requires senior approval |
| `chore/<name>` | Non-functional changes (deps, docs, refactors) | Open |

**Never push directly to `main`.**

---

## Git Commit Convention

```
<type>: <short description>

Types:
  feat:    New feature
  fix:     Bug fix
  chore:   Non-functional (deps, docs, CI)
  test:    Test-only changes
  refac:   Refactor (no behaviour change)
  perf:    Performance improvement
```

---

## CI Requirements

Every PR to `main` must pass:
- `pytest` (all backend tests)
- `dependency-scan` (safety + pip-audit + npm audit)
- `eslint` (frontend linting)
- Tenant gate must not be bypassed
- No `ALLOW_DEMO_ROLE_HEADER = True` ever committed

---

## Absolute Rules

1. **Never bypass tenant enforcement.** Every endpoint calls `get_request_school_id()`.
2. **Never disable audit logging.** `AuditMiddleware` is always active.
3. **No silent exception catching.** Log exceptions at WARNING or above; never swallow.
4. **No cross-tenant queries.** Every queryset is scoped by `school_id`.
5. **Never add fields to `ledger.Payment`.** It has `ImmutableMoneyMixin` — use a related model.
6. **`ALLOW_DEMO_ROLE_HEADER = False` is unconditional.** Do not change this.
7. **No new models without migrations.** Run `makemigrations` before committing.
8. **No new Django apps without adding to `INSTALLED_APPS`.** Check `settings.py`.

---

## Key Files

| File | Purpose |
|---|---|
| `backend/crown_api/settings.py` | All Django settings |
| `backend/crown_api/api_urls.py` | Primary API URL registration |
| `backend/crown_api/urls.py` | Root URL conf |
| `backend/core/permissions.py` | RBAC permission engine |
| `backend/households/scoping.py` | `get_request_school_id()` |
| `backend/ledger/models.py` | Immutable payment spine |
| `docs/architecture/SYSTEM_OVERVIEW.md` | System architecture map |
| `FILE_INDEX.md` | Full file index |

---

## Testing

```powershell
# Run all backend tests
& ".venv\Scripts\python.exe" -m pytest backend/ -v

# Run a specific test file
& ".venv\Scripts\python.exe" -m pytest backend/ledger/tests/test_revenue_integrity.py -v

# Run frontend linting
cd frontend/dashboards
npx eslint src/
```

---

## Getting Help

- Architecture questions → `docs/architecture/SYSTEM_OVERVIEW.md`
- API spec → `docs/DIRECTOR_ACTIONS_API.md`
- Financial Aid pattern (gold standard) → `docs/REFERENCE_MODULE_PATTERN.md`
- Integration guide → `INTEGRATION_GUIDE.md`
- If stuck → open a support ticket at `/api/v1/support/tickets/`
