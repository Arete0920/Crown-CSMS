# Isolated PostgreSQL Restore Drill

**Status:** Runnable repository control; operational-backup evidence remains required.  
**Controlling issue:** #1270  
**Production mutation:** Prohibited

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

## Remaining operational drill

Closing #1270 still requires a current retained operational backup or explicitly approved substitute. That drill must preserve the backup system's authoritative creation timestamp and immutable identifier, verify digest and size, demonstrate the configured one-hour RPO, run tenant and application checks, and record measured recovery time.

The GitHub connector used by ChatGPT does not expose workflow dispatch and this execution environment has no authenticated GitHub CLI. A private operational backup must therefore be supplied through an approved backup workflow or started through GitHub Actions by an authenticated operator.

## Acceptance boundary

A passing automatic run establishes:

- real PostgreSQL dump and restore mechanics;
- archive preflight;
- isolated database creation;
- required-table and migration validation;
- measured restore duration;
- successful temporary-database cleanup;
- no production mutation.

It does not prove a current operational backup, Azure rollback, accepted RTO/RPO, production cutover, or production authorization.
