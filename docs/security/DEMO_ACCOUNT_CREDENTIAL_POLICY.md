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
$env:CROWN_ENV = "local"
$env:CROWN_DEMO_PASSWORD = "<strong-secret-from-a-secret-manager>"
python backend/manage.py reset_demo_passwords --school-id "<Heritage-demo-UUID>"
```

Both legacy management commands now require an explicit `CROWN_ENV=local`
(or `test`) designation and a configured SQLite database. Unset or
unrecognized environments, PostgreSQL, explicit production labels, and
hosted/Azure runtime markers are rejected before any data mutation. This is
intentionally stricter than the separately governed evaluator-facing Heritage
sandbox bootstrap.

Destructive `seed_demo_school --wipe` additionally requires the exact Heritage
school name, `--confirm-demo-wipe`, `CROWN_ALLOW_DEMO_WIPE=true`,
`CROWN_ENV=local` (or `test`), and a configured SQLite database. Do not
enable these flags against a customer database. The local reset ceremony must
set both confirmations explicitly.

The credential and tenant-safety regressions live in
`backend/core/tests/test_demo_credential_safety.py`.

The legacy `seed_heritage_realism_pack` orchestrator additionally requires
`CROWN_ALLOW_LEGACY_FIXTURE_SEED=true` on isolated local/test SQLite.
Its preflight checks the same hosted/database prohibition and this explicit
fixture authorization **before** calling `seed_demo_school`. Denial must not
leave partially seeded school records. Legacy scheduling has its own explicit
school-binding authorization; the fixture flag does not override it.

For the **full local-only realism pack**, explicitly set
`CROWN_ALLOW_LEGACY_FIXTURE_SEED=true` and
`CROWN_ALLOW_LEGACY_SCHEDULING_SEED=true`, in addition to the
local/test SQLite environment. The orchestrator checks these opt-ins, the
legacy household/person directory, and the absence of unrelated schools
**before seeding**. It temporarily binds the verified sole Heritage UUID
to `CROWN_LEGACY_SCHEDULING_SCHOOL_ID` while invoking the scheduling
script and restores the previous environment afterward. A conflicting
preselected UUID is rejected. Standalone legacy scheduling still requires
the operator to supply its explicit school UUID.
