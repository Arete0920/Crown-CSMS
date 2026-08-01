from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from types import SimpleNamespace

import pytest

from parent360.api import views


@pytest.mark.parametrize(
    ("status", "decision", "enrolled", "expected"),
    [
        ("STARTED", None, True, "enrolled"),
        ("STARTED", "accepted", False, "accepted"),
        ("STARTED", "waitlisted", False, "waitlisted"),
        ("STARTED", "declined", False, "declined"),
        ("IN_REVIEW", None, False, "in_review"),
        ("SUBMITTED", None, False, "application_submitted"),
        ("STARTED", None, False, "application_started"),
    ],
)
def test_admissions_lifecycle_stage(status, decision, enrolled, expected):
    app = SimpleNamespace(id="app-1", status=status)
    enrolled_ids = {"app-1"} if enrolled else set()
    assert views._admissions_lifecycle_stage(app, decision, enrolled_ids) == expected


@pytest.mark.parametrize(
    ("intent", "expected"),
    [
        ("applying", "Aid Application Started"),
        ("not_applying", "Not Applying"),
        ("undecided", "Aid Interest Indicated"),
        ("other", "Aid Interest Indicated"),
        (None, "Aid Interest Indicated"),
    ],
)
def test_admissions_financial_aid_status(intent, expected):
    flags = {"financial_aid_interest": {"intent": intent}} if intent is not None else {}
    assert views._admissions_financial_aid_status(flags) == expected


def test_contract_and_deposit_status_only_applies_after_acceptance():
    state = {"contract_status": "signed", "deposit_status": "paid"}
    assert views._admissions_contract_and_deposit_status(state, "accepted") == ("signed", "paid")
    assert views._admissions_contract_and_deposit_status({}, "enrolled") == ("not_started", "pending")
    assert views._admissions_contract_and_deposit_status(state, "in_review") == (
        "not_applicable",
        "not_applicable",
    )


@pytest.mark.parametrize(
    ("stage", "label"),
    [
        ("in_review", "Under Review"),
        ("application_submitted", "Application Submitted"),
        ("accepted", "Accepted"),
        ("waitlisted", "Waitlisted"),
        ("declined", "Declined"),
        ("enrolled", "Enrollment Complete"),
        ("application_started", "Application Started"),
    ],
)
def test_admissions_status_labels(stage, label):
    assert views._admissions_status_labels(stage)[0] == label


def test_admissions_assessment_context_required_optional_and_captured(monkeypatch):
    flags = {"preferred_tour_window": "Morning", "preferred_interview_mode": "Teams"}
    captured = views._admissions_assessment_context(flags)
    assert captured == (
        True,
        "Morning",
        "Teams",
        "scheduling_in_progress",
        "Admissions team will confirm your assessment/interview slot.",
    )

    monkeypatch.setattr(views, "ADMISSIONS_ASSESSMENT_REQUIRED", True)
    required = views._admissions_assessment_context({})
    assert required[0] is False
    assert required[3] == "required"

    monkeypatch.setattr(views, "ADMISSIONS_ASSESSMENT_REQUIRED", False)
    optional = views._admissions_assessment_context({})
    assert optional[3] == "optional"


def test_admissions_deadline_depends_on_stage():
    submitted = datetime(2026, 8, 1, 12, 0, tzinfo=dt_timezone.utc)
    app = SimpleNamespace(submitted_at=submitted)
    assert views._admissions_deadline(app, "application_submitted") == "2026-08-03T12:00:00+00:00"
    assert views._admissions_deadline(app, "in_review") == "2026-08-03T12:00:00+00:00"
    assert views._admissions_deadline(app, "accepted") == "2026-08-08T12:00:00+00:00"
    assert views._admissions_deadline(app, "application_started") is None
    assert views._admissions_deadline(SimpleNamespace(submitted_at=None), "accepted") is None
