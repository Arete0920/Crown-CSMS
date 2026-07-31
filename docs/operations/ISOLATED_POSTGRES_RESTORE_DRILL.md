# Isolated PostgreSQL Restore Drill

**Status:** Runnable repository control; operational-backup evidence remains required.  
**Effective date:** 2026-07-31  
**Last reviewed:** 2026-07-31  
**Repository baseline reviewed:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Controlling issue:** #1627 (Lane 3 under #1619)  
**Historical context:** #1270  
**Production mutation:** Prohibited

## Freshness boundary

Before this runbook or any linked evidence is used or changed, verify the effective date, repository baseline, controlling issue, workflow definition, PostgreSQL version, artifact retention, backup identity, and whether a later canonical runbook supersedes it. Evidence from an older source SHA or synthetic fixture must remain explicitly historical and must not be treated as current operational-backup proof.

## Purpose

The `Isolated PostgreSQL Restore Drill` workflow executes a real PostgreSQL custom-format dump restore into a uniquely named, non-production database. It validates archive readability, backup age, digest, size, required tables, migration history, elapsed restore time, and cleanup. Evidence is retained as a GitHub Actions artifact.

## Automatic mechanics drill

Pull requests and qualifying pushes run the workflow automatically. It:

1. starts an isolated PostgreSQL 16 service;
2. applies current CROWN migrations to a source database;
3. creates a custom-format `pg_dump` archive;
4. records its timestamp, size, SHA-256 digest, and run identity;
5. executes `verify_backup_restore` against a new isolated database;
6. verifies required tables, public-table count, migration count, and cleanup;
7. uploads the evidence packet.

This is a real PostgreSQL dump and restore. It proves current restore mechanics, not the existence or freshness of an operational backup.

## Verified pull-request evidence

The run associated with PR #1798 produced artifact `8787408835`, digest `sha256:7838940af5bb0d116d55be02759309a09bae7f6e61aa85c4fc4a05cf0b42d5c9`, for pull-request merge ref `39dad0289498c0e62276c74aaf98911bd2735bd8` derived from branch head `969546ac4e474265574d78b0ae55d98902d6b259` and base `cae29286c77847006fe1890b84080581c1705f8f`.

That generated-fixture run recorded:

- result `PASS`;
- PostgreSQL 16 isolated service;
- all current migrations applied and `manage.py check` reporting no issues;
- custom-format archive size `1,576,066` bytes;
- archive SHA-256 `0755ae768d26e30fd9799781af0385ed897f458adf220c6c87c48b730aa643ac`;
- archive preflight passed;
- `388` public tables;
- `187` Django migration rows;
- required tables `core_school`, `core_useraccount`, and `django_migrations` present;
- isolated restore elapsed time `3.403` seconds;
- temporary database created and dropped;
- `production_database_mutated=false`.

This evidence is attributable to the pull-request merge ref, not to a final immutable release candidate or deployed runtime.

## Evidence packet

The artifact contains:

- `backup-created-at-utc.txt`;
- `backup-immutable-identifier.txt`;
- `backup-size-bytes.txt`;
- `backup.sha256`;
- `restore-evidence.json`;
- `retained-recovery-evidence.json`;
- `SUMMARY.md`.

A passing run requires archive preflight, isolated database creation, structural validation, successful database cleanup, and `production_database_mutated=false`.

## Remaining Lane 3 operational drill

Closing #1627 requires a retained operational backup or explicitly approved substitute tied to the selected immutable release SHA. The authorized operator must:

1. record environment, operator, source SHA, deployment identity, backup system, backup creation time, immutable backup identifier, digest, and size;
2. verify the approved RPO target before restore begins;
3. restore only into an isolated approved database and record start/end timestamps;
4. run schema, migration, required-table, tenant-isolation, row-count, relationship, and financial-integrity checks;
5. prove application connectivity to the restored copy without permitting production writes;
6. execute or independently prove application rollback to a known-good exact SHA;
7. record detection time, decision time, rollback duration, restore duration, total recovery time, and measured data-loss interval;
8. compare measured RTO/RPO with accepted targets and record accountable acceptance or rejection;
9. retain commands, logs, monitoring evidence, validation output, deviations, aborts, escalation, and cleanup evidence.

## Abort and escalation criteria

Stop the exercise and escalate if any of the following occurs:

- production database or production storage mutation is possible;
- source SHA, deployment identity, or backup identity cannot be proven;
- archive digest, size, age, or ownership cannot be verified;
- restore targets an existing or shared database;
- migration state or required tables do not reconcile;
- tenant isolation, financial totals, or referential integrity fail;
- monitoring or audit evidence is unavailable;
- operator privileges exceed the approved drill scope;
- accepted RTO/RPO cannot be evaluated from retained timestamps.

## Acceptance boundary

A passing automatic run establishes real PostgreSQL restore mechanics, archive preflight, isolated database creation, structural validation, measured restore duration, cleanup, and no production mutation.

It does **not** prove a current operational backup, Azure/application rollback, accepted RTO/RPO, production cutover, resilience certification, or production authorization. Those claims require the completed Lane 3 operational evidence packet linked to #1627 and #1619 for the same unchanged release SHA.