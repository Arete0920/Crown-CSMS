# WO-1387 — Schema Cutover and Web Non-Mutation

Status: ACTIVE IMPLEMENTATION LANE
Related: #1387, #1270, #1275, #1374

## Objective

Make the controlled, locked migration stage the only production schema-mutation authority and prove that ordinary web startup cannot apply migrations.

## Verified starting state

- `entrypoint.sh` ran `python manage.py migrate --noinput` unconditionally.
- `backend/scripts/startup.sh` ran `python manage.py migrate --noinput` unconditionally.
- `.github/workflows/deploy-prod.yml` writes `RUN_MIGRATIONS=true` after deploying the web image.
- `.github/workflows/deploy-prod-dispatch.yml` writes `RUN_MIGRATIONS=true` in two appsettings blocks after deploying the web image.
- `.github/workflows/schema-migration-stage.yml` provides exact-SHA checkout, production environment approval, PostgreSQL enforcement, advisory locking, migration execution, and migration checks.

## Required implementation

1. Resolve and verify the exact release SHA before any production mutation or deployment.
2. Execute the locked migration stage for that exact SHA before web deployment.
3. Block web deployment when migration execution or verification fails.
4. Remove all unconditional migration execution from ordinary web startup.
5. Remove the contradictory `RUN_MIGRATIONS=true` production app setting.
6. Remove duplicate dispatch appsettings application.
7. Add source-contract tests proving web startup contains no migration command and production deployment orders migration before web deployment.
8. Preserve local explicit migration commands for developer setup and controlled maintenance.

## Expected files

- `.github/workflows/schema-migration-stage.yml`
- `.github/workflows/deploy-prod.yml`
- `.github/workflows/deploy-prod-dispatch.yml`
- `entrypoint.sh`
- `backend/scripts/startup.sh`
- focused deployment/schema contract tests
- this work order

## Forbidden scope

- application data-model changes;
- new Django migrations;
- identity reconciliation under #1353;
- payment-provider work;
- frontend behavior;
- production approval claims;
- secret-value changes;
- branch-protection bypass;
- competitor comparisons or market-positioning content.

## Validation matrix

- clean database requiring all migrations;
- current database with no pending migrations;
- repeated invocation;
- PostgreSQL advisory-lock contention;
- failed migration blocks web deployment;
- successful migration permits web deployment;
- source proof that web replicas do not call `migrate`;
- interrupted migration recovery procedure;
- exact application and migration SHA reconciliation.

## Completion rule

Do not merge until the branch is limited to the declared scope, exact-head CI is green, no review blockers exist, and the source and test evidence demonstrate that web startup is not a schema-mutation authority.
