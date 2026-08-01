from types import SimpleNamespace
from unittest.mock import patch

from applications import views_admissions as admissions


def test_normalize_contract_line_items_filters_and_normalizes_values():
    assert admissions._normalize_contract_line_items(None) == []
    assert admissions._normalize_contract_line_items({"label": "Tuition"}) == []

    long_label = "L" * 140
    long_category = "C" * 60
    result = admissions._normalize_contract_line_items(
        [
            None,
            "invalid",
            {"label": ""},
            {"label": "Bad amount", "amount_cents": "not-a-number"},
            {
                "label": long_label,
                "category": long_category,
                "amount_cents": "12500",
                "meta": {"source": "schedule"},
            },
            {
                "name": "Enrollment Fee",
                "amount_cents": None,
                "meta": "discarded",
            },
        ]
    )

    assert result == [
        {
            "label": long_label[:120],
            "category": long_category.lower()[:48],
            "amount_cents": 12500,
            "meta": {"source": "schedule"},
        },
        {
            "label": "Enrollment Fee",
            "category": "other",
            "amount_cents": 0,
            "meta": {},
        },
    ]


def test_compute_contract_totals_maps_categories_and_calculates_net_obligation():
    totals = admissions._compute_contract_totals(
        [
            {"category": "tuition", "amount_cents": 1_000_000},
            {"category": "fee", "amount_cents": 40_000},
            {"category": "fees", "amount_cents": 10_000},
            {"category": "discount", "amount_cents": 25_000},
            {"category": "aid", "amount_cents": 100_000},
            {"category": "scholarship", "amount_cents": 50_000},
            {"category": "voucher", "amount_cents": 30_000},
            {"category": "tax_credit", "amount_cents": 20_000},
            {"category": "donor", "amount_cents": 15_000},
            {"category": "deposit", "amount_cents": 75_000},
            {"category": "unknown", "amount_cents": 999_999},
        ],
        None,
    )

    assert totals["gross_tuition_cents"] == 1_000_000
    assert totals["fees_cents"] == 50_000
    assert totals["discounts_cents"] == 25_000
    assert totals["aid_cents"] == 100_000
    assert totals["scholarships_cents"] == 50_000
    assert totals["esa_voucher_tax_credit_cents"] == 50_000
    assert totals["donor_assistance_cents"] == 15_000
    assert totals["deposit_cents"] == 75_000
    assert totals["amount_due_today_cents"] == 75_000
    assert totals["net_family_obligation_cents"] == 735_000


def test_compute_contract_totals_honors_valid_declared_overrides_only():
    totals = admissions._compute_contract_totals(
        [
            {"category": "tuition", "amount_cents": 500_000},
            {"category": "deposit", "amount_cents": 50_000},
            {"category": "due_today", "amount_cents": 10_000},
        ],
        {
            "gross_tuition_cents": "600000",
            "fees_cents": "invalid",
            "amount_due_today_cents": "25000",
            "deposit_cents": None,
        },
    )

    assert totals["gross_tuition_cents"] == 600_000
    assert totals["fees_cents"] == 0
    assert totals["deposit_cents"] == 0
    assert totals["amount_due_today_cents"] == 25_000
    assert totals["net_family_obligation_cents"] == 600_000


def test_resolve_requested_contract_status_precedence():
    draft = admissions.EnrollmentContractStatus.DRAFT.value
    issued = admissions.EnrollmentContractStatus.ISSUED.value
    signed = admissions.EnrollmentContractStatus.SIGNED.value

    latest = SimpleNamespace(status=signed)

    assert admissions._resolve_requested_contract_status(
        latest=latest,
        payload={"status": issued.upper()},
        status_hint=draft,
    ) == issued
    assert admissions._resolve_requested_contract_status(
        latest=latest,
        payload={"status": "not-a-status"},
        status_hint=draft,
    ) == draft
    assert admissions._resolve_requested_contract_status(
        latest=latest,
        payload={},
        status_hint=None,
    ) == signed
    assert admissions._resolve_requested_contract_status(
        latest=None,
        payload={},
        status_hint=None,
    ) == admissions.EnrollmentContractStatus.DRAFT


def test_stamp_contract_status_timestamps_sets_only_missing_matching_field():
    moment = object()

    issued = SimpleNamespace(
        status=admissions.EnrollmentContractStatus.ISSUED.value,
        issued_at=None,
        signed_at="existing-signed",
        countersigned_at="existing-countersigned",
    )
    with patch.object(admissions.timezone, "now", return_value=moment):
        admissions._stamp_contract_status_timestamps(issued)
    assert issued.issued_at is moment
    assert issued.signed_at == "existing-signed"
    assert issued.countersigned_at == "existing-countersigned"

    signed = SimpleNamespace(
        status=admissions.EnrollmentContractStatus.SIGNED.value,
        issued_at="existing-issued",
        signed_at=None,
        countersigned_at=None,
    )
    with patch.object(admissions.timezone, "now", return_value=moment):
        admissions._stamp_contract_status_timestamps(signed)
    assert signed.issued_at == "existing-issued"
    assert signed.signed_at is moment
    assert signed.countersigned_at is None

    countersigned = SimpleNamespace(
        status=admissions.EnrollmentContractStatus.COUNTERSIGNED.value,
        issued_at=None,
        signed_at=None,
        countersigned_at=None,
    )
    with patch.object(admissions.timezone, "now", return_value=moment):
        admissions._stamp_contract_status_timestamps(countersigned)
    assert countersigned.countersigned_at is moment
