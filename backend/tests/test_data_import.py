"""Module 007 Data Import & Migration proof tests."""

import pytest

from tools.import_manager import (
    DataImportManager,
    DuplicateImportError,
    ImportRollbackError,
    ImportValidationError,
    InMemoryImportRepository,
)


def build_manager(repository=None):
    return DataImportManager(repository or InMemoryImportRepository(), required_fields=("external_id", "name"))


def valid_records():
    return [
        {"external_id": "S-001", "name": "Ada Lovelace", "grade_level": "07"},
        {"external_id": "S-002", "name": "Katherine Johnson", "grade_level": "08"},
    ]


def test_module007_rejects_invalid_schema_before_commit():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)

    with pytest.raises(ImportValidationError):
        manager.import_records([{"external_id": "S-001", "grade_level": "07"}], actor="registrar")

    assert repository.records == []
    assert repository.imports == {}
    assert repository.audit_events == []


def test_module007_commits_valid_import_and_audit_trail():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)

    result = manager.import_records(valid_records(), actor="registrar")

    assert result.status == "COMMITTED"
    assert result.record_count == 2
    assert len(repository.records) == 2
    assert {record["_import_id"] for record in repository.records} == {result.import_id}
    assert repository.imports[result.import_id]["actor"] == "registrar"
    assert [event.event_type for event in repository.audit_events] == ["IMPORT_COMMITTED"]


def test_module007_prevents_duplicate_reimport_of_same_payload():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)

    manager.import_records(valid_records(), actor="registrar")

    with pytest.raises(DuplicateImportError):
        manager.import_records(valid_records(), actor="registrar")

    assert len(repository.records) == 2
    assert len(repository.imports) == 1


def test_module007_import_is_atomic_when_insert_fails():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)
    repository.records.append({"external_id": "EXISTING", "name": "Existing Student"})
    repository.fail_next_insert = True

    with pytest.raises(RuntimeError, match="simulated insert failure"):
        manager.import_records(valid_records(), actor="registrar")

    assert repository.records == [{"external_id": "EXISTING", "name": "Existing Student"}]
    assert repository.imports == {}
    assert [event.event_type for event in repository.audit_events] == ["IMPORT_ROLLED_BACK_ON_FAILURE"]


def test_module007_rolls_back_committed_import_by_import_id():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)
    result = manager.import_records(valid_records(), actor="registrar")

    rollback = manager.rollback_import(result.import_id, actor="registrar")

    assert rollback.status == "ROLLED_BACK"
    assert rollback.record_count == 2
    assert repository.records == []
    assert repository.imports[result.import_id]["status"] == "ROLLED_BACK"
    assert [event.event_type for event in repository.audit_events] == ["IMPORT_COMMITTED", "IMPORT_ROLLED_BACK"]


def test_module007_rejects_unknown_or_duplicate_rollback():
    repository = InMemoryImportRepository()
    manager = build_manager(repository)

    with pytest.raises(ImportRollbackError):
        manager.rollback_import("missing-import-id", actor="registrar")

    result = manager.import_records(valid_records(), actor="registrar")
    manager.rollback_import(result.import_id, actor="registrar")

    with pytest.raises(ImportRollbackError):
        manager.rollback_import(result.import_id, actor="registrar")
