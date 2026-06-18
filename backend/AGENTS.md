# Backend Agent Contract

This contract applies to `backend/**`.

## Scope Discipline

Backend changes must be tied to a named work order, module, wizard, dashboard, or defect.

Do not alter authentication, RBAC, tenant isolation, migrations, settings, package files, or accounting logic unless explicitly scoped.

## Required Backend Proof

For backend code changes, run the narrowest relevant tests first, then broader checks as required:

```powershell
python backend/manage.py check
python -m pytest <focused-test-path> -v --nomigrations --tb=short
```

If the repository uses a virtual environment path in the active worktree, use that interpreter consistently.

## Tenant And School Isolation

Any model, API, service, or query that reads tenant-scoped data must prove isolation through tests or explicit evidence.

Never create cross-tenant queries. Never bypass school or tenant filters for convenience.

## API And Permission Work

When adding or changing APIs, prove:

- unauthenticated behavior;
- unauthorized/forbidden behavior;
- allowed role behavior;
- tenant/school scoping;
- audit/event behavior where applicable.

## Accounting Safety

Never use float types for money. Use decimal-safe patterns. Never weaken ledger immutability, auditability, reconciliation, or tenant isolation.

## Migrations

Do not auto-generate or commit migrations unless migration work is explicitly in scope and reviewed.

## Closeout

Report:

- changed backend files;
- commands run;
- exact test output path;
- remaining backend risks;
- whether independent review is required.
