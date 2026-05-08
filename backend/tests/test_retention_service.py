from types import SimpleNamespace

from core.services import retention_service


class _AuditCollector:
    def __init__(self):
        self.rows = []

    def create(self, **kwargs):
        self.rows.append(kwargs)
        return kwargs


def test_purge_expired_records_reports_legal_hold_skip(monkeypatch):
    legal_hold_policy = SimpleNamespace(
        model_name="core.NonPurgeableModel",
        legal_hold=True,
        retention_days=30,
    )

    class _PolicyManager:
        @staticmethod
        def all():
            return [legal_hold_policy]

    class _PolicyModel:
        objects = _PolicyManager()

    audit = _AuditCollector()

    class _AuditModel:
        objects = audit

    warning_calls = []

    def _warning(msg, *args):
        warning_calls.append(msg % args)

    monkeypatch.setattr(retention_service, "DataRetentionPolicy", _PolicyModel)
    monkeypatch.setattr(retention_service, "RetentionPurgeAudit", _AuditModel)
    monkeypatch.setattr(retention_service.logger, "warning", _warning)

    results = retention_service.purge_expired_records()

    assert results == [
        {
            "model": "core.NonPurgeableModel",
            "deleted": 0,
            "skipped_reason": "legal hold enabled",
        }
    ]
    assert any("legal hold enabled" in msg for msg in warning_calls)
    assert len(audit.rows) == 1
    assert audit.rows[0]["skipped_reason"] == "legal hold enabled"


def test_purge_expired_records_reports_missing_model(monkeypatch):
    missing_policy = SimpleNamespace(
        model_name="core.DoesNotExist",
        legal_hold=False,
        retention_days=15,
    )

    class _PolicyManager:
        @staticmethod
        def all():
            return [missing_policy]

    class _PolicyModel:
        objects = _PolicyManager()

    audit = _AuditCollector()

    class _AuditModel:
        objects = audit

    def _missing_model(_name):
        raise LookupError("not found")

    monkeypatch.setattr(retention_service, "DataRetentionPolicy", _PolicyModel)
    monkeypatch.setattr(retention_service, "RetentionPurgeAudit", _AuditModel)
    monkeypatch.setattr(retention_service.apps, "get_model", _missing_model)

    results = retention_service.purge_expired_records()

    assert len(results) == 1
    assert results[0]["model"] == "core.DoesNotExist"
    assert "model not found:" in results[0]["skipped_reason"]
    assert len(audit.rows) == 1
    assert "model not found:" in audit.rows[0]["skipped_reason"]


def test_purge_expired_records_reports_delete_failure(monkeypatch):
    failing_policy = SimpleNamespace(
        model_name="core.FailingModel",
        legal_hold=False,
        retention_days=90,
    )

    class _PolicyManager:
        @staticmethod
        def all():
            return [failing_policy]

    class _PolicyModel:
        objects = _PolicyManager()

    audit = _AuditCollector()

    class _AuditModel:
        objects = audit

    class _BrokenQueryset:
        @staticmethod
        def delete():
            raise RuntimeError("forced delete error")

    class _BrokenObjects:
        @staticmethod
        def filter(**_kwargs):
            return _BrokenQueryset()

    class _BrokenModel:
        created_at = object()
        objects = _BrokenObjects()

    monkeypatch.setattr(retention_service, "DataRetentionPolicy", _PolicyModel)
    monkeypatch.setattr(retention_service, "RetentionPurgeAudit", _AuditModel)
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: _BrokenModel)

    results = retention_service.purge_expired_records()

    assert len(results) == 1
    assert results[0]["model"] == "core.FailingModel"
    assert "delete failed:" in results[0]["skipped_reason"]
    assert len(audit.rows) == 1
    assert "delete failed:" in audit.rows[0]["skipped_reason"]
