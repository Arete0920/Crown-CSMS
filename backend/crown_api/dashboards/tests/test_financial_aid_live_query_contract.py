"""DB-independent executable query and response-contract checks for the Jireh live builder.

Does not replace Django ORM/DRF or a real database acceptance suite.
"""
import sys
from types import ModuleType, SimpleNamespace
import pytest

from crown_api.dashboards.financial_aid_live import (
    FinancialAidDashboardIntegrityError,
    financial_aid_live_payload,
)

SCHOOL = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
YEAR = "33333333-3333-3333-3333-333333333333"
FAMILY = "44444444-4444-4444-4444-444444444444"
STUDENT = "55555555-5555-5555-5555-555555555555"


def application(*, status="SUBMITTED", family_school=SCHOOL):
    return {"family_id": FAMILY, "family__school_id": family_school,
            "academic_year__school_id": SCHOOL, "status": status}


def award(*, amount=12500, student_school=SCHOOL, reversal_count=0, linked=True):
    row = dict(student_id=STUDENT, student__school_id=student_school,
        student__family_id=FAMILY, student__family__school_id=SCHOOL,
        academic_year__school_id=SCHOOL, aid_application_id="app",
        aid_application__school_id=SCHOOL,
        aid_application__academic_year_id=YEAR,
        aid_application__family_id=FAMILY,
        decision_status="ACCEPTED", awarded_cents=amount,
        ledger_entry_id="legacy" if linked else None,
        ledger_entry__school_id=SCHOOL, ledger_entry__academic_year_id=YEAR,
        ledger_entry__student_id=STUDENT, ledger_entry__family_id=FAMILY,
        ledger_entry__amount_cents=-amount, ledger_entry__is_reversal=False,
        ledger_entry__source="AID_AWARD", ledger_entry__account__school_id=SCHOOL,
        ledger_entry__account__code="AID", ledger_entry__reversal_of_id=None,
        ledger_reversal_count=reversal_count)
    return row


class Query:
    def __init__(self, *, name, data, log):
        self.name, self.data, self.log = name, data, log

    def filter(self, **kwargs):
        self.log.append((self.name, "filter", kwargs))
        return self

    def values_list(self, field, flat=False):
        self.log.append((self.name, "values_list", (field, flat)))
        if field != "id" or flat is not True:
            raise AssertionError("Unexpected academic-year projection")
        return self.data

    def annotate(self, **kwargs):
        self.log.append((self.name, "annotate", kwargs))
        return self

    def values(self, *fields):
        self.log.append((self.name, "values", fields))
        return self.data


@pytest.fixture
def fake_orm(monkeypatch):
    log = []
    data = {"years": [YEAR], "apps": [application()], "awards": [award()]}

    def module(name, **attrs):
        result = ModuleType(name)
        result.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, result)

    class FakeCount:
        def __init__(self, field, distinct=False):
            self.field, self.distinct = field, distinct

    module("aid", __path__=[])
    module("aid.models",
        AidApplication=SimpleNamespace(objects=Query(name="apps", data=data["apps"], log=log)),
        AidAward=SimpleNamespace(objects=Query(name="awards", data=data["awards"], log=log)))
    module("core", __path__=[])
    module("core.models", AcademicYear=SimpleNamespace(objects=Query(name="years", data=data["years"], log=log)))
    module("django", __path__=[])
    module("django.db", __path__=[])
    module("django.db.models", Count=FakeCount)

    def metric(label, value, secondary=None):
        return {"label": str(label), "value": str(value), "secondary": secondary}

    def alert(title, level="Low", secondary=""):
        return {"title": title, "level": level, "secondary": secondary}

    def build_dashboard_payload(**kw):
        assert set(kw) == {"dashboard_key", "metrics", "alerts", "queue", "meta"}
        return kw

    module("crown_api.dashboards.payload_contract", metric=metric, alert=alert,
           build_dashboard_payload=build_dashboard_payload)
    return data, log, FakeCount


def test_live_builder_scopes_all_projections_to_current_tenant_and_year(fake_orm):
    data, log, FakeCount = fake_orm
    result = financial_aid_live_payload(SCHOOL)
    assert log[0] == ("years", "filter", {"school_id": SCHOOL, "is_current": True})
    assert ("apps", "filter", {"school_id": SCHOOL, "academic_year_id": YEAR}) in log
    assert ("awards", "filter", {"school_id": SCHOOL, "academic_year_id": YEAR}) in log
    ann = next(value for name, op, value in log if name == "awards" and op == "annotate")
    assert ann["ledger_reversal_count"].field == "ledger_entry__reversals"
    assert ann["ledger_reversal_count"].distinct is True
    fields = next(value for name, op, value in log if name == "awards" and op == "values")
    for essential in ("student__family__school_id", "aid_application__academic_year_id",
            "ledger_entry__account__school_id", "ledger_entry__source", "ledger_reversal_count"):
        assert essential in fields
    assert result["dashboard_key"] == "financial-aid"
    assert result["meta"]["served_from"] == "live_db"
    assert result["meta"]["money_basis"] == "face_value_not_disbursement"
    assert result["metrics"][3]["value"] == "$125.00"
    assert len(result["alerts"]) == 0
    assert "family_name" not in str(result)


def test_no_current_year_returns_none_before_any_financial_rows(fake_orm):
    data, log, _ = fake_orm
    data["years"][:] = []
    assert financial_aid_live_payload(SCHOOL) is None
    assert not any(name in ("apps", "awards") for name, _, _ in log)


def test_multiple_current_years_fail_closed_before_any_financial_rows(fake_orm):
    data, log, _ = fake_orm
    data["years"][:] = [YEAR, OTHER]
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)
    assert not any(name in ("apps", "awards") for name, _, _ in log)


def test_empty_data_returns_true_zeroes_not_fixed_samples(fake_orm):
    data, _, _ = fake_orm
    data["apps"][:] = []
    data["awards"][:] = []
    result = financial_aid_live_payload(SCHOOL)
    assert [m["value"] for m in result["metrics"]] == ["0", "0", "0", "$0.00"]
    assert result["meta"]["submitted_applications"] == 0
    assert not result["alerts"] and not result["queue"]


def test_unlinked_accepted_award_is_disclosed_as_reconciliation_not_cash(fake_orm):
    data, _, _ = fake_orm
    data["awards"][:] = [award(linked=False)]
    result = financial_aid_live_payload(SCHOOL)
    assert result["meta"]["accepted_without_ledger_count"] == 1
    assert len(result["alerts"]) == 1
    assert result["meta"]["money_basis"] == "face_value_not_disbursement"
    assert result["metrics"][3]["label"] == "Accepted award face value"


@pytest.mark.parametrize("bad", [
    {"student_school": OTHER},
    {"reversal_count": 1},
    {"amount": -1},
])
def test_award_integrity_failure_never_returns_partial_payload(fake_orm, bad):
    data, _, _ = fake_orm
    data["awards"][:] = [award(**bad)]
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)


def test_foreign_family_integrity_failure_never_returns_partial_payload(fake_orm):
    data, _, _ = fake_orm
    data["apps"][:] = [application(family_school=OTHER)]
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)
