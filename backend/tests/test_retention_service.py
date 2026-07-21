from types import SimpleNamespace

import pytest

from core.services import retention_service


class _AuditCollector:
    def __init__(self, fail=False):
        self.rows = []
        self.fail = fail

    def create(self, **kwargs):
        if self.fail:
            raise RuntimeError("forced audit error")
        self.rows.append(kwargs)
        return kwargs


class _PolicyManager:
    def __init__(self, policies):
        self.policies = policies

    def all(self):
        return self.policies


class _Field:
    def __init__(self, name, attname=None):
        self.name = name
        self.attname = attname or name


class _Meta:
    pk = SimpleNamespace(attname="id")
    label = "core.ScopedModel"

    @staticmethod
    def get_field(name):
        if name != "created_at":
            raise LookupError(name)
        return _Field("created_at")

    @staticmethod
    def get_fields():
        return [_Field("created_at"), _Field("school", "school_id")]


def _install_policy_and_audit(monkeypatch, policy, *, audit_fail=False):
    audit = _AuditCollector(fail=audit_fail)
    monkeypatch.setattr(
        retention_service,
        "DataRetentionPolicy",
        SimpleNamespace(objects=_PolicyManager([policy])),
    )
    monkeypatch.setattr(
        retention_service,
        "RetentionPurgeAudit",
        SimpleNamespace(objects=audit),
    )
    return audit


def test_purge_is_dry_run_by_default_and_never_deletes(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _Queryset:
        @staticmethod
        def count():
            return 3

    class _Objects:
        filters = []

        @classmethod
        def filter(cls, **kwargs):
            cls.filters.append(kwargs)
            return _Queryset()

    model = SimpleNamespace(_meta=_Meta(), objects=_Objects())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    results = retention_service.purge_expired_records(tenant_id="school-1")

    assert results[0]["mode"] == "dry_run"
    assert results[0]["matched"] == 3
    assert results[0]["deleted"] == 0
    assert results[0]["skipped_reason"] == "dry run"
    assert _Objects.filters[0]["school_id"] == "school-1"
    snapshot = audit.rows[0]["policy_snapshot"]
    assert snapshot["dry_run"] is True
    assert snapshot["selected_count"] == 0
    assert snapshot["batch_count"] == 0
    assert snapshot["rolled_back"] is False


def test_execute_requires_boolean_confirmation_approver_and_scope():
    with pytest.raises(ValueError):
        retention_service.purge_expired_records(execute="yes")
    with pytest.raises(retention_service.RetentionAuthorizationError):
        retention_service.purge_expired_records(execute=True)
    with pytest.raises(retention_service.RetentionAuthorizationError):
        retention_service.purge_expired_records(
            execute=True,
            confirmation=retention_service.EXECUTION_CONFIRMATION,
        )
    with pytest.raises(retention_service.RetentionAuthorizationError):
        retention_service.purge_expired_records(
            execute=True,
            confirmation=retention_service.EXECUTION_CONFIRMATION,
            approved_by="owner",
        )


def test_allow_global_must_be_boolean():
    with pytest.raises(ValueError):
        retention_service.purge_expired_records(allow_global="yes")


def test_legal_hold_always_skips(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.NonPurgeableModel", legal_hold=True, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    results = retention_service.purge_expired_records(tenant_id="school-1")

    assert results[0]["skipped_reason"] == "legal hold enabled"
    assert results[0]["deleted"] == 0
    assert audit.rows[0]["legal_hold"] is True


def test_invalid_retention_window_fails_closed(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=0
    )
    audit = _install_policy_and_audit(monkeypatch, policy)
    get_model_calls = []
    monkeypatch.setattr(
        retention_service.apps,
        "get_model",
        lambda name: get_model_calls.append(name),
    )

    results = retention_service.purge_expired_records(tenant_id="school-1")

    assert results[0]["skipped_reason"] == "invalid retention_days"
    assert results[0]["matched"] == 0
    assert results[0]["deleted"] == 0
    assert get_model_calls == []
    assert audit.rows[0]["skipped_reason"] == "invalid retention_days"


def test_blank_tenant_id_fails_closed(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)
    model = SimpleNamespace(_meta=_Meta(), objects=SimpleNamespace())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    results = retention_service.purge_expired_records(tenant_id="   ")

    assert results[0]["skipped_reason"] == "tenant scope required"
    assert audit.rows[0]["policy_snapshot"]["tenant_id"] is None


def test_global_override_cannot_bypass_tenant_owned_model(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)
    model = SimpleNamespace(_meta=_Meta(), objects=SimpleNamespace())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)
    monkeypatch.setattr(
        retention_service.settings,
        retention_service.GLOBAL_MODEL_ALLOWLIST_SETTING,
        ["core.ScopedModel"],
        raising=False,
    )

    results = retention_service.purge_expired_records(allow_global=True)

    assert results[0]["tenant_field"] == "school_id"
    assert results[0]["skipped_reason"] == "tenant scope required"
    assert audit.rows[0]["policy_snapshot"]["global_model_approved"] is False


def test_global_override_requires_positive_model_allowlist(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.GlobalModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _GlobalMeta(_Meta):
        label = "core.GlobalModel"

        @staticmethod
        def get_fields():
            return [_Field("created_at")]

    model = SimpleNamespace(_meta=_GlobalMeta(), objects=SimpleNamespace())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)
    monkeypatch.setattr(
        retention_service.settings,
        retention_service.GLOBAL_MODEL_ALLOWLIST_SETTING,
        [],
        raising=False,
    )

    results = retention_service.purge_expired_records(allow_global=True)

    assert results[0]["skipped_reason"] == "global model not approved"
    assert audit.rows[0]["policy_snapshot"]["global_model_approved"] is False


def test_global_override_allows_only_approved_unscoped_model(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.GlobalModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _GlobalMeta(_Meta):
        label = "core.GlobalModel"

        @staticmethod
        def get_fields():
            return [_Field("created_at")]

    class _Queryset:
        @staticmethod
        def count():
            return 2

    class _Objects:
        @staticmethod
        def filter(**kwargs):
            assert "school_id" not in kwargs
            return _Queryset()

    model = SimpleNamespace(_meta=_GlobalMeta(), objects=_Objects())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)
    monkeypatch.setattr(
        retention_service.settings,
        retention_service.GLOBAL_MODEL_ALLOWLIST_SETTING,
        "core.GlobalModel",
        raising=False,
    )

    results = retention_service.purge_expired_records(allow_global=True)

    assert results[0]["mode"] == "dry_run"
    assert results[0]["matched"] == 2
    assert results[0]["skipped_reason"] == "dry run"
    assert audit.rows[0]["policy_snapshot"]["global_model_approved"] is True


def test_unknown_tenant_field_fails_closed(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.GlobalModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _GlobalMeta(_Meta):
        @staticmethod
        def get_fields():
            return [_Field("created_at")]

    model = SimpleNamespace(_meta=_GlobalMeta(), objects=SimpleNamespace())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    results = retention_service.purge_expired_records(tenant_id="school-1")

    assert results[0]["skipped_reason"] == "tenant field not found"
    assert audit.rows[0]["deleted_count"] == 0


def test_execute_reapplies_scope_and_cutoff_in_bounded_batches(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)
    remaining_ids = [1, 2, 3, 4, 5]
    delete_filters = []

    class _CandidateQueryset:
        @staticmethod
        def count():
            return len(remaining_ids)

        @staticmethod
        def order_by(_field):
            return _CandidateQueryset()

        @staticmethod
        def values_list(_field, flat=False):
            assert flat is True
            return list(remaining_ids)

    class _DeleteQueryset:
        def __init__(self, ids):
            self.ids = list(ids)

        def delete(self):
            for item in self.ids:
                remaining_ids.remove(item)
            return len(self.ids), {"core.ScopedModel": len(self.ids)}

    class _Objects:
        @staticmethod
        def filter(**kwargs):
            if "id__in" in kwargs:
                delete_filters.append(kwargs)
                return _DeleteQueryset(kwargs["id__in"])
            assert kwargs["school_id"] == "school-1"
            assert "created_at__lt" in kwargs
            return _CandidateQueryset()

    model = SimpleNamespace(_meta=_Meta(), objects=_Objects())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    results = retention_service.purge_expired_records(
        execute=True,
        confirmation=retention_service.EXECUTION_CONFIRMATION,
        approved_by="compliance-owner",
        tenant_id="school-1",
        batch_size=2,
    )

    assert [row["id__in"] for row in delete_filters] == [[1, 2], [3, 4], [5]]
    assert all(row["school_id"] == "school-1" for row in delete_filters)
    assert all("created_at__lt" in row for row in delete_filters)
    assert results[0]["selected"] == 5
    assert results[0]["deleted"] == 5
    assert results[0]["batches"] == 3
    snapshot = audit.rows[0]["policy_snapshot"]
    assert snapshot["primary_deleted_count"] == 5
    assert snapshot["cascade_deleted_count"] == 0
    assert snapshot["rolled_back"] is False


def test_cascade_delete_is_rejected_and_reported_as_rolled_back(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _CandidateQueryset:
        @staticmethod
        def count():
            return 1

        @staticmethod
        def order_by(_field):
            return _CandidateQueryset()

        @staticmethod
        def values_list(_field, flat=False):
            return [1]

    class _DeleteQueryset:
        @staticmethod
        def delete():
            return 2, {"core.ScopedModel": 1, "core.Related": 1}

    class _Objects:
        @staticmethod
        def filter(**kwargs):
            return _DeleteQueryset() if "id__in" in kwargs else _CandidateQueryset()

    model = SimpleNamespace(_meta=_Meta(), objects=_Objects())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    with pytest.raises(RuntimeError, match="cascade deletion detected"):
        retention_service.purge_expired_records(
            execute=True,
            confirmation=retention_service.EXECUTION_CONFIRMATION,
            approved_by="compliance-owner",
            tenant_id="school-1",
        )

    snapshot = audit.rows[0]["policy_snapshot"]
    assert audit.rows[0]["deleted_count"] == 0
    assert snapshot["cascade_deleted_count"] == 1
    assert snapshot["rolled_back"] is True


def test_delete_failure_is_audited_and_propagated(monkeypatch):
    policy = SimpleNamespace(
        model_name="core.ScopedModel", legal_hold=False, retention_days=30
    )
    audit = _install_policy_and_audit(monkeypatch, policy)

    class _CandidateQueryset:
        @staticmethod
        def count():
            return 1

        @staticmethod
        def order_by(_field):
            return _CandidateQueryset()

        @staticmethod
        def values_list(_field, flat=False):
            return [1]

    class _DeleteQueryset:
        @staticmethod
        def delete():
            raise RuntimeError("forced delete error")

    class _Objects:
        @staticmethod
        def filter(**kwargs):
            return _DeleteQueryset() if "id__in" in kwargs else _CandidateQueryset()

    model = SimpleNamespace(_meta=_Meta(), objects=_Objects())
    monkeypatch.setattr(retention_service.apps, "get_model", lambda _name: model)

    with pytest.raises(RuntimeError, match="forced delete error"):
        retention_service.purge_expired_records(
            execute=True,
            confirmation=retention_service.EXECUTION_CONFIRMATION,
            approved_by="compliance-owner",
            tenant_id="school-1",
        )

    assert audit.rows[0]["skipped_reason"].startswith("execution rolled back")
    assert audit.rows[0]["policy_snapshot"]["rolled_back"] is True


def test_batch_size_is_bounded():
    with pytest.raises(ValueError):
        retention_service.purge_expired_records(batch_size=0)
    with pytest.raises(ValueError):
        retention_service.purge_expired_records(
            batch_size=retention_service.MAX_BATCH_SIZE + 1
        )
