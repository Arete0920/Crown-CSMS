# Isolated PostgreSQL Restore Drill

**Status:** Runnable repository control; operational-backup evidence remains required.  
**Original mechanics baseline:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Last authority reconciliation:** 2026-08-18  
**Current authority:** `docs/CURRENT_RELEASE_STATUS.md` plus the authorized owner-handoff/operational-transfer record for the selected exact identity  
**Historical trackers:** predecessor recovery issue numbers, including former Lane 3/Lane 5 trackers, are provenance only  
**Production mutation:** Prohibited

## Freshness boundary

### Explicit DEV restored-copy migration rehearsal

The existing workflow has a default-OFF `rehearse_reviewed_migrations` input.
Use it only with `dev_operational_restore=true`, the exact current `expected_dev_sha`,
`confirm_dev_restore=restore-dev-backup-in-ci`, and the owner's synthetic-only
DEV attestation. It uses the pinned PostgreSQL 15 service matching the observed
DEV major version. The ordinary PostgreSQL 16 recovery mode remains unchanged.

The `reviewed_migration_profile` choice defaults to `heritage24`, preserving
the historical pinned 24-node contract. Select `finance_setup_0003` only for
a separately authorized operational restore/rehearsal whose complete pending
graph is exactly Finance Setup migration 0003. It rejects additional, missing,
duplicate or backward nodes and verifies the checked-in migration digest.
This profile cannot run the prior-image probe or authorize the existing live
reviewed24 stage. Its receipt reports one migration and its distinct profile.

The Finance Setup profile preserves raw pre-migration baseline fingerprints.
For row-preservation comparison only, it normalizes the reviewed `school_id`
integer-to-text representation; all other column values, all existing rows,
table counts and migration history remain checked. It verifies an integer
source column and text result, and rolls back numeric legacy INSERT and UUID
INSERT/read probes. This proves neither reverse migration with UUID policies
nor full prior-application rollback. Retained current-baseline recovery remains
a separate gate; a disposable snapshot is not a retained operational backup.

### Separately authorized DEV Finance Setup stage

The existing `deploy-dev.yml` keeps both migration switches default-OFF.
For a separately authorized Finance Setup release, select only
`apply_finance_setup_0003=true`, set
`confirm_finance_setup_0003=migrate-dev-finance-setup-0003`, and leave
`apply_reviewed_heritage24=false` with its confirmation blank. Both profiles
cannot run together. Ordinary deployment still rejects unreviewed migrations.

Before Azure credentials are read, the stage requires explicit synthetic-data,
verified durable-recovery, and maintenance-window attestations. Supply the exact
prior successful Finance rehearsal run and artifact IDs for the same protected
main SHA. The stage authenticates GitHub artifact provenance and digest, rejects
legacy or mismatched-profile receipts, checks the live database's exact raw
baseline, and permits only the pinned single forward migration. Under the
existing migration lock and one PostgreSQL transaction, it verifies the integer
source column, varchar(36) result, exact history increment, zero pending nodes,
and preservation of every existing row, including locks and policy children.
Only the reviewed school identifier representation is normalized for comparison.
Validation failure rolls back the schema and data changes.

Source availability and a passing disposable test do not authorize this stage,
deployment, feature configuration, invitations, or buyer certification. A receipt
continues to record full application rollback as `NOT_TESTED`. Revalidate the
current exact source and recovery evidence before requesting release authority.

The source snapshot and dump remain read-only. After the restored copy's table
counts, column definitions and migration history match, the optional rehearsal:

1. verifies the copy's unique database, local port, cluster identity and PG15;
2. verifies every migration file hash in the explicitly selected, pinned profile;
3. rejects extra, missing, duplicate or backward migration nodes;
4. applies that graph only to the disposable copy;
5. verifies zero pending nodes and the exact migration-history increment;
6. verifies pre-existing non-seed table values and table counts are preserved;
7. drops the restored database and removes the private dump on success or failure.

Only the reviewed permission and default-off feature seeds may increase their
existing table counts. Row values, credentials and process exception text are
withheld from the retained receipt. Failure diagnostics contain only a reviewed
migration identity, fixed reason code and SQLSTATE. Synthetic PG15 integration
tests preserve a historical PM pickup and late fee through the full graph. Legacy attendance/configuration/enrollment and staff INSERTs are
rehearsed in a rolled-back savepoint; empty evidence and false handoff defaults
never clear staff or guardian readiness. The graph and preservation checks are
executed in one PostgreSQL transaction.

This mode never changes DEV schema or applies the default deployment allowlist.
The original restore comparison is explicitly scoped before the clone migrations;
the separate `migration_rehearsal` receipt records the transformed copy. A passing
rehearsal does not authorize live migration, deployment, payments or buyer access.
Retained rollback capability and application rollback require separate evidence.

### Optional recorded prior-image probe

The existing operational restored-copy job can optionally probe the recorded DEV
image digest on its migrated disposable PostgreSQL 15 database. It is off by
default. In addition to the existing operational restore and reviewed-migration
authority, require `verify_prior_image=true` and
`confirm_prior_image=test-prior-image-on-disposable-copy`. The existing DEV Azure
identity must already have ACR pull access; this mode does not grant permissions.

The fixed image runs its original entrypoint without host ports, mounted source
credentials, bootstrap flags, or a writable root filesystem. An ownership-labelled
internal Docker network restricts external connectivity; only the disposable
database service is attached alongside the app. The probe verifies the network
is internal before startup, then checks served build/artifact identity,
database identity, anonymous platform denials,
and rolled-back legacy Extended Care/Camp inserts using the actual old models.
The application container is removed before the existing restore cleanup drops
the database and deletes the temporary archive. The task-owned internal network
is detached and removed as part of cleanup. Registry credentials are local
to this job and discarded. A pull, identity, probe, or cleanup failure blocks the
job. Source rows and process diagnostics are not published.

Results appear under `prior_image_probe` in the existing sanitized receipt.
This is a limited startup/read/write compatibility probe, **not full application
rollback certification**, durable backup retention, or live DEV authorization.
The existing `application_rollback_compatibility=NOT_TESTED` and
`release_readiness=NOT_VERIFIED` fields retain their original meaning. Do not
repeat the default rehearsal solely for another green run; this opt-in mode
requires a separate authorized operation to obtain the missing image evidence.

PR #632's original secret-scan finding was reproduced with Gitleaks 8.18.4:
the public SHA256 of the subscriptions 0006 migration matched `generic-api-key`
because its migration identifier contains `module_key`. The digest is verified
from the checked-in migration bytes. Its exact historical fingerprint is recorded
in `.gitleaksignore` for CODEOWNER review; rules and path scanning remain enabled.
The current manifest uses a named SHA256 constant to avoid this ambiguity.

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
