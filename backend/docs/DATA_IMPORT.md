# Data Import & Migration Procedure

Module: 007 — Data Import & Migration

## Purpose

CROWN data imports must be safe before they touch production records. The import path must reject malformed payloads before commit, prevent duplicate re-imports, preserve an audit trail, and support explicit rollback by import id.

## Runtime contract

`backend/tools/import_manager.py` provides the framework-light import contract used by module certification tests:

1. Validate records before writes.
2. Fingerprint each canonical payload.
3. Reject duplicate committed fingerprints.
4. Apply records atomically using repository snapshot/restore semantics.
5. Record committed import metadata.
6. Emit audit events for commits and failure rollbacks.
7. Roll back committed imports by import id.

## Required repository contract

Concrete import repositories must provide:

- `snapshot()`
- `restore(snapshot)`
- `fingerprint_exists(fingerprint)`
- `insert_many(records, import_id=...)`
- `record_import(import_id=..., fingerprint=..., actor=..., record_count=...)`
- `get_import(import_id)`
- `mark_import_rolled_back(import_id)`
- `delete_records_by_import_id(import_id)`
- `append_audit_event(event)`

The in-memory repository included with the manager is intentionally used only for local dry-run behavior and certification tests. Production repositories should wrap database transactions around equivalent operations.

## Certification coverage

`backend/tests/test_data_import.py` proves the required Module 007 behaviors:

- schema validation happens before writes;
- valid imports commit records and audit metadata;
- exact duplicate payloads are rejected;
- failed inserts restore the previous repository state;
- committed imports can be rolled back by import id;
- unknown and repeated rollbacks are rejected.

## Validation commands

```bash
cd backend
python manage.py check
pytest tests/test_data_import.py -v --tb=short
```

## Certification status

Module 007 can be moved to `PROVEN` only after the validation commands pass in CI or an equivalent captured proof run.
