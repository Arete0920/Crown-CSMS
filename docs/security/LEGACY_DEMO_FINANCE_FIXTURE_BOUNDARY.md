# Legacy household and finance fixture isolation

The older `crown_api` household, person, invoice, and payment models are not
canonically school-tenant-keyed. Their data-seeding scripts therefore must
not operate against a hosted, production, or shared database.

`seed_households.py` and `seed_finance.py` now require all of:
- `CROWN_ENV=local` (or `test`);
- `CROWN_ALLOW_LEGACY_FIXTURE_SEED=true`;
- SQLite as the configured default database engine;
- no Azure/hosted runtime markers and no conflicting production labels;
- only the two known fictional Hartwell and Carter household fixtures in the
  legacy directory (any unrelated household/person blocks execution).

The scripts refuse existing invoice/payment records outside the fixed fixture
references. They never enumerate or invoice arbitrary customer households.
The names, phone numbers, and `heritage.example.org` emails are synthetic;
no notifications, bank transfers or external payments should be initiated.

To run on a fresh **isolated** local SQLite database:

```powershell
$env:CROWN_ENV = "local"
$env:CROWN_ALLOW_LEGACY_FIXTURE_SEED = "true"
python backend/scripts/seed_households.py
python backend/scripts/seed_finance.py
```

This is a legacy proof capability only, not school onboarding or production
billing. For current CROWN application operation, use the canonical,
school-scoped finance, admissions and family services.

No production migrations or API contracts are changed. Existing old local
fixture databases containing unrelated records must be reset independently
rather than silently normalized in place.
