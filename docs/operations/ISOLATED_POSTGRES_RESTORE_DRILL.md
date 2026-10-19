# Isolated PostgreSQL Restore Drill

**Status:** Runnable repository control; operational-backup evidence remains required.  
**Original mechanics baseline:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Last authority reconciliation:** 2026-08-18  
**Current authority:** `docs/CURRENT_RELEASE_STATUS.md` plus the authorized owner-handoff/operational-transfer record for the selected exact identity  
**Historical trackers:** predecessor recovery issue numbers, including former Lane 3/Lane 5 trackers, are provenance only  
**Production mutation:** Prohibited

## Freshness boundary

Before this runbook or linked evidence is used operationally, verify the current repository identity, workflow definition, PostgreSQL version, artifact retention, backup identity, target environment, and whether a later canonical runbook supersedes it. Evidence from an older source SHA, predecessor issue campaign, or synthetic fixture must remain explicitly historical and must not be treated as current operational-backup proof.

## Purpose

The isolated PostgreSQL restore control validates a real PostgreSQL custom-format dump by restoring it into a uniquely named, non-production database. The control is intended to verify archive readability, backup identity and age, digest, required tables, migration history, elapsed restore time, structural integrity, and cleanup without mutating production.

## Automatic mechanics drill

The repository workflow/mechanics may:

1. start an isolated supported PostgreSQL service;
2. apply the current CROWN migration set to a source database;
3. create or receive a custom-format `pg_dump` archive;
4. record timestamp, size, SHA-256 digest, source identity, and run identity;
5. execute `verify_backup_restore` against a new isolated database;
6. verify required tables, migration state, structural checks, and restore-database cleanup;
7. run the historical `MarketingLead` INSERT/read regression once against a separate pytest database with normal migrations on the same isolated PostgreSQL 16 service;
8. verify that the pytest database was dropped and the generated source database still exists;
9. retain an evidence packet requiring both restore and regression success.

The workflow pins the generated source database to `crown_source` on the local PostgreSQL 16 service and verifies Django will use the distinct `test_crown_source` database. It runs `backend/crm_marketing/tests/test_inquiry_capture.py::test_pre_inquiry_model_can_insert_after_inquiry_migration` with `--ds=crown_api.settings --migrations --create-db`. The historical `0001_initial` model omits all new inquiry columns; the current model must read the expected persistent defaults. No live database, operational backup, new credential, or provider is used.

The retained packet requires the exact named JUnit case to pass without a skip, failure, or error, successful normal-migration execution on PostgreSQL 16, and test-database cleanup. A missing or failing regression cannot be replaced by a successful restore result.

A generated-fixture run proves the recorded restore mechanics and this legacy INSERT/read boundary. It does **not** prove the existence, freshness, ownership, retention, or recoverability of an operational production backup.

## Historical mechanics evidence

Prior retained evidence demonstrated a real PostgreSQL 16 isolated restore with archive preflight, required-table verification, Django migration verification, measured elapsed restore time, temporary database creation/drop, and `production_database_mutated=false`.

That evidence remains useful provenance for the mechanics but is not current release-linked operational-backup proof. Historical artifact IDs, workflow runs, predecessor repository SHAs, and issue numbers must not be promoted into current transfer or production evidence without explicit current canonical incorporation.

## Evidence packet

A current evidence packet should include, with secrets excluded:

- exact Crown-CSMS source/release identity;
- environment and authorized operator;
- backup source/system and immutable backup identifier;
- backup creation time and age at drill start;
- backup size and SHA-256 digest;
- restore start/end timestamps and elapsed duration;
- archive-preflight result;
- migration and required-table results;
- `inquiry-legacy-insert.xml` with the single named, unskipped compatibility case and `inquiry-legacy-insert-execution.json` recording PostgreSQL version, distinct source/test database names, normal migrations, exit status, and cleanup;
- a schema-version-2 `retained-recovery-evidence.json` whose overall result requires both restore and inquiry legacy INSERT/read results to pass;
- tenant-isolation, critical-record, relationship, and financial-integrity results required by the selected scope;
- application compatibility/connectivity result against the restored copy where applicable;
- cleanup result;
- measured RTO/RPO and accepted target/disposition where required;
- evidence links and authorized acceptance/rejection.

## Controlled operational drill

For a selected release or transfer identity, the authorized operator should:

1. prove exact source, deployment/runtime identity where applicable, and backup identity before mutation;
2. verify the approved RPO target before restore begins;
3. restore only into an isolated approved database;
4. run schema, migration, required-table, tenant-isolation, row-count, relationship, and material financial-integrity checks appropriate to the system state;
5. prove application connectivity to the restored copy without permitting production writes where that proof is required;
6. independently reconcile application rollback/forward-fix compatibility with the restored database;
7. record detection, decision, rollback, restore, and total-recovery timestamps when measuring RTO;
8. calculate the measured data-loss interval when evaluating RPO;
9. retain commands, logs, monitoring evidence, validation output, deviations, aborts, escalation, acceptance, and cleanup evidence.

## Abort and escalation criteria

Stop the exercise and escalate when:

- production database or production storage mutation is possible without explicit approved authority;
- source SHA, deployment/runtime identity, or backup identity cannot be proven;
- archive digest, size, age, ownership, or retention cannot be verified;
- restore targets an existing/shared database when isolation is required;
- migration state or required tables do not reconcile;
- tenant isolation, material financial totals, or referential integrity fail;
- application/database compatibility cannot be established;
- monitoring or audit evidence required by the exercise is unavailable;
- operator privileges exceed the approved drill scope;
- accepted RTO/RPO cannot be evaluated from retained evidence when those measurements are required.

## Acceptance boundary

A passing repository mechanics run establishes only the checks actually recorded, including archive preflight, isolated database creation, structural validation, elapsed restore duration, cleanup, no production mutation, and the legacy `MarketingLead` INSERT/read boundary against the current inquiry schema. The compatibility test does not certify every previous-image endpoint against new inquiry data. If a later image deployment fails after migration, retain the additive schema/data and have the operator verify the chosen rollback image separately.

It does **not** by itself prove a current operational backup, application rollback completion, accepted RTO/RPO, production cutover, resilience certification, production authorization, legal/compliance approval, or completed owner turnover.

Current operational recovery acceptance must be tied to the exact selected Crown-CSMS identity and the authorized current transfer/release record, not to predecessor issue numbers or historical artifacts.
