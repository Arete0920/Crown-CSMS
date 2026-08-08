from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path: str) -> str:
    return (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")


def test_billing_scheduled_mutation_is_tenant_explicit():
    task_source = _source("billing/tasks.py")
    service_source = _source("billing/services_grace.py")

    assert "with tenant_context(school):" in task_source
    assert "_enforce(school_id=school.id)" in task_source
    assert "def enforce_grace_period(*, school_id)" in service_source
    assert "school_id=school_id" in service_source


def test_support_scheduled_mutation_is_tenant_explicit():
    task_source = _source("support/tasks.py")
    service_source = _source("support/services_escalation.py")
    api_source = _source("support/api_support.py")

    assert "with tenant_context(school):" in task_source
    assert "_escalate(school_id=school.id)" in task_source
    assert "def escalate_overdue_tickets(*, school_id)" in service_source
    assert "school_id=school_id" in service_source
    assert "escalate_overdue_tickets(school_id=school_id)" in api_source


def test_analytics_background_execution_binds_tenant_context():
    source = _source("analytics/tasks.py")

    assert source.count("with tenant_context(school):") >= 2
    assert "run_all_predictive_models.delay(str(school_id))" in source


def test_payment_dependent_beat_tasks_remain_fail_closed():
    source = _source("ledger/tasks.py")

    assert "PAYMENT_INTEGRATION_ON_HOLD" in source
    assert '"mutated": False' in source
    assert "process_failed_payments" not in source
    assert "record_daily_payout_audit" not in source


def test_retention_beat_task_remains_preview_only_by_default():
    source = _source("core/tasks.py")

    assert "execute=False" in source
    assert "allow_global=False" in source
    assert "confirmation=None" in source
