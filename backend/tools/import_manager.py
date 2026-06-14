"""Atomic data import manager for Module 007: Data Import & Migration.

The manager is intentionally framework-light so it can be used by Django services,
management commands, and tests without binding import safety to a single model.
It enforces the certification-critical contract:

* schema validation before writes
* duplicate-batch rejection before writes
* atomic all-or-nothing import application
* durable audit events
* explicit rollback using the recorded import id
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Protocol
from uuid import uuid4


class ImportValidationError(ValueError):
    """Raised when an import batch does not match the expected schema."""


class DuplicateImportError(ValueError):
    """Raised when the exact same import payload has already been committed."""


class ImportRollbackError(RuntimeError):
    """Raised when an import cannot be rolled back safely."""


@dataclass(frozen=True)
class ImportAuditEvent:
    """A normalized audit event emitted by the import manager."""

    event_type: str
    import_id: str
    actor: str
    record_count: int
    message: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class ImportResult:
    """Result returned for a committed or rolled-back import."""

    import_id: str
    fingerprint: str
    record_count: int
    status: str


class ImportRepository(Protocol):
    """Persistence contract required by DataImportManager."""

    def snapshot(self) -> Any: ...

    def restore(self, snapshot: Any) -> None: ...

    def fingerprint_exists(self, fingerprint: str) -> bool: ...

    def insert_many(self, records: list[dict[str, Any]], *, import_id: str) -> None: ...

    def record_import(self, *, import_id: str, fingerprint: str, actor: str, record_count: int) -> None: ...

    def get_import(self, import_id: str) -> dict[str, Any] | None: ...

    def mark_import_rolled_back(self, import_id: str) -> None: ...

    def delete_records_by_import_id(self, import_id: str) -> int: ...

    def append_audit_event(self, event: ImportAuditEvent) -> None: ...


class DataImportManager:
    """Validates, applies, audits, and rolls back data import batches."""

    def __init__(self, repository: ImportRepository, *, required_fields: Iterable[str]) -> None:
        self.repository = repository
        self.required_fields = tuple(required_fields)
        if not self.required_fields:
            raise ImportValidationError("required_fields must contain at least one field")

    def validate_records(self, records: list[dict[str, Any]]) -> None:
        if not isinstance(records, list) or not records:
            raise ImportValidationError("import payload must be a non-empty list of records")

        seen_keys: set[tuple[Any, ...]] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise ImportValidationError(f"record {index} must be an object")
            missing = [field_name for field_name in self.required_fields if record.get(field_name) in (None, "")]
            if missing:
                raise ImportValidationError(f"record {index} missing required fields: {', '.join(missing)}")
            key = tuple(record[field_name] for field_name in self.required_fields)
            if key in seen_keys:
                raise ImportValidationError(f"duplicate record inside payload at index {index}")
            seen_keys.add(key)

    def fingerprint_records(self, records: list[dict[str, Any]]) -> str:
        canonical = repr(sorted((tuple(sorted(record.items())) for record in records)))
        return sha256(canonical.encode("utf-8")).hexdigest()

    def import_records(self, records: list[dict[str, Any]], *, actor: str) -> ImportResult:
        self.validate_records(records)
        fingerprint = self.fingerprint_records(records)
        if self.repository.fingerprint_exists(fingerprint):
            raise DuplicateImportError("an import with the same payload has already been committed")

        import_id = str(uuid4())
        snapshot = self.repository.snapshot()
        try:
            self.repository.insert_many(records, import_id=import_id)
            self.repository.record_import(
                import_id=import_id,
                fingerprint=fingerprint,
                actor=actor,
                record_count=len(records),
            )
            self.repository.append_audit_event(
                ImportAuditEvent(
                    event_type="IMPORT_COMMITTED",
                    import_id=import_id,
                    actor=actor,
                    record_count=len(records),
                    message="Import committed atomically.",
                )
            )
        except Exception:
            self.repository.restore(snapshot)
            self.repository.append_audit_event(
                ImportAuditEvent(
                    event_type="IMPORT_ROLLED_BACK_ON_FAILURE",
                    import_id=import_id,
                    actor=actor,
                    record_count=len(records),
                    message="Import failed and repository snapshot was restored.",
                )
            )
            raise

        return ImportResult(import_id=import_id, fingerprint=fingerprint, record_count=len(records), status="COMMITTED")

    def rollback_import(self, import_id: str, *, actor: str) -> ImportResult:
        import_record = self.repository.get_import(import_id)
        if not import_record:
            raise ImportRollbackError(f"unknown import id: {import_id}")
        if import_record.get("status") == "ROLLED_BACK":
            raise ImportRollbackError(f"import already rolled back: {import_id}")

        snapshot = self.repository.snapshot()
        try:
            removed = self.repository.delete_records_by_import_id(import_id)
            self.repository.mark_import_rolled_back(import_id)
            self.repository.append_audit_event(
                ImportAuditEvent(
                    event_type="IMPORT_ROLLED_BACK",
                    import_id=import_id,
                    actor=actor,
                    record_count=removed,
                    message="Import rollback completed.",
                )
            )
        except Exception:
            self.repository.restore(snapshot)
            raise

        return ImportResult(
            import_id=import_id,
            fingerprint=str(import_record["fingerprint"]),
            record_count=removed,
            status="ROLLED_BACK",
        )


class InMemoryImportRepository:
    """Small repository implementation used by tests and local dry runs."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.imports: dict[str, dict[str, Any]] = {}
        self.audit_events: list[ImportAuditEvent] = []
        self.fail_next_insert = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "records": deepcopy(self.records),
            "imports": deepcopy(self.imports),
            "audit_events": deepcopy(self.audit_events),
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.records = deepcopy(snapshot["records"])
        self.imports = deepcopy(snapshot["imports"])
        self.audit_events = deepcopy(snapshot["audit_events"])

    def fingerprint_exists(self, fingerprint: str) -> bool:
        return any(item["fingerprint"] == fingerprint and item["status"] == "COMMITTED" for item in self.imports.values())

    def insert_many(self, records: list[dict[str, Any]], *, import_id: str) -> None:
        if self.fail_next_insert:
            self.fail_next_insert = False
            raise RuntimeError("simulated insert failure")
        for record in records:
            stored = deepcopy(record)
            stored["_import_id"] = import_id
            self.records.append(stored)

    def record_import(self, *, import_id: str, fingerprint: str, actor: str, record_count: int) -> None:
        self.imports[import_id] = {
            "import_id": import_id,
            "fingerprint": fingerprint,
            "actor": actor,
            "record_count": record_count,
            "status": "COMMITTED",
        }

    def get_import(self, import_id: str) -> dict[str, Any] | None:
        record = self.imports.get(import_id)
        return deepcopy(record) if record else None

    def mark_import_rolled_back(self, import_id: str) -> None:
        self.imports[import_id]["status"] = "ROLLED_BACK"

    def delete_records_by_import_id(self, import_id: str) -> int:
        before = len(self.records)
        self.records = [record for record in self.records if record.get("_import_id") != import_id]
        return before - len(self.records)

    def append_audit_event(self, event: ImportAuditEvent) -> None:
        self.audit_events.append(event)
