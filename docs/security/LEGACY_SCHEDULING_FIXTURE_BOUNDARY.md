# Legacy scheduling fixture boundary

The legacy `backend/scripts/seed_scheduling.py` previously iterated through
every current academic year. It now permits writes only for one explicitly
selected **Heritage Christian Academy** school with exactly one current year
in an isolated single-school local/test SQLite database.

It shares the hosted/production/SQLite restrictions accepted for legacy
household and finance fixtures in PR #370, but **requires a separate scheduling
opt-in**; finance opt-in never authorizes scheduling seeding.

## Explicit operator authorization

In an already isolated local SQLite test database containing exactly one
Heritage school, explicitly supply that *existing* school's UUID:

```powershell
$env:CROWN_ENV = "local"
$env:CROWN_ALLOW_LEGACY_SCHEDULING_SEED = "true"
$env:CROWN_LEGACY_SCHEDULING_SCHOOL_ID = "<existing-Heritage-demo-UUID>"
cd backend
python scripts/seed_scheduling.py
```

The command rejects missing or malformed UUIDs, a non-Heritage or absent school,
multiple schools, zero or multiple current Heritage academic years, production
labels, Azure/hosted indicators, absent opt-in, and non-SQLite engines. It
performs tenant/academic-year checks before writes and executes the master-data
updates as one transaction. It retains deterministic terms, courses, section
IDs, and existing roster non-inference.

## Heritage workflow and PostgreSQL compatibility

- `seed_heritage_realism_pack` invokes the legacy household and scheduling
  scripts. Existing wrappers must not assume it can run on PostgreSQL or without
  operator opt-in and an explicitly selected Heritage UUID.
- PR #382 removes this incompatible legacy seed invocation from the PostgreSQL
  finance certification job, retaining a separate school-scoped canonical
  payment/integrity test. The PostgreSQL job must not bypass this restriction.
- Historical `scripts/ops/PRE_DEMO_RESET_AND_SEED.ps1` performs a database
  **flush** before the legacy seed commands. Its existing DB_HOST check does
  not establish the effective Django DATABASE_URL/SQLite isolation. Do not run
  that destructive wrapper until it has been separately audited and secured.
- This PR does **not** certify a hosted Heritage demonstration database or
  safely authorize legacy demo resets and student-record creation.

The regression tests exercise successful isolated Heritage seeding, idempotent
replay, active-term reuse, atomic rollback, authorization and tenant rejection,
hosted/production markers, and PostgreSQL exclusion. Tests use disposable
pytest databases; no live school or customer database should be used.

Rollback: revert the bounded changes, never relax the safety guard to let
legacy scripts access customer, hosted, or PostgreSQL databases.
