from types import SimpleNamespace
from unittest.mock import MagicMock

from rest_framework.test import APIRequestFactory, force_authenticate

from crown_api import director_views as views


def _request(query="", user=None):
    request = APIRequestFactory().get(f"/api/director/dashboard/{query}")
    force_authenticate(
        request,
        user=user or SimpleNamespace(is_authenticated=True, is_superuser=True, id=1),
    )
    return request


def test_director_dashboard_denies_unauthorized_user(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: False)

    response = views.director_dashboard(_request("?school_id=school-a&year_id=year-a"))

    assert response.status_code == 403
    assert response.data == {"error": "Unauthorized. Director access required."}


def test_director_dashboard_requires_school_id(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)

    response = views.director_dashboard(_request("?year_id=year-a"))

    assert response.status_code == 400
    assert response.data == {"detail": "school_id is required"}


def test_director_dashboard_accepts_academic_year_alias_and_rejects_missing_year(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    resolve = MagicMock(return_value=None)
    monkeypatch.setattr(views, "resolve_academic_year", resolve)

    response = views.director_dashboard(
        _request("?school_id=school-a&academic_year_id=year-a")
    )

    assert response.status_code == 400
    assert response.data == {"detail": "academic_year not found for school"}
    resolve.assert_called_once_with("school-a", "year-a")


def test_director_dashboard_scopes_queries_and_serializes_sections(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        lambda school_id, year_id: SimpleNamespace(id="year-a"),
    )
    monkeypatch.setattr(
        views.GradeLevel,
        "GRADE_CHOICES",
        (("K", "Kindergarten"), ("01", "Grade 1")),
    )

    apps = MagicMock()
    apps.count.return_value = 6
    apps.filter.return_value.count.return_value = 1
    app_manager = MagicMock()
    app_manager.filter.return_value = apps
    monkeypatch.setattr(views.AidApplication, "objects", app_manager)

    aid_awards = MagicMock()
    aid_awards.count.return_value = 4
    aid_awards.filter.return_value.count.return_value = 1
    aid_awards.aggregate.return_value = {"total": 125000}
    finance_awards = MagicMock()
    finance_awards.aggregate.return_value = {"total": 150000}
    award_manager = MagicMock()
    award_manager.filter.side_effect = [aid_awards, finance_awards]
    monkeypatch.setattr(views.AidAward, "objects", award_manager)

    documents = MagicMock()
    documents.count.return_value = 2
    document_manager = MagicMock()
    document_manager.filter.return_value = documents
    monkeypatch.setattr(views.AidDocument, "objects", document_manager)

    tuition = MagicMock()
    tuition.count.return_value = 12
    tuition.aggregate.return_value = {"total": 900000}
    tuition_manager = MagicMock()
    tuition_manager.filter.return_value = tuition
    monkeypatch.setattr(views.StudentTuition, "objects", tuition_manager)

    ledger = MagicMock()
    ledger.filter.return_value.aggregate.return_value = {"total": -100000}
    ledger.aggregate.side_effect = [{"total": -250000}, {"total": 800000}]
    ledger_manager = MagicMock()
    ledger_manager.filter.return_value = ledger
    monkeypatch.setattr(views.LedgerEntry, "objects", ledger_manager)

    enrollments = MagicMock()
    enrollments.count.return_value = 3
    enrollments.values.return_value.annotate.return_value = [
        {"grade_level__code": "K", "c": 2},
        {"grade_level__code": "01", "c": 1},
    ]
    enrollment_manager = MagicMock()
    enrollment_manager.filter.return_value = enrollments
    monkeypatch.setattr(views.Enrollment, "objects", enrollment_manager)

    family_manager = MagicMock()
    family_manager.filter.return_value.count.return_value = 2
    monkeypatch.setattr(views.Family, "objects", family_manager)

    response = views.director_dashboard(
        _request("?school_id=school-a&year_id=year-a")
    )

    assert response.status_code == 200
    assert response.data == {
        "meta": {"school_id": "school-a", "year_id": "year-a"},
        "sections": {
            "aid": {
                "applications": {
                    "total": 6,
                    "submitted": 1,
                    "needs_info": 1,
                    "under_review": 1,
                    "approved": 1,
                    "denied": 1,
                },
                "awards": {
                    "total_awards": 4,
                    "offered_not_accepted": 1,
                    "accepted_not_posted": 1,
                    "posted_to_ledger": 1,
                    "total_awarded_cents": 125000,
                },
                "documents": {"missing_documents_count": 2},
            },
            "finance": {
                "tuition": {
                    "students_billed": 12,
                    "gross_tuition_cents": 900000,
                },
                "aid": {
                    "total_aid_awarded_cents": 150000,
                    "total_aid_posted_cents": -100000,
                },
                "ledger": {
                    "net_receivables_cents": 550000,
                    "total_credits_cents": -250000,
                    "total_debits_cents": 800000,
                },
            },
            "registrar": {
                "enrollment": {
                    "total_students": 3,
                    "by_grade": {"K": 2, "01": 1},
                },
                "families": {"total_families": 2},
            },
        },
    }

    app_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    assert award_manager.filter.call_count == 2
    award_manager.filter.assert_any_call(
        school_id="school-a", academic_year_id="year-a"
    )
    document_manager.filter.assert_called_once_with(
        school_id="school-a",
        aid_application__academic_year_id="year-a",
        received=False,
    )
    tuition_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    ledger_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    enrollment_manager.filter.assert_called_once_with(
        school_id="school-a",
        academic_year_id="year-a",
        status="ENROLLED",
    )
    family_manager.filter.assert_called_once_with(school_id="school-a")


def test_director_dashboard_returns_controlled_error_on_internal_failure(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        MagicMock(side_effect=RuntimeError("boom")),
    )
    logger = MagicMock()
    monkeypatch.setattr(views, "logger", logger)

    response = views.director_dashboard(
        _request("?school_id=school-a&year_id=year-a")
    )

    assert response.status_code == 500
    assert response.data == {"error": "Dashboard error"}
    logger.exception.assert_called_once_with("Director dashboard error")
