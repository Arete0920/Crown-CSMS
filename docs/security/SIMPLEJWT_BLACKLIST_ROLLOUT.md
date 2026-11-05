# SimpleJWT refresh-token blacklist: controlled rollout

**Scope:** security issue #350; accepted runtime and database evidence must be recorded separately from a source merge. This document does not approve production deployment, credential disclosure, database rewrites or emergency privilege changes.

## Why the change matters

CROWN sets `ROTATE_REFRESH_TOKENS=True` and `BLACKLIST_AFTER_ROTATION=True`. Upstream SimpleJWT only blacklists a consumed refresh token when `rest_framework_simplejwt.token_blacklist` is installed and its database tables exist. Without that app, old refresh tokens remain usable until expiry. Once the app is enabled, token issuance itself may write to `token_blacklist_outstandingtoken`. Deploying code before migrating tables may break logins.

References:
- https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html
- https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html
- https://github.com/jazzband/djangorestframework-simplejwt/releases/tag/v5.5.1

## Required preflight in each actual deployment environment

1. Identify the exact deployed CROWN source SHA and currently installed SimpleJWT version. Check which Django settings module, database alias, and tenant/auth routes are active. No credentials or token values in evidence.
2. Make an approved, tested recovery point. Verify database restore can be completed; record the custodian, environment, UTC time, and restricted evidence location.
3. **Read** the `django_migrations` rows for `app='token_blacklist'` and inspect SimpleJWT 5.5.1's migration graph, especially `0013_alter_blacklistedtoken_options_and_more`. Confirm whether a locally generated `0013` predates the vendor release and whether downstream migrations depend on it. Stop and obtain a reviewed specific remediation if the graph conflicts: never blindly fake, delete, or roll back rows.
4. On a disposable database copy matching the actual starting schema, run Django's migration plan and migrations with the **candidate code**. Confirm both token tables and token indexes, then rehearse rollback and recovery. No school data or credentials in public CI.
5. Require the controlled deployment sequence to apply approved database migrations **before serving traffic with the new code**. Ensure only the intended environment is targeted and maintenance/runbook authority is recorded. Avoid adding manual production shell commands in public issue comments.
6. Run an isolated, synthetic token proof: issue a refresh, rotate once, verify old token rejected (401), and replacement token usable. Test invalid/expired tokens and rate limit behavior, exercise tenant context, inspect logs for token absence. Preserve only redacted status/case counts. Distinguish staging from production.
   On PostgreSQL, concurrently submit the same refresh token from two connections and require exactly one 200 and one 401. Row locking is database-specific: SQLite-only tests do not certify this guarantee. Inspect transactions and lock behavior under multi-worker load; no token data in output.
7. Establish retention/maintenance for `flushexpiredtokens` on an approved recurring schedule and measure outstanding-token growth. Audit DB writes and failure behavior for the new token persistence.
8. Record exact deployed build/version, schema/migration state, 401/200 contract evidence, rollout owner and rollback decision. Close #350 only after the target runtime meets all gates.

## Source acceptance

The source PR must pass exact-head Django and PostgreSQL migration/test suites, static/security CI, and protected main governance. This checklist does **not** authorize making CI fail open, deploying without migrations, or asserting CROWN is SOC 2 compliant. Keep unrelated authentication rollout #330–#333 independently governed.

## Read-only DEV migration discovery

An accepted-source checkout can run `python scripts/ops/run_dev_inquiry_migration.py
--expected-sha FULL_ACCEPTED_SHA --check-only`. The checker reuses the existing
DEV Azure/Key Vault identity validation, TLS verification, advisory lock, vendor
graph verification, and pending-plan allowlist, but **does not execute migration
commands, create tables, or deploy application code**. It reports only fixed
reason codes and bounded migration identifiers. An unreviewed blacklist plan
is an expected `BLOCKED` result and must not be overridden.

Run the existing `scripts/ops/run_dev_inquiry_migration.py` with `--check-only`
from an approved, credentialed operator environment and the exact accepted
source SHA. Do not create a new GitHub Actions workflow. The workflow
is not a migration authorization and does not prove backup/restore readiness.
After a sanitized preflight, reconcile the actual DEV migration graph and
necessary recovery point before authorizing any schema mutation. Do not
activate the blacklist app on a running deployment while tables are absent.

## Explicit reviewed DEV schema stage (separate from deployment)

The migration application stage is **manual only**. After a release candidate
has been accepted into protected main, the owner/operator must verify the actual
DEV migration history, current vendor distribution and schema, and record an
independently tested DEV recovery point. Do not infer recovery readiness from
an attestation string or a passing unit test.

Use the existing `scripts/ops/run_dev_inquiry_migration.py` runner
with `--apply-reviewed-blacklist --confirm-dev-blacklist migrate-dev-blacklist`,
the exact accepted-main SHA, and a
restricted recovery evidence reference. It reuses the existing verified Azure
DEV environment/hostname, Key Vault resolution, PostgreSQL identity/TLS,
advisory migration lock and transaction-capable Django migration command.
The runner allows **only a contiguous forward suffix** of the reviewed
SimpleJWT 5.5.1 `token_blacklist` migrations; unrelated, reverse and
unrecorded historical migration states block. It verifies the completed tables,
columns and unique constraints before reporting success. The GitHub manual
confirmation is an execution authorization, **not** independent proof that a
backup was completed or restored.

This workflow never modifies production and does not build/deploy the
blacklist-enabled application image. Keep DEV application traffic on the
previous accepted revision until schema application and independent testing
are complete. The ordinary `deploy-dev.yml` migration allowlist remains
unchanged; a failed or incomplete separate schema stage must not be bypassed.

## Existing GitHub Actions DEV-only schema execution path

The **existing** `.github/workflows/dev-blacklist-database-inventory.yml` can now
expose a separately confirmed, operator-dispatched reviewed blacklist schema
stage. This is a safer authenticated alternative to pasting database credentials
or repeatedly running migration commands from a local shell. No new workflow,
automatic database write, runtime setting change, application deployment or
production migration is introduced.

**Prerequisites before any dispatch:** (1) accepted exact `main` SHA;
(2) documented currently recoverable DEV backup and independently rehearsed
restore evidence for the target database; (3) validated installed SimpleJWT
version and vendor migration graph; (4) approval by the DEV operator to perform
a controlled migration at that exact source. The October 25 isolated restore
drill alone does not establish a current target backup; a GitHub URL is a
reference, not proof that these prerequisites were met.

From GitHub Actions on protected `main`, select the existing *DEV Blacklist
Database Inventory (read-only)* workflow, and request only:
- `expected_sha`: current complete protected-main commit SHA;
- `apply_reviewed_blacklist`: true (leave support and legacy flags false);
- `confirm_dev_blacklist`: `migrate-dev-blacklist`;
- `dev_recovery_receipt`: the current DEV recovery evidence URL in this repository,
  without secret data; **INDEPENDENT_REVIEW_REQUIRED** before dispatch;
- `inspect_migration_plan`: false.

The job checks that exactly one schema mode is selected and that the correct
typed confirmation and recovery-reference form are present **before Azure
login**. It then requires the checked-out source to be the unchanged protected
main SHA, validates source/vendor and tenant/database guards in the existing
runner, uses PostgreSQL locking, applies only the reviewed contiguous
SimpleJWT blacklist migration suffix, and verifies the resulting schema.
This is a bounded schema mutation, not a read-only job. A syntactically valid
recovery URL must never be treated as independent proof of recoverability.
Preserve the sanitized Actions result, read back the actual schema, and test
real PostgreSQL concurrent token replay before changing any hosted settings.

**Do not set `CROWN_SIMPLEJWT_BLACKLIST_ENABLED=true` in DEV until all post-stage
requirements pass.** Do not enable production as a consequence of this DEV
job. The ordinary non-stage inventory remains read-only.

## Safe two-stage application activation

The new `CROWN_SIMPLEJWT_BLACKLIST_ENABLED` application setting defaults to
`false`. Merging a reviewed source revision alone must not load the blacklist
app, create schema tables, or require blacklist tables during login/refresh.
Until the actual deployment's schema is verified and this setting is `true`,
the ordinary SimpleJWT serializer retains the pre-rollout rotation behavior;
**a returned rotated token is not yet proof of revocation**.

1. Accept reviewed source through the existing protected CI without activating
   the setting in any hosted environment.
2. Use the accepted-main SHA in the read-only DEV preflight. The preflight
   temporarily enables the blacklist app **inside the isolated migration
   process only**; it never changes App Service settings.
3. Reconcile the recorded migration history and actual tables; verify an
   approved, tested DEV database recovery point before any schema action.
4. Run the separate DEV-only reviewed migration job with explicit authorization.
   The temporary app enablement is confined to that migration runner.
5. Verify the full vendor migration chain, required tables/constraints and
   actual PostgreSQL concurrent 200/401 replay behavior against the target
   database. Independently record exact accepted/deployed source identity.
6. Only after these checks may the designated operator set
   `CROWN_SIMPLEJWT_BLACKLIST_ENABLED=true` on the intended DEV runtime and
   execute the hosted acceptance suite. Activation is a separate operational
   step, not an automatic side effect of this PR. Confirm that production
   remains disabled until its own migration/recovery evidence and approval.

If any step fails, leave the setting disabled and do not claim the security
finding resolved. The legacy Crown-signed refresh endpoint is separately
tracked in #372 and remains outside the SimpleJWT blacklist.

No additional workflow is permitted by CROWN's canonical workflow inventory.
The reviewed runner is an operator-controlled tool, not an automatic deploy.
