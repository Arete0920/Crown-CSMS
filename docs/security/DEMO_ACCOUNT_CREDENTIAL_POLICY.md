# Demo account credential and tenant-reset policy

The Heritage evaluator sandbox is passwordless. Its role-scoped sessions are
not created by `reset_demo_passwords`, and no public demo credential list is
permitted.

The legacy management commands use six distinct per-account secrets:
`CROWN_DEMO_HEAD_PASSWORD`, `CROWN_DEMO_FINANCE_PASSWORD`,
`CROWN_DEMO_AID_PASSWORD`, `CROWN_DEMO_REGISTRAR_PASSWORD`,
`CROWN_DEMO_TEACHER_PASSWORD`, and `CROWN_DEMO_PARENT_PASSWORD`.
Each supplied secret must be 16-256 characters, properly formatted and distinct.
Do not commit these values to Git. `CROWN_DEMO_PASSWORD` is a retired shared
credential and is not accepted for these legacy school accounts.

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
\# Set all six distinct CROWN_DEMO_*_PASSWORD variables from a protected secret manager
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

## Additional operational restrictions

The legacy school seed command is Heritage-only even without `--wipe` and refuses
mixed-school and duplicate-Heritage databases. This is stronger than requiring
SQLite alone, which does not establish an isolated dataset. Destructive
`--wipe` additionally requires `--school-id <existing Heritage UUID>`;
name-only targeting is not sufficient. A cross-school financial-aid audit
reference blocks the wipe rather than deleting the other school's history.

The local `scripts/ops/runseed.ps1` ceremony now requires explicit
`-HeritageSchoolId` and `-ConfirmDemoWipe`; the local smoke tool also
requires `-HeritageSchoolId`. Seeded directors are not Django staff users or
superusers. These are source restrictions and must pass new-head CI plus an
isolated end-to-end demonstration before operational acceptance.

**Credential migration:** The legacy shared variable `CROWN_DEMO_PASSWORD` no
longer provisions these accounts. The explicit reset requires all six distinct
account secrets and refuses incomplete, weak, malformed, or repeated values
before database writes. Where credentials are absent, seeding disables password
login. This change requires exact-head test acceptance and a disposable Heritage
rehearsal before being treated as operationally certified.

## Retired full-database reset wrapper

`scripts/ops/PRE_DEMO_RESET_AND_SEED.ps1` is intentionally disabled.
Its historical `manage.py flush --noinput` could erase all records from an
operator-selected database; host-name checks alone were not sufficient.

`tools/demo_reset_smoke.ps1` now requires explicit operator-provided
`CROWN_ENV=local`, `CROWN_ALLOW_DEMO_WIPE=true`, an isolated SQLite
`DATABASE_URL`, an exact `-HeritageSchoolId` UUID, and the
`-ConfirmDemoWipe` switch. It refuses hosted/production environment markers.
It does not manufacture its own wipe authorization. The backend still checks
single-school ownership and rejects cross-school activity independently.
No customer or production database should ever be used for this procedure.
