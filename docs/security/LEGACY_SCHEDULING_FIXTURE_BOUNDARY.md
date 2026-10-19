# Legacy scheduling seed scope

The old `backend/scripts/seed_scheduling.py` script previously processed
**every current academic year** in its database. It is now restricted to one
explicitly selected Heritage Christian Academy school on a single-school,
isolated local/test SQLite database.

Required environment settings:
```powershell
$env:CROWN_ENV = "local"
$env:CROWN_ALLOW_LEGACY_SCHEDULING_SEED = "true"
$env:CROWN_LEGACY_SCHEDULING_SCHOOL_ID = "<existing-Heritage-demo-UUID>"
python backend/scripts/seed_scheduling.py
```

The script refuses hosting/Azure markers, production environment labels,
mixed-school databases, a missing/incorrect school UUID, or multiple current
Heritage academic years. It retains existing deterministic section IDs, term
rules and no-inferred-roster behavior. It does not modify customer school
schedules or historical migrations. Run governed CI before merging.
