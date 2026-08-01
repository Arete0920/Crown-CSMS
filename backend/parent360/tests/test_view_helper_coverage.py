from decimal import Decimal
from types import SimpleNamespace

from parent360.api import views


def test_safe_decimal_converts_supported_values_and_uses_default_for_invalid_input():
    assert views._safe_decimal("12.50") == Decimal("12.50")
    assert views._safe_decimal(7) == Decimal("7")
    assert views._safe_decimal(None) == Decimal("0")
    assert views._safe_decimal("not-a-number", Decimal("9.25")) == Decimal("9.25")


def test_compute_weighted_percent_ignores_nonpositive_possible_points():
    grade_rows = [
        SimpleNamespace(points_earned="18", points_possible="20"),
        SimpleNamespace(points_earned="9", points_possible="10"),
        SimpleNamespace(points_earned="100", points_possible="0"),
        SimpleNamespace(points_earned=None, points_possible=None),
    ]

    assert views._compute_weighted_percent(grade_rows) == Decimal("90")


def test_compute_weighted_percent_returns_none_without_positive_possible_points():
    grade_rows = [
        SimpleNamespace(points_earned="5", points_possible="0"),
        SimpleNamespace(points_earned="5", points_possible="-1"),
        SimpleNamespace(points_earned=None, points_possible=None),
    ]

    assert views._compute_weighted_percent(grade_rows) is None


def test_percent_to_gpa_proxy_covers_boundaries_and_missing_percent():
    assert views._percent_to_gpa_proxy(None) is None
    assert views._percent_to_gpa_proxy(Decimal("93")) == Decimal("4.0")
    assert views._percent_to_gpa_proxy(Decimal("90")) == Decimal("3.7")
    assert views._percent_to_gpa_proxy(Decimal("65")) == Decimal("1.0")
    assert views._percent_to_gpa_proxy(Decimal("64.99")) == Decimal("0.0")


def test_build_checklist_by_app_aggregates_completion_and_missing_items():
    statuses = SimpleNamespace(
        APPROVED="approved",
        SUBMITTED="submitted",
        UNDER_REVIEW="under_review",
        MISSING="missing",
        REJECTED="rejected",
    )
    rows = [
        {
            "application_id": 1,
            "status": "approved",
            "item_key": "birth_certificate",
            "title": "Birth Certificate",
            "office": "admissions",
            "submitted_at": None,
        },
        {
            "application_id": 1,
            "status": "missing",
            "item_key": "transcript",
            "title": "Transcript",
            "office": "registrar",
            "submitted_at": None,
        },
        {
            "application_id": 2,
            "status": "under_review",
            "item_key": "recommendation",
            "title": "Recommendation",
            "office": "admissions",
            "submitted_at": None,
        },
    ]

    result = views._build_checklist_by_app(rows, statuses)

    assert result[1]["required_total"] == 2
    assert result[1]["complete_count"] == 1
    assert result[1]["missing_count"] == 1
    assert result[1]["pending_items"] == [
        {
            "item_key": "transcript",
            "title": "Transcript",
            "office": "registrar",
            "status": "missing",
            "submitted_at": None,
        }
    ]
    assert result[2] == {
        "required_total": 1,
        "complete_count": 1,
        "missing_count": 0,
        "pending_items": [],
    }


def test_build_enrollment_state_by_app_keeps_latest_event_per_application():
    class Events:
        def filter(self, **kwargs):
            assert kwargs == {"event_type": "enrollment_state_updated"}
            return self

        def order_by(self, *fields):
            assert fields == ("application_id", "-created_at")
            return self

        def values(self, *fields):
            assert fields == ("application_id", "payload")
            return [
                {
                    "application_id": 1,
                    "payload": {
                        "contract_status": "signed",
                        "deposit_status": "paid",
                        "note": "complete",
                    },
                },
                {
                    "application_id": 1,
                    "payload": {"contract_status": "pending"},
                },
                {"application_id": 2, "payload": None},
            ]

    result = views._build_enrollment_state_by_app(Events())

    assert result[1] == {
        "contract_status": "signed",
        "deposit_status": "paid",
        "note": "complete",
        "transition_reason": "",
    }
    assert result[2] == {
        "contract_status": "not_started",
        "deposit_status": "pending",
        "note": "",
        "transition_reason": "",
    }


def test_build_decision_by_app_keeps_only_supported_decisions():
    class Events:
        def filter(self, **kwargs):
            assert kwargs == {"event_type": "decision_made"}
            return self

        def values(self, *fields):
            assert fields == ("application_id", "payload")
            return [
                {"application_id": 1, "payload": {"decision": "accepted"}},
                {"application_id": 2, "payload": {"decision": "waitlisted"}},
                {"application_id": 3, "payload": {"decision": "declined"}},
                {"application_id": 4, "payload": {"decision": "draft"}},
                {"application_id": 5, "payload": None},
            ]

    assert views._build_decision_by_app(Events()) == {
        1: "accepted",
        2: "waitlisted",
        3: "declined",
    }
