from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from applications import views_admissions as views


from applications.fee_policy import AdmissionsFeePolicy


def _fee_policy(first=8500, additional=5000):
    return AdmissionsFeePolicy(
        school_id="test-school", term="2026-2027", schedule_id="test-schedule",
        first_child_cents=first, additional_child_cents=additional,
    )


def _submit_data(*, students=1, aid_intent="not_applying"):
    return SimpleNamespace(students=[{} for _ in range(students)],
                           financial_aid_interest={"intent": aid_intent})


@pytest.mark.parametrize(("count", "expected"), [
    (1, ["85.00"]), (2, ["85.00", "50.00"]),
    (3, ["85.00", "50.00", "50.00"]),
    (5, ["85.00", "50.00", "50.00", "50.00", "50.00"]),
])
def test_canonical_fee_rows(count, expected):
    rows = views._fee_rows_for_household(_submit_data(students=count, aid_intent="applying"), [], _fee_policy())
    assert [row["application_fee"] for row in rows] == expected
    assert [row["total"] for row in rows] == expected
    assert all(row["financial_aid_fee"] == "0.00" for row in rows)
    assert all(row["enrollment_fee"] == "0.00" for row in rows)


def test_no_global_legacy_fee_quote():
    assert views._application_fee_config()["configured"] is False
    assert views._application_fee_config()["amount"] is None
    assert views._application_fee_required(_fee_policy()) is True
    assert views._application_fee_required(_fee_policy(0, 0)) is False


def test_financial_aid_interest_not_a_charge():
    assert views._financial_aid_interest_is_applying(_submit_data(aid_intent="applying"))
    assert views._financial_aid_fee_config(_submit_data(aid_intent="applying"))["amount"] is None
    assert views._financial_aid_fee_config(_submit_data(aid_intent="applying"))["payable_now"] is False


def test_fee_quote_explicitly_scoped():
    config = views._application_fee_config(_fee_policy())
    assert config["configured"] is True
    assert config["school_id"] == "test-school"
    assert config["term"] == "2026-2027"
    assert config["amount"] == "85.00"
    assert config["additional_child_amount"] == "50.00"


def test_graph_configuration_accepts_graph_or_azure_credentials(monkeypatch):
    for name in (
        "GRAPH_TENANT_ID",
        "GRAPH_CLIENT_ID",
        "GRAPH_CLIENT_SECRET",
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    assert views._is_graph_email_configured() is False

    monkeypatch.setenv("GRAPH_TENANT_ID", "tenant")
    monkeypatch.setenv("GRAPH_CLIENT_ID", "client")
    monkeypatch.setenv("GRAPH_CLIENT_SECRET", "secret")
    assert views._is_graph_email_configured() is True

    monkeypatch.delenv("GRAPH_TENANT_ID")
    monkeypatch.delenv("GRAPH_CLIENT_ID")
    monkeypatch.delenv("GRAPH_CLIENT_SECRET")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    assert views._is_graph_email_configured() is True


def test_sharepoint_and_sms_configuration(monkeypatch):
    monkeypatch.delenv("M365_SHAREPOINT_SITE_ID", raising=False)
    monkeypatch.delenv("M365_DEFAULT_DRIVE_ID", raising=False)
    monkeypatch.delenv("COMMS_SMS_ENABLED", raising=False)

    assert views._is_sharepoint_configured() is False
    assert views._is_sms_configured() is False

    monkeypatch.setenv("M365_DEFAULT_DRIVE_ID", "drive")
    monkeypatch.setenv("COMMS_SMS_ENABLED", " YES ")

    assert views._is_sharepoint_configured() is True
    assert views._is_sms_configured() is True


def test_contract_m365_handoff_requires_email_and_sharepoint(monkeypatch):
    monkeypatch.setattr(views, "_is_graph_email_configured", lambda: True)
    monkeypatch.setattr(views, "_is_sharepoint_configured", lambda: False)

    payload = views._build_contract_m365_handoff(application_ids=["app-1", "app-2"])

    assert payload["enabled"] is False
    assert payload["provider"] == "microsoft_365"
    assert payload["application_ids"] == ["app-1", "app-2"]
    assert "guardian_names" in payload["template"]["autopopulate_fields"]


def test_heritage_canonical_upfront_fee_math():
    from applications.fee_policy import AdmissionsFeePolicy

    policy = AdmissionsFeePolicy(
        school_id="test-school", term="2026-2027", schedule_id="test-schedule",
        first_child_cents=8500, additional_child_cents=5000,
    )
    assert [policy.amount_for_child(i) for i in range(1, 6)] == [
        Decimal("85.00"), Decimal("50.00"), Decimal("50.00"),
        Decimal("50.00"), Decimal("50.00"),
    ]
    assert sum(policy.amount_for_child(i) for i in range(1, 4)) == Decimal("185.00")
    assert policy.required is True


def test_admissions_fee_policy_requires_school_and_term():
    from applications.fee_policy import get_admissions_fee_policy

    assert get_admissions_fee_policy(school=None, term="2026-2027") is None
    assert get_admissions_fee_policy(school=SimpleNamespace(pk="school-uuid"), term="") is None
