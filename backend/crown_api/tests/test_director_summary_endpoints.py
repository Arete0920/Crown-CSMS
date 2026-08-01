from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from crown_api import director_views as views


SUMMARY_VIEWS = (
    (views.aid_summary, "/api/director/aid/summary/"),
    (views.finance_summary, "/api/director/finance/summary/"),
    (views.registrar_summary, "/api/director/registrar/summary/"),
)


def _request(path, user=None):
    request = APIRequestFactory().get(path)
    force_authenticate(
        request,
        user=user or SimpleNamespace(is_authenticated=True, is_superuser=True, id=1),
    )
    return request


@pytest.mark.parametrize("summary_view,path", SUMMARY_VIEWS)
def test_director_summary_requires_school_id(summary_view, path):
    response = summary_view(_request(path))

    assert response.status_code == 400
    assert response.data == {"detail": "school_id is required"}


@pytest.mark.parametrize("summary_view,path", SUMMARY_VIEWS)
def test_director_summary_denies_unauthorized_user(monkeypatch, summary_view, path):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: False)

    response = summary_view(_request(f"{path}?school_id=school-a"))

    assert response.status_code == 403
    assert response.data == {"detail": "Forbidden"}


@pytest.mark.parametrize("summary_view,path", SUMMARY_VIEWS)
def test_director_summary_rejects_unresolved_academic_year(
    monkeypatch, summary_view, path
):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    resolve = MagicMock(return_value=None)
    monkeypatch.setattr(views, "resolve_academic_year", resolve)

    response = summary_view(
        _request(f"{path}?school_id=school-a&academic_year_id=year-a")
    )

    assert response.status_code == 400
    assert response.data == {"detail": "academic_year not found for school"}
    resolve.assert_called_once_with("school-a", "year-a")


def test_aid_summary_scopes_all_queries_to_school_and_year(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        lambda school_id, academic_year_id: SimpleNamespace(id="year-a"),
    )

    apps = MagicMock()
    apps.count.return_value = 6
    apps.filter.return_value.count.return_value = 1
    app_manager = MagicMock()
    app_manager.filter.return_value = apps
    monkeypatch.setattr(views.AidApplication, "objects", app_manager)

    awards = MagicMock()
    awards.count.return_value = 4
    awards.filter.return_value.count.return_value = 1
    awards.aggregate.return_value = {"total": 125000}
    award_manager = MagicMock()
    award_manager.filter.return_value = awards
    monkeypatch.setattr(views.AidAward, "objects", award_manager)

    documents = MagicMock()
    documents.count.return_value = 2
    document_manager = MagicMock()
    document_manager.filter.return_value = documents
    monkeypatch.setattr(views.AidDocument, "objects", document_manager)

    response = views.aid_summary(
        _request(
            "/api/director/aid/summary/?school_id=school-a&academic_year_id=year-a"
        )
    )

    assert response.status_code == 200
    assert response.data["applications"]["total"] == 6
    assert response.data["awards"]["total_awarded_cents"] == 125000
    assert response.data["documents"]["missing_documents_count"] == 2
    app_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    award_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    document_manager.filter.assert_called_once_with(
        school_id="school-a",
        aid_application__academic_year_id="year-a",
        received=False,
    )


def test_finance_summary_scopes_all_queries_to_school_and_year(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        lambda school_id, academic_year_id: SimpleNamespace(id="year-a"),
    )

    tuition = MagicMock()
    tuition.count.return_value = 12
    tuition.aggregate.return_value = {"total": 900000}
    tuition_manager = MagicMock()
    tuition_manager.filter.return_value = tuition
    monkeypatch.setattr(views.StudentTuition, "objects", tuition_manager)

    awards = MagicMock()
    awards.aggregate.return_value = {"total": 150000}
    award_manager = MagicMock()
    award_manager.filter.return_value = awards
    monkeypatch.setattr(views.AidAward, "objects", award_manager)

    ledger = MagicMock()
    ledger.filter.return_value.aggregate.return_value = {"total": -100000}
    ledger.aggregate.side_effect = [{"total": -250000}, {"total": 800000}]
    ledger_manager = MagicMock()
    ledger_manager.filter.return_value = ledger
    monkeypatch.setattr(views.LedgerEntry, "objects", ledger_manager)

    response = views.finance_summary(
        _request(
            "/api/director/finance/summary/?school_id=school-a&academic_year_id=year-a"
        )
    )

    assert response.status_code == 200
    assert response.data == {
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
    }
    tuition_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    award_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )
    ledger_manager.filter.assert_called_once_with(
        school_id="school-a", academic_year_id="year-a"
    )


def test_registrar_summary_scopes_enrollment_and_family_queries(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        lambda school_id, academic_year_id: SimpleNamespace(id="year-a"),
    )
    monkeypatch.setattr(
        views.GradeLevel,
        "GRADE_CHOICES",
        (("K", "Kindergarten"), ("01", "Grade 1")),
    )

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

    response = views.registrar_summary(
        _request(
            "/api/director/registrar/summary/?school_id=school-a&academic_year_id=year-a"
        )
    )

    assert response.status_code == 200
    assert response.data == {
        "enrollment": {
            "total_students": 3,
            "by_grade": {"K": 2, "01": 1},
        },
        "families": {"total_families": 2},
    }
    enrollment_manager.filter.assert_called_once_with(
        school_id="school-a",
        academic_year_id="year-a",
        status="ENROLLED",
    )
    family_manager.filter.assert_called_once_with(school_id="school-a")
