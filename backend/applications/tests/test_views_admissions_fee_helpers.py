from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from applications import views_admissions as views


@pytest.mark.parametrize(
    ("child_index", "expected"),
    [
        (-1, 0),
        (0, 0),
        (1, 0),
        (2, 25),
        (3, 50),
        (4, 75),
        (5, 100),
        (8, 100),
    ],
)
def test_child_discount_percent_tiers(child_index, expected):
    assert views._child_discount_percent(child_index) == expected


@pytest.mark.parametrize(
    ("amount", "child_index", "expected"),
    [
        (Decimal("100.00"), 1, Decimal("100.00")),
        (Decimal("100.00"), 2, Decimal("75.00")),
        (Decimal("100.00"), 3, Decimal("50.00")),
        (Decimal("100.00"), 4, Decimal("25.00")),
        (Decimal("100.00"), 5, Decimal("0.00")),
        (Decimal("0.01"), 2, Decimal("0.01")),
    ],
)
def test_apply_child_discount(amount, child_index, expected):
    assert views._apply_child_discount(amount, child_index) == expected


def _submit_data(*, students=1, aid_intent="not_applying"):
    return SimpleNamespace(
        students=[{} for _ in range(students)],
        financial_aid_interest={"intent": aid_intent},
    )


def test_financial_aid_fee_required_only_for_applying(monkeypatch):
    monkeypatch.setattr(views, "FINANCIAL_AID_FEE_USD", Decimal("35.00"))

    assert views._financial_aid_fee_required(_submit_data(aid_intent="applying")) is True
    assert views._financial_aid_fee_required(_submit_data(aid_intent=" Applying ")) is True
    assert views._financial_aid_fee_required(_submit_data(aid_intent="considering")) is False
    assert views._financial_aid_fee_required(_submit_data(aid_intent="")) is False


def test_zero_fees_disable_required_flags(monkeypatch):
    monkeypatch.setattr(views, "APPLICATION_FEE_USD", Decimal("0"))
    monkeypatch.setattr(views, "FINANCIAL_AID_FEE_USD", Decimal("0"))
    monkeypatch.setattr(views, "ENROLLMENT_FEE_USD", Decimal("0"))

    data = _submit_data(aid_intent="applying")
    assert views._application_fee_required() is False
    assert views._financial_aid_fee_required(data) is False
    assert views._enrollment_fee_required() is False


def test_fee_rows_use_larger_of_students_or_application_ids(monkeypatch):
    monkeypatch.setattr(views, "APPLICATION_FEE_USD", Decimal("100.00"))
    monkeypatch.setattr(views, "FINANCIAL_AID_FEE_USD", Decimal("40.00"))
    monkeypatch.setattr(views, "ENROLLMENT_FEE_USD", Decimal("20.00"))

    rows = views._fee_rows_for_household(
        _submit_data(students=3, aid_intent="applying"),
        ["app-1", "app-2"],
    )

    assert rows == [
        {
            "child_index": 1,
            "application_id": "app-1",
            "discount_percent": 0,
            "application_fee": "100.00",
            "financial_aid_fee": "40.00",
            "enrollment_fee": "20.00",
            "total": "160.00",
        },
        {
            "child_index": 2,
            "application_id": "app-2",
            "discount_percent": 25,
            "application_fee": "75.00",
            "financial_aid_fee": "30.00",
            "enrollment_fee": "15.00",
            "total": "120.00",
        },
        {
            "child_index": 3,
            "application_id": None,
            "discount_percent": 50,
            "application_fee": "50.00",
            "financial_aid_fee": "20.00",
            "enrollment_fee": "10.00",
            "total": "80.00",
        },
    ]


def test_fee_config_payloads(monkeypatch):
    monkeypatch.setattr(views, "APPLICATION_FEE_USD", Decimal("85.00"))
    monkeypatch.setattr(views, "FINANCIAL_AID_FEE_USD", Decimal("35.00"))
    monkeypatch.setattr(views, "ENROLLMENT_FEE_USD", Decimal("250.00"))

    application = views._application_fee_config()
    financial_aid = views._financial_aid_fee_config(_submit_data(aid_intent="applying"))
    enrollment = views._enrollment_fee_config()

    assert application["required"] is True
    assert application["amount"] == "85.00"
    assert application["currency"] == "USD"
    assert application["discount_policy"]["tiers"][-1] == {
        "child_index": 5,
        "discount_percent": 100,
        "applies_to": "and_above",
    }
    assert financial_aid == {"required": True, "amount": "35.00", "currency": "USD"}
    assert enrollment == {"required": True, "amount": "250.00", "currency": "USD"}


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
