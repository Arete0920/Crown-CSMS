from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from crown_api import director_views as views


def _user(*, authenticated=True, superuser=False, user_id=1):
    return SimpleNamespace(
        is_authenticated=authenticated,
        is_superuser=superuser,
        id=user_id,
    )


def _request(user):
    return SimpleNamespace(user=user)


def test_crown_director_allowed_honors_explicit_dev_override(monkeypatch):
    monkeypatch.setattr(views.settings, "CROWN_DEV_OPEN_API", True, raising=False)

    assert views.crown_director_allowed(_request(None)) is True


def test_crown_director_allowed_allows_superuser(monkeypatch):
    monkeypatch.setattr(views.settings, "CROWN_DEV_OPEN_API", False, raising=False)

    assert views.crown_director_allowed(_request(_user(superuser=True))) is True


@pytest.mark.parametrize(
    "user",
    [
        None,
        _user(authenticated=False),
        _user(user_id=None),
    ],
)
def test_crown_director_allowed_fails_closed_without_valid_identity(monkeypatch, user):
    monkeypatch.setattr(views.settings, "CROWN_DEV_OPEN_API", False, raising=False)

    assert views.crown_director_allowed(_request(user)) is False


def test_crown_director_allowed_checks_authoritative_role_codes(monkeypatch):
    monkeypatch.setattr(views.settings, "CROWN_DEV_OPEN_API", False, raising=False)
    query = MagicMock()
    query.filter.return_value.exists.return_value = True
    monkeypatch.setattr(views.UserRole, "objects", query)

    assert views.crown_director_allowed(_request(_user(user_id=42))) is True
    query.filter.assert_called_once_with(
        user_id=42,
        role_code__in=views.ALLOWED_ROLE_CODES,
    )


def test_user_has_director_role_fails_closed_for_missing_identity():
    assert views.user_has_director_role(None) is False
    assert views.user_has_director_role(_user(authenticated=False)) is False
    assert views.user_has_director_role(_user(user_id=None)) is False


def test_user_has_director_role_allows_superuser():
    assert views.user_has_director_role(_user(superuser=True)) is True


def test_user_has_director_role_queries_allowed_roles(monkeypatch):
    query = MagicMock()
    query.filter.return_value.exists.return_value = False
    monkeypatch.setattr(views.UserRole, "objects", query)

    assert views.user_has_director_role(_user(user_id=77)) is False
    query.filter.assert_called_once_with(
        user_id=77,
        role_code__in=views.ALLOWED_ROLE_CODES,
    )


def test_resolve_academic_year_scopes_explicit_id_to_school(monkeypatch):
    expected = SimpleNamespace(id=9)
    query = MagicMock()
    query.filter.return_value.first.return_value = expected
    monkeypatch.setattr(views.AcademicYear, "objects", query)

    result = views.resolve_academic_year("school-a", academic_year_id="year-9")

    assert result is expected
    query.filter.assert_called_once_with(pk="year-9", school_id="school-a")
    query.filter.return_value.first.assert_called_once_with()


def test_resolve_academic_year_uses_latest_current_year(monkeypatch):
    expected = SimpleNamespace(id=10)
    query = MagicMock()
    query.filter.return_value.order_by.return_value.first.return_value = expected
    monkeypatch.setattr(views.AcademicYear, "objects", query)

    result = views.resolve_academic_year("school-a")

    assert result is expected
    query.filter.assert_called_once_with(school_id="school-a", is_current=True)
    query.filter.return_value.order_by.assert_called_once_with("-start_date")


def test_priority_snapshot_requires_academic_year():
    assert views.build_director_priority_snapshot("school-a", None) is None


def test_priority_snapshot_scopes_and_serializes_each_queue(monkeypatch):
    academic_year = SimpleNamespace(id="year-a")
    needs_family = SimpleNamespace(family_name="Needs Family")
    review_family = SimpleNamespace(family_name="Review Family")
    needs_app = SimpleNamespace(id="app-needs", family=needs_family, submitted_at="needs-at")
    review_app = SimpleNamespace(id="app-review", family=review_family, submitted_at="review-at")

    admissions_manager = MagicMock()
    needs_qs = MagicMock()
    review_qs = MagicMock()
    admissions_manager.filter.side_effect = [needs_qs, review_qs]
    needs_qs.select_related.return_value.order_by.return_value.__getitem__.return_value = [needs_app]
    review_qs.select_related.return_value.order_by.return_value.__getitem__.return_value = [review_app]
    monkeypatch.setattr(views.AdmissionsApplication, "objects", admissions_manager)

    aid_apps_manager = MagicMock()
    aid_apps_qs = MagicMock()
    aid_apps_manager.filter.return_value = aid_apps_qs
    aid_apps_qs.order_by.return_value.values.return_value.__getitem__.return_value = [
        {"id": "aid-app", "status": views.AidApplication.STATUS_NEEDS_INFO}
    ]
    monkeypatch.setattr(views.AidApplication, "objects", aid_apps_manager)

    awards_manager = MagicMock()
    awards_qs = MagicMock()
    awards_manager.filter.return_value = awards_qs
    awards_qs.order_by.return_value.values.return_value.__getitem__.return_value = [
        {"id": "award-a", "awarded_cents": 50000}
    ]
    monkeypatch.setattr(views.AidAward, "objects", awards_manager)

    ledger_manager = MagicMock()
    ledger_qs = MagicMock()
    ledger_manager.filter.return_value = ledger_qs
    ledger_qs.values.return_value.annotate.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = [
        {"family_id": "family-a", "family__family_name": "Balance Family", "balance_cents": 25000}
    ]
    monkeypatch.setattr(views.LedgerEntry, "objects", ledger_manager)

    snapshot = views.build_director_priority_snapshot("school-a", academic_year)

    assert snapshot == {
        "aid": {
            "needs_info": [
                {"id": "aid-app", "status": views.AidApplication.STATUS_NEEDS_INFO}
            ],
            "accepted_not_posted": [
                {"id": "award-a", "awarded_cents": 50000}
            ],
        },
        "admissions": {
            "needs_info_applications": [
                {
                    "application_id": "app-needs",
                    "family": "Needs Family",
                    "submitted_at": "needs-at",
                }
            ],
            "under_review_applications": [
                {
                    "application_id": "app-review",
                    "family": "Review Family",
                    "submitted_at": "review-at",
                }
            ],
        },
        "finance": {
            "balance_due": [
                {
                    "family_id": "family-a",
                    "family__family_name": "Balance Family",
                    "balance_cents": 25000,
                }
            ]
        },
    }

    admissions_manager.filter.assert_any_call(
        school_id="school-a",
        academic_year=academic_year,
        status=views.AdmissionsApplication.STATUS_NEEDS_INFO,
    )
    admissions_manager.filter.assert_any_call(
        school_id="school-a",
        academic_year=academic_year,
        status=views.AdmissionsApplication.STATUS_UNDER_REVIEW,
    )
    aid_apps_manager.filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        status=views.AidApplication.STATUS_NEEDS_INFO,
    )
    awards_manager.filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        decision_status=views.AidAward.DECISION_ACCEPTED,
        ledger_entry__isnull=True,
    )
    ledger_manager.filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        family__isnull=False,
    )
