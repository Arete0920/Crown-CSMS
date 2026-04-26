# Crown2026 Build Rules & Architecture Guidelines

**Version**: 1.0 | **Date**: January 3, 2026 | **Status**: Active

This document establishes non-negotiable rules for developing, testing, and deploying the Crown school management system. These rules prevent recurring failures and maintain code quality.

---

## 1. Directory & File Discipline

### 1.1 Folder Structure
```
Crown2026/
├── backend/                    # Django app root
│   ├── manage.py              # Django management (DO NOT duplicate in root)
│   ├── venv/                  # Python virtual environment
│   ├── crown_api/             # Django settings + URL routing
│   ├── core/                  # Core models (User, School, Family, Student, etc.)
│   ├── aid/                   # Aid management (Applications, Awards, Documents)
│   ├── finance/               # Finance tracking (Chart of Accounts, Ledger)
│   └── db.sqlite3             # Development database
├── docs/                       # Documentation (BUILD_RULES.md, API specs, etc.)
└── scripts/                    # Utility scripts (if needed)
```

### 1.2 File Naming Conventions
- **Models**: Singular, clear names (`User`, `AidApplication`, `LedgerEntry`)
- **Views**: `{domain}_views.py` (e.g., `director_views.py` for API endpoints)
- **Management Commands**: `backend/core/management/commands/{command_name}.py`
- **Test Files**: `test_{domain}.py` (e.g., `test_director_apis.py`)
- **Database Files**: Always in `backend/` root, never in subdirectories

### 1.3 Absolute Path Rule (CRITICAL)
- **Terminal commands MUST use absolute paths** when referencing Python, manage.py, or project files
- Relative paths work inconsistently across Windows PowerShell terminal context changes
- **GOOD**: `cd "c:\Users\JMega\OneDrive\Desktop\Crown2026\backend"; .\venv\Scripts\python.exe manage.py runserver`
- **BAD**: `python manage.py runserver` (uses wrong Python interpreter)

---

## 2. Python Virtual Environment Rules

### 2.1 Activation & Execution
- **Always use explicit venv Python**, never rely on activated shell environment
- **CORRECT**: `.\venv\Scripts\python.exe` (absolute path to venv Python)
- **WRONG**: `python` (might use system Python, not venv)
- **Package Installation**: `.\venv\Scripts\python.exe -m pip install {package}`

### 2.2 Dependencies
- **Django 6.0** (LTS)
- **Django REST Framework 3.16.1** (API serialization)
- **python-dotenv** (environment variable management)
- Maintain `requirements.txt` or `Pipfile` for reproducibility

### 2.3 Environment Variables
- **Development**: Use hardcoded values or `.env` file (git-ignored)
- **Production**: Use OS environment variables via `os.getenv()`
- **Key Variables**:
  - `CROWN_DEV_OPEN_API`: Set to `"1"` to enable unauthenticated director API access (dev only)
  - `DJANGO_SETTINGS_MODULE`: Always `crown_api.settings`
  - `PYTHONUNBUFFERED`: Set to `"1"` for real-time log output

---

## 3. Django Server Rules

### 3.1 Server Startup (REQUIRED COMMAND)
```powershell
cd "c:\Users\JMega\OneDrive\Desktop\Crown2026\backend"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

**Why `--noreload`?**
- Prevents double-initialization of Django app registry
- Eliminates `AppRegistryNotReady` errors
- More stable for development on Windows

**Why `127.0.0.1:8000` not `0.0.0.0:8000`?**
- Localhost-only binding is safer for development
- Matches production security model (reverse proxy handles external access)

### 3.2 Pre-Server Checklist
1. **Kill stray Python processes**: `Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force`
2. **Clear Python cache**: Delete all `__pycache__` directories and `.pyc` files
3. **Run Django check**: `.\venv\Scripts\python.exe manage.py check` (must return "0 issues")
4. **Verify database**: `db.sqlite3` exists and migrations are applied
5. **Start server**: Use exact command above

### 3.3 Database Migrations
- **Always run migrations after code changes**: `.\venv\Scripts\python.exe manage.py migrate`
- **Never modify migration files manually** after they've been applied
- **Create migrations for schema changes**: `.\venv\Scripts\python.exe manage.py makemigrations`
- **Verify migrations**: `.\venv\Scripts\python.exe manage.py showmigrations`

### 3.4 Database Seeding
- **Seed command**: `.\venv\Scripts\python.exe manage.py seed_demo_school --wipe`
- **Fresh database**: `rm db.sqlite3; .\venv\Scripts\python.exe manage.py migrate; .\venv\Scripts\python.exe manage.py seed_demo_school --wipe`
- **Seed produces**: 300 students, 180 families, 63 aid applications, 115 awards with realistic workflow distribution
- **Demo admin credentials**: `head@crown-demo.local` / `demo1234` (only exists after seeding)

### 3.5 Seed Command Idempotency Rules (CRITICAL)

**Context**: Proof Ceremony CI runs `seed_demo_school --wipe` repeatedly, exposing non-idempotent patterns that fail under test conditions.

#### 3.5.1 Mandatory Patterns
1. **Use `get_or_create()` for unique constraints**
   - ❌ **WRONG**: `Guardian.objects.create(school=school, email=email, ...)`
   - ✅ **CORRECT**: `Guardian.objects.get_or_create(school=school, email=email, defaults={...})`
   - **Why**: Random email generation + `.create()` = UniqueViolation on reruns

2. **Use `get_or_create()` keyed on natural keys**
   - Models with unique constraints must be created idempotently
   - Key on `(school, name)`, `(school, email)`, `(school, code)`, etc. depending on model
   - Pass variable data via `defaults={}` parameter

3. **Delete in FK-safe order**
   - ❌ **WRONG**: Delete `UserAccount` before `AidAuditEvent` (protected FK fails)
   - ✅ **CORRECT**: Delete `AidAuditEvent` (child) before `UserAccount` (parent)
   - **Pattern**: Delete referencing objects BEFORE referenced objects

#### 3.5.2 Example: Guardian Seed (Fixed in PR #40)
```python
# BEFORE (broken)
Guardian.objects.create(
    school=school,
    family=fam,
    email=f"{last.lower()}.{random.randint(1000,9999)}@demo.local",
    ...
)

# AFTER (idempotent)
email = f"{last.lower()}.{random.randint(1000,9999)}@demo.local"
Guardian.objects.get_or_create(
    school=school,
    email=email,  # Unique constraint key
    defaults={
        "family": fam,
        "first_name": random.choice(FIRST_NAMES),
        ...
    }
)
```

#### 3.5.3 Wipe Order for `seed_demo_school --wipe`
Correct deletion cascade (from commit f81b4be0):
```python
def _wipe_school(self, school: School):
    from financial_aid.models import AidAuditEvent

    # 1. Delete audit events (reference UserAccount via actor_user_id)
    user_ids = list(UserAccount.objects.filter(school=school).values_list('id', flat=True))
    AidAuditEvent.objects.filter(school_id=school.id).delete()
    if user_ids:
        AidAuditEvent.objects.filter(actor_user_id__in=user_ids).delete()

    # 2. Delete school data (now safe, no protected FKs)
    AidAward.objects.filter(school=school).delete()
    AidApplication.objects.filter(school=school).delete()
    LedgerEntry.objects.filter(school=school).delete()
    StudentTuition.objects.filter(school=school).delete()
    TuitionPlan.objects.filter(school=school).delete()
    JournalBatch.objects.filter(school=school).delete()
    ChartAccount.objects.filter(school=school).delete()
    Enrollment.objects.filter(school=school).delete()
    Student.objects.filter(school=school).delete()
    Guardian.objects.filter(school=school).delete()
    Family.objects.filter(school=school).delete()
    UserRole.objects.filter(school=school).delete()
    UserAccount.objects.filter(school=school).delete()  # Now safe
    Staff.objects.filter(school=school).delete()
    GradeLevel.objects.filter(school=school).delete()
    AcademicYear.objects.filter(school=school).delete()
```

#### 3.5.4 Testing Seed Idempotency
Seed commands **must** pass this test:
```python
# Run seed twice in sequence
call_command("seed_demo_school", "--wipe")
call_command("seed_demo_school", "--wipe")  # Must not crash
```

If this fails with UniqueViolation or ProtectedError, fix the seed command before pushing.

#### 3.5.5 When Adding New Seed Commands
1. Use `get_or_create()` for all models with unique constraints
2. Test double-run locally before committing
3. Add tests verifying idempotency (like `test_seed_category_weights_command.py`)
4. Document unique keys in command docstring

**Root Cause Reference**: PR #40 commit f81b4be0 fixed proof-ceremony failures caused by non-idempotent Guardian creation.

---

## 4. API Endpoint Rules

### 4.1 Director APIs (Read-Only Summaries)
All director endpoints are located in `backend/crown_api/director_views.py`:

#### Aid Summary
```
GET /api/director/aid/summary/?school_id={uuid}&academic_year_id={uuid}
```
Returns: Applications (total, submitted, needs_info, under_review, approved, denied), Awards (total, offered, accepted, posted, total_cents), Documents (missing_count)

#### Finance Summary
```
GET /api/director/finance/summary/?school_id={uuid}&academic_year_id={uuid}
```
Returns: Tuition (students_billed, gross_cents), Aid (total_awarded_cents, total_posted_cents), Ledger (net_receivables, debits, credits)

#### Registrar Summary
```
GET /api/director/registrar/summary/?school_id={uuid}&academic_year_id={uuid}
```
Returns: Enrollment (total_students, by_grade distribution), Families (total_families)

### 4.2 Authentication & Authorization
- **Function**: `crown_director_allowed(request)` in `director_views.py`
- **Checks** (in order):
  1. Dev toggle: `CROWN_DEV_OPEN_API` setting (True = allow all)
  2. Superuser: `request.user.is_superuser` (always allow)
  3. Role-based: `UserRole.objects.filter(user=user, role_code__in=ALLOWED_ROLE_CODES)`
- **Dev toggle** (PRODUCTION WARNING): Currently hardcoded `CROWN_DEV_OPEN_API = True` in `settings.py`
  - **TODO**: Switch to `os.getenv("CROWN_DEV_OPEN_API", "0") == "1"` before production
  - Never leave toggle always-on in production

### 4.3 API Response Format
All responses return JSON with clean field names:
```json
{
  "applications": {
    "total": 63,
    "submitted": 53,
    "needs_info": 7,
    "under_review": 3,
    "approved": 0,
    "denied": 0
  },
  "awards": {
    "total_awards": 115,
    "offered_not_accepted": 11,
    "accepted_not_posted": 11,
    "posted_to_ledger": 93,
    "total_awarded_cents": 1250000
  }
}
```

---

## 5. Git & Version Control Rules

### 5.1 Commit Discipline
- **Commit early & often**: After each working feature, not after massive refactors
- **Commit message format**: `{type}: {description}`
  - Types: `feat`, `fix`, `refactor`, `docs`, `chore`
  - Examples: `feat: director API endpoints`, `fix: User model null school`, `chore: clean junk files`
- **Never commit junk files**: Debug scripts, test outputs, IDE files
- **Before committing**: Run `git status` and `git diff` to audit changes

### 5.2 Branch Policy
- **Active branch**: `recovery` (recovery from initial setup failures)
- **Commit & push frequently**: Don't let commits pile up
- **Before major refactors**: Create a checkpoint commit so you can revert if needed

### 5.3 Code Review Checklist
Before committing:
```
□ Feature works end-to-end (server starts, no errors)
□ No debug code left in
□ No hardcoded credentials (except dev demo accounts)
□ Models properly defined (all fields, constraints, __str__)
□ Admin registration if needed
□ Migrations created if schema changed
□ API responses return clean JSON
□ Tests pass (or test file created)
□ git diff output reviewed
```

---

## 6. Data Model Rules

### 6.1 Core Models (backend/core/models.py)
- **User model** (`UserAccount`): Extends Django AbstractUser, has `school` (FK), `staff` (OneToOne), `guardian` (OneToOne)
- **School**: Central entity, has students, families, staff, enrollments, tuition, aid data
- **Family**: Groups parents/guardians; multiple families per student possible
- **Student**: Has enrollments, tuition records, aid applications
- **Staff**: School employees with roles (director, teacher, etc.)
- **UserRole**: Links users to schools with role codes (AID_DIRECTOR, FINANCE_DIRECTOR, REGISTRAR, HEAD_OF_SCHOOL, etc.)

### 6.2 Null Handling
- **CRITICAL**: User model `__str__()` must handle `None` school:
  ```python
  def __str__(self):
      school_name = self.school.name if self.school else "No School"
      return f"{self.email} ({school_name})"
  ```
  Without this, unrelated users crash the admin list view.

### 6.3 Audit Trail Pattern
- **Every transaction model** should have `created_at`, `updated_at` timestamps
- **Financial records** should be immutable (created once, never modified)
- **Use reversals instead of updates** for ledger corrections (debit/credit pairs)

---

## 7. Testing Rules

### 7.1 Test File Location & Naming
- Location: `backend/{app}/tests.py` or `backend/{app}/test_{feature}.py`
- Run tests: `.\venv\Scripts\python.exe manage.py test`
- Coverage target: 80%+ (APIs, models, edge cases)

### 7.2 Test Database
- Tests automatically use in-memory SQLite (`test_*.py` creates fresh DB per test)
- No cleanup needed; test DB is discarded after test completes
- Run migrations in test setup: `call_command('migrate')`

### 7.3 API Testing
- Use DRF's `APITestCase` for endpoint testing
- Test authenticated + unauthenticated requests
- Verify response status codes (200, 403, 400)
- Validate JSON response schema matches spec

---

## 8. Production Readiness Checklist

Before deploying to production:

```
Security:
□ CROWN_DEV_OPEN_API switched to os.getenv() (default False)
□ All hardcoded passwords removed
□ Django DEBUG = False
□ ALLOWED_HOSTS configured for domain
□ CSRF protection enabled
□ HTTPS enforced (SSL certificate)
□ Secret key rotated & stored in env var

Database:
□ PostgreSQL (not SQLite) in production
□ Database backups automated
□ Migrations tested on production-like data
□ Indexes created on frequently queried fields

Performance:
□ Database connection pooling configured
□ Static files collected to CDN
□ Caching configured (Redis or Memcached)
□ Query optimization (select_related, prefetch_related)
□ Load testing completed (>100 concurrent users)

Monitoring:
□ Error tracking (Sentry or similar)
□ Log aggregation configured
□ Health check endpoint available
□ Database monitoring (slow queries)
□ API rate limiting configured

Deployment:
□ Docker image tested locally
□ Kubernetes manifests validated
□ Zero-downtime deployment strategy tested
□ Rollback procedure documented
□ Runbook created for common issues
```

---

## 9. Troubleshooting Guide

### Problem: `ModuleNotFoundError: No module named 'django'`
**Cause**: Using system Python instead of venv Python
**Fix**: Use `.\venv\Scripts\python.exe` not `python`

### Problem: `AppRegistryNotReady: Apps aren't loaded yet`
**Cause**: Importing models before Django loads app registry
**Fix**: Use lazy imports in URLconf or add `--noreload` flag to runserver

### Problem: Server hangs or crashes silently
**Cause**: Stray Python process from previous run still bound to port 8000
**Fix**: Kill all Python: `Get-Process python | Stop-Process -Force`

### Problem: Admin login credentials don't work
**Cause**: User not created with `is_staff=True` and `is_superuser=True`
**Fix**: Re-seed database: `.\venv\Scripts\python.exe manage.py seed_demo_school --wipe`

### Problem: Database migrations conflict
**Cause**: Multiple developers created migrations with same name
**Fix**: Revert conflicts manually, squash migrations: `.\venv\Scripts\python.exe manage.py squashmigrations`

### Problem: `User matching query does not exist` on login
**Cause**: User account deleted or email changed after initial seeding
**Fix**: Check admin: http://127.0.0.1:8000/admin/core/useraccount/

---

## 10. Code Style & Standards

### 10.1 Python Style (PEP 8)
- Line length: 100 characters
- Use 4-space indentation
- Imports: Standard library, third-party, local (in that order)
- Type hints: Use for function signatures (Python 3.9+)

### 10.2 Django Code Style
- Model names: Singular (User, AidApplication, not Users, Applications)
- Field names: snake_case, descriptive (not `u` or `a`)
- Queryset methods: Use `select_related()` and `prefetch_related()` to prevent N+1 queries
- Admin classes: Register all models, use `list_display`, `search_fields`, `list_filter`

### 10.3 API Response Style
- Field names: snake_case (not camelCase)
- Timestamps: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Amounts: Always in cents (integer), never float
- Enums: String values (not numeric) for readability

### 10.4 Comments & Documentation
- Docstrings: Use for all models, views, and functions
- Inline comments: Explain "why", not "what" (code should be self-documenting for "what")
- API docs: Keep updated in docs/API.md when endpoints change

---

## 11. Known Limitations & TODO Items

### 11.1 Current Limitations
- **Authentication**: Dev toggle always-open (`CROWN_DEV_OPEN_API = True`), needs env var switch
- **Database**: SQLite (development only), must migrate to PostgreSQL for production
- **Multi-tenancy**: Single school per database, multi-school support would require refactor
- **Async**: All operations synchronous, no background job queue (Celery not integrated)

### 11.2 TODO Before Production
- [ ] Switch CROWN_DEV_OPEN_API to environment variable with default False
- [ ] Implement actual role-based access control (re-enable UserRole checks)
- [ ] Add student portal (currently admin-only)
- [ ] Implement full audit logging (who changed what, when)
- [ ] Add email notifications (aid awards, tuition bills)
- [ ] Implement payment processing integration
- [ ] Add document upload & storage (S3 or similar)
- [ ] Create comprehensive API documentation (Swagger/OpenAPI)

---

## 12. References

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Crown2026 Repository](https://github.com/tcmegahan/Crown2026)
- [Crown2026 API Spec](./API.md) (to be created)

---

**Last Updated**: January 3, 2026
**Maintained By**: Development Team
**Questions?** Check server logs first: http://127.0.0.1:8000/ → check terminal for error messages

---

## CORE COMMANDMENTS

Crown2026 Build Rules (Speed + Stability)

One repo. One workspace. No sub-projects.

Django backend is authoritative.

No new dependencies unless explicitly approved.

No changes to auth, roles, or finance without tests or explicit sign-off.

No speculative refactors.

Every change ends with: git status → git diff → commit → push.

If something breaks, we fix forward or revert — never stack guesses.

Commit this file alone right after the main push.

This is as much for future you as it is for Copilot.
