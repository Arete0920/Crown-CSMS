# Demo account credential and tenant-reset policy

The Heritage evaluator sandbox is passwordless. Its role-scoped sessions are
not created by `reset_demo_passwords`, and no public demo credential list is
permitted.

The legacy `seed_demo_school` and `reset_demo_passwords` management commands
use `CROWN_DEMO_PASSWORD` only when it is explicitly configured and meets
minimum length and formatting rules (16-256 characters, no control characters
or surrounding whitespace). The value must be supplied through a protected
environment or secret store, not committed to Git.

When the setting is absent, `seed_demo_school` creates accounts with **unusable
passwords**. On a repeat run it disables previously usable passwords for the
named fixture accounts and removes any stale superuser grant.

The reset command requires an explicit `--school-id` (or an explicit
`CROWN_DEMO_SCHOOL_ID` environment value), verifies the selected school's
name, and refuses cross-school or identity-mismatched usernames **before**
updating any accounts. It never picks the first school in the database.

Example local-only reset:

```powershell
$env:CROWN_DEMO_PASSWORD = "<strong-secret-from-a-secret-manager>"
python backend/manage.py reset_demo_passwords --school-id "<Heritage-demo-UUID>"
```

This is not permission to use either command on a production customer
database. Destructive seed/reset entrypoints require additional isolation
controls and must be reviewed separately.

The credential and tenant-safety regressions live in
`backend/core/tests/test_demo_credential_safety.py`.
