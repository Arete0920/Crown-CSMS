from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from applications import views_admissions as views


class QuerySequence:
    def __init__(self, *, exact=None, current=None, latest=None, items=()):
        self.exact = exact
        self.current = current
        self.latest = latest
        self.items = list(items)
        self.filters = []

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        if "name" in kwargs:
            return SimpleNamespace(first=lambda: self.exact)
        if kwargs.get("is_current") is True:
            return SimpleNamespace(first=lambda: self.current)
        return self

    def order_by(self, *args):
        return SimpleNamespace(first=lambda: self.latest)

    def __iter__(self):
        return iter(self.items)


def app(*, status="DRAFT", household_id=None):
    return SimpleNamespace(
        id=uuid4(),
        school_id=uuid4(),
        status=status,
        household_id=household_id,
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [(1, 3, "0.33"), (2, 3, "0.67"), (5, 0, "0.00"), (5, -1, "0.00")],
)
def test_rate_rounds_and_handles_nonpositive_denominators(numerator, denominator, expected):
    assert views._rate(numerator, denominator) == expected


def test_academic_year_name_normalizes_unicode_dashes_and_whitespace():
    assert views._normalize_ay_name(" 2027\u20132028 ") == "2027-2028"
    assert views._normalize_ay_name("2027\u20142028") == "2027-2028"
    assert views._normalize_ay_name("") == ""


def test_find_academic_year_prefers_exact_match():
    exact = SimpleNamespace(name="2027-2028")
    qs = QuerySequence(exact=exact, items=[SimpleNamespace(name="2027\u20132028")])

    assert views._find_academic_year_by_name(qs, "2027-2028") is exact


def test_find_academic_year_falls_back_to_normalized_match():
    normalized = SimpleNamespace(name="2027\u20132028")
    qs = QuerySequence(items=[SimpleNamespace(name="2026-2027"), normalized])

    assert views._find_academic_year_by_name(qs, "2027-2028") is normalized
    assert views._find_academic_year_by_name(QuerySequence(items=[]), "missing") is None


def test_academic_year_window_uses_explicit_match(monkeypatch):
    year = SimpleNamespace(name="2027-2028", start_date=date(2027, 8, 1), end_date=date(2028, 6, 1))
    qs = QuerySequence(exact=year)
    monkeypatch.setattr(views.AcademicYear.objects, "filter", lambda **kwargs: qs)

    assert views._get_academic_year_window("school-1", "2027-2028") == (
        "2027-2028",
        date(2027, 8, 1),
        date(2028, 6, 1),
        True,
    )


def test_academic_year_window_uses_current_then_latest_and_handles_empty(monkeypatch):
    current = SimpleNamespace(name="current", start_date=date(2026, 8, 1), end_date=date(2027, 6, 1))
    monkeypatch.setattr(views.AcademicYear.objects, "filter", lambda **kwargs: QuerySequence(current=current))
    assert views._get_academic_year_window("school-1", None)[0] == "current"

    latest = SimpleNamespace(name="latest", start_date=date(2025, 8, 1), end_date=date(2026, 6, 1))
    monkeypatch.setattr(views.AcademicYear.objects, "filter", lambda **kwargs: QuerySequence(latest=latest))
    assert views._get_academic_year_window("school-1", None)[0] == "latest"

    monkeypatch.setattr(views.AcademicYear.objects, "filter", lambda **kwargs: QuerySequence())
    assert views._get_academic_year_window("school-1", None) == ("unknown", None, None, False)
    assert views._get_academic_year_window("school-1", "missing") == ("missing", None, None, True)


@pytest.mark.parametrize(
    ("status", "inquiry", "scheduled", "completed", "decision", "enrolled", "expected"),
    [
        ("DRAFT", False, False, False, None, True, "enrolled"),
        ("DRAFT", False, False, False, "accepted", False, "accepted"),
        ("DRAFT", False, False, False, "waitlisted", False, "waitlisted"),
        ("DRAFT", False, False, False, "declined", False, "declined"),
        ("IN_REVIEW", False, False, False, None, False, "in_review"),
        ("SUBMITTED", False, False, False, None, False, "application_submitted"),
        ("DRAFT", True, True, True, None, False, "tour_completed"),
        ("DRAFT", True, True, False, None, False, "tour_scheduled"),
        ("DRAFT", True, False, False, None, False, "inquiry"),
        ("DRAFT", False, False, False, None, False, "application_started"),
        ("DECIDED", False, False, False, None, False, "declined"),
        ("UNKNOWN", False, False, False, None, False, "application_started"),
    ],
)
def test_compute_stage_applies_documented_precedence(
    status, inquiry, scheduled, completed, decision, enrolled, expected
):
    assert views._compute_stage(
        app(status=status), inquiry, scheduled, completed, decision, enrolled
    ) == expected


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"decision": "accepted"}, "accepted"),
        ({"decision": "waitlisted"}, "waitlisted"),
        ({"decision": "declined"}, "declined"),
        ({"decision": "unknown"}, None),
        ({}, None),
        (None, None),
    ],
)
def test_decision_from_payload_accepts_only_known_values(payload, expected):
    assert views._decision_from_payload(payload) == expected


def test_application_post_acceptance_short_circuits_on_enrollment(monkeypatch):
    first = MagicMock()
    first.exists.return_value = True
    filter_mock = MagicMock(return_value=first)
    monkeypatch.setattr(views.ApplicationEvent.objects, "filter", filter_mock)

    assert views._application_is_post_acceptance(app()) is True
    assert filter_mock.call_count == 1


def test_application_post_acceptance_checks_accepted_decision(monkeypatch):
    enrollment = MagicMock()
    enrollment.exists.return_value = False
    decision = MagicMock()
    decision.exists.return_value = True
    monkeypatch.setattr(views.ApplicationEvent.objects, "filter", MagicMock(side_effect=[enrollment, decision]))

    assert views._application_is_post_acceptance(app()) is True


def test_default_enrollment_state_reflects_acceptance(monkeypatch):
    candidate = app()
    monkeypatch.setattr(views, "_application_is_post_acceptance", lambda value: False)
    assert views._default_enrollment_state_for_application(candidate) == {
        "contract_status": views.CONTRACT_NOT_APPLICABLE,
        "deposit_status": views.DEPOSIT_NOT_APPLICABLE,
    }

    monkeypatch.setattr(views, "_application_is_post_acceptance", lambda value: True)
    assert views._default_enrollment_state_for_application(candidate) == {
        "contract_status": views.CONTRACT_NOT_STARTED,
        "deposit_status": views.DEPOSIT_PENDING,
    }


def test_aid_sync_returns_default_without_household_or_award(monkeypatch):
    assert views._aid_sync_state_for_application(app())["aid_award_count"] == 0

    candidate = app(household_id=uuid4())
    monkeypatch.setattr(views, "build_award_summary_by_household", lambda **kwargs: {})
    assert views._aid_sync_state_for_application(candidate)["aid_award_status"] == "not_recorded"


def test_aid_sync_distinguishes_pending_and_post_acceptance(monkeypatch):
    household_id = uuid4()
    candidate = app(household_id=household_id)
    monkeypatch.setattr(
        views,
        "build_award_summary_by_household",
        lambda **kwargs: {household_id: {"count": "2"}},
    )
    monkeypatch.setattr(views, "_application_is_post_acceptance", lambda value: False)
    pending = views._aid_sync_state_for_application(candidate)
    assert pending == {
        "aid_award_status": "award_recorded",
        "aid_contract_sync_status": "pending_acceptance",
        "aid_billing_sync_status": "pending_acceptance",
        "aid_award_count": 2,
    }

    monkeypatch.setattr(views, "_application_is_post_acceptance", lambda value: True)
    ready = views._aid_sync_state_for_application(candidate)
    assert ready["aid_contract_sync_status"] == "ready_for_contract_adjustment"
    assert ready["aid_billing_sync_status"] == "ready_for_billing_application"


def test_lifecycle_chain_reports_pending_ready_in_progress_and_completed(monkeypatch):
    candidate = app()

    def run(events, post_acceptance):
        results = iter(events)
        monkeypatch.setattr(
            views.ApplicationEvent.objects,
            "filter",
            lambda **kwargs: SimpleNamespace(exists=lambda: next(results)),
        )
        monkeypatch.setattr(views, "_application_is_post_acceptance", lambda value: post_acceptance)
        return views._lifecycle_chain_state_for_application(candidate)

    assert run([False, False, False], False) == {
        "applicant_to_student_status": "pending",
        "classroom_readiness_status": "pending",
        "parent_portal_activation_status": "pending",
    }
    assert run([False, False, False], True)["applicant_to_student_status"] == "ready"
    assert run([True, False, False], True) == {
        "applicant_to_student_status": "completed",
        "classroom_readiness_status": "in_progress",
        "parent_portal_activation_status": "in_progress",
    }
    assert run([True, True, True], True) == {
        "applicant_to_student_status": "completed",
        "classroom_readiness_status": "completed",
        "parent_portal_activation_status": "completed",
    }


def test_latest_enrollment_state_composes_defaults_and_payload(monkeypatch):
    candidate = app()
    monkeypatch.setattr(views, "_aid_sync_state_for_application", lambda value: {"aid_award_count": 1})
    monkeypatch.setattr(views, "_lifecycle_chain_state_for_application", lambda value: {"applicant_to_student_status": "ready"})
    monkeypatch.setattr(
        views,
        "_default_enrollment_state_for_application",
        lambda value: {"contract_status": "not_started", "deposit_status": "pending"},
    )

    latest_query = MagicMock()
    latest_query.order_by.return_value.first.return_value = None
    monkeypatch.setattr(views.ApplicationEvent.objects, "filter", MagicMock(return_value=latest_query))
    baseline = views._latest_enrollment_state_for_application(candidate)
    assert baseline["contract_status"] == "not_started"
    assert baseline["aid_award_count"] == 1

    latest_query.order_by.return_value.first.return_value = SimpleNamespace(payload="invalid")
    assert views._latest_enrollment_state_for_application(candidate) == baseline

    latest_query.order_by.return_value.first.return_value = SimpleNamespace(
        payload={
            "contract_status": "signed",
            "deposit_status": "paid",
            "note": "verified",
            "transition_reason": "family completed",
            "owner_assignment": "admissions-director",
            "trace_id": "trace-1",
        }
    )
    updated = views._latest_enrollment_state_for_application(candidate)
    assert updated["contract_status"] == "signed"
    assert updated["deposit_status"] == "paid"
    assert updated["trace_id"] == "trace-1"


def test_transition_validation_allows_same_or_graph_edge_and_rejects_other():
    graph = {"pending": {"paid", "waived"}}
    assert views._validate_state_transition(current="pending", requested="pending", graph=graph, state_name="deposit") is None
    assert views._validate_state_transition(current="pending", requested="paid", graph=graph, state_name="deposit") is None
    assert views._validate_state_transition(current="pending", requested="refunded", graph=graph, state_name="deposit") == (
        "Invalid deposit transition: pending -> refunded. Allowed: ['paid', 'waived']"
    )


def test_application_has_event_is_tenant_and_application_scoped(monkeypatch):
    query = MagicMock()
    query.exists.return_value = True
    filter_mock = MagicMock(return_value=query)
    monkeypatch.setattr(views.ApplicationEvent.objects, "filter", filter_mock)
    candidate = app()

    assert views._application_has_event(candidate, "decision_made") is True
    filter_mock.assert_called_once_with(
        school_id=candidate.school_id,
        application_id=candidate.id,
        event_type="decision_made",
    )


def test_legacy_bridge_guards_handle_missing_inputs():
    assert views._resolve_or_create_legacy_family(school=SimpleNamespace(), household=None) is None
    assert views._resolve_legacy_grade_level(school=SimpleNamespace(), grade_code="") is None
    assert views._resolve_or_create_legacy_student(
        school=SimpleNamespace(), family=None, applicant=SimpleNamespace(), ordinal=0
    ) is None
    assert views._create_legacy_conversion_session(
        school=SimpleNamespace(), actor_user=None, academic_year=SimpleNamespace(), application_ids=[], target_status="ENROLLED"
    ) is None
