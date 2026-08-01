from types import SimpleNamespace
from unittest.mock import MagicMock, call

from rest_framework.test import APIRequestFactory, force_authenticate

from crown_api import director_views as views


def _request(query="", user=None):
    request = APIRequestFactory().get(f"/api/director/priority/{query}")
    force_authenticate(
        request,
        user=user or SimpleNamespace(is_authenticated=True, is_superuser=True, id=1),
    )
    return request


def _empty_related_queryset():
    queryset = MagicMock()
    queryset.select_related.return_value.order_by.return_value.__getitem__.return_value = []
    return queryset


def _configure_empty_priority_sources(monkeypatch, *, family_balances=None, missing_grade=0):
    aid_app_manager = MagicMock()
    aid_app_manager.filter.side_effect = [
        _empty_related_queryset(),
        _empty_related_queryset(),
    ]
    monkeypatch.setattr(views.AidApplication, "objects", aid_app_manager)

    award_manager = MagicMock()
    award_manager.filter.return_value = _empty_related_queryset()
    monkeypatch.setattr(views.AidAward, "objects", award_manager)

    admissions_manager = MagicMock()
    admissions_manager.filter.side_effect = [
        _empty_related_queryset(),
        _empty_related_queryset(),
    ]
    monkeypatch.setattr(views.AdmissionsApplication, "objects", admissions_manager)

    balance_rows = family_balances or []
    ledger_queryset = MagicMock()
    ledger_queryset.values.return_value.annotate.return_value.order_by.return_value.__getitem__.return_value = balance_rows
    ledger_manager = MagicMock()
    ledger_manager.filter.return_value = ledger_queryset
    monkeypatch.setattr(views.LedgerEntry, "objects", ledger_manager)

    tuition_manager = MagicMock()
    tuition_manager.filter.return_value.count.return_value = 4
    monkeypatch.setattr(views.StudentTuition, "objects", tuition_manager)

    enrollment_queryset = MagicMock()
    enrollment_queryset.filter.return_value.count.return_value = missing_grade
    enrollment_manager = MagicMock()
    enrollment_manager.filter.return_value = enrollment_queryset
    monkeypatch.setattr(views.Enrollment, "objects", enrollment_manager)

    return {
        "aid_apps": aid_app_manager,
        "awards": award_manager,
        "admissions": admissions_manager,
        "ledger": ledger_manager,
        "tuition": tuition_manager,
        "enrollment": enrollment_manager,
        "enrollment_queryset": enrollment_queryset,
    }


def test_director_priority_denies_unauthorized_user(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: False)
    resolve = MagicMock()
    monkeypatch.setattr(views, "resolve_academic_year", resolve)

    response = views.director_priority(
        _request("?school_id=school-a&year_id=year-a")
    )

    assert response.status_code == 403
    assert response.data == {"error": "Unauthorized. Director access required."}
    resolve.assert_not_called()


def test_director_priority_accepts_academic_year_alias_and_scopes_empty_queues(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    academic_year = SimpleNamespace(id="year-a")
    resolve = MagicMock(return_value=academic_year)
    monkeypatch.setattr(views, "resolve_academic_year", resolve)
    managers = _configure_empty_priority_sources(monkeypatch)

    response = views.director_priority(
        _request("?school_id=school-a&academic_year_id=year-a")
    )

    assert response.status_code == 200
    assert response.data == {
        "meta": {"school_id": "school-a", "year_id": "year-a"},
        "worklist_top_10": [],
        "aid": {
            "needs_info_applications": [],
            "under_review_applications": [],
            "accepted_not_posted_awards": [],
        },
        "admissions": {
            "needs_info_applications": [],
            "under_review_applications": [],
        },
        "finance": {
            "top_balances_due": [],
            "students_billed_count": 4,
        },
        "registrar": {"enrollments_missing_grade_count": 0},
    }

    resolve.assert_called_once_with("school-a", "year-a")
    managers["aid_apps"].filter.assert_has_calls(
        [
            call(
                school_id="school-a",
                academic_year=academic_year,
                status=views.AidApplication.STATUS_NEEDS_INFO,
            ),
            call(
                school_id="school-a",
                academic_year=academic_year,
                status=views.AidApplication.STATUS_UNDER_REVIEW,
            ),
        ],
        any_order=True,
    )
    managers["awards"].filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        decision_status=views.AidAward.DECISION_ACCEPTED,
        ledger_entry__isnull=True,
    )
    managers["admissions"].filter.assert_has_calls(
        [
            call(
                school_id="school-a",
                academic_year=academic_year,
                status=views.AdmissionsApplication.STATUS_NEEDS_INFO,
            ),
            call(
                school_id="school-a",
                academic_year=academic_year,
                status=views.AdmissionsApplication.STATUS_UNDER_REVIEW,
            ),
        ],
        any_order=True,
    )
    managers["ledger"].filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        family__isnull=False,
    )
    managers["tuition"].filter.assert_called_once_with(
        school_id="school-a", academic_year=academic_year
    )
    managers["enrollment"].filter.assert_called_once_with(
        school_id="school-a",
        academic_year=academic_year,
        status="ENROLLED",
    )
    managers["enrollment_queryset"].filter.assert_called_once_with(
        grade_level__isnull=True
    )


def test_director_priority_sorts_scores_and_caps_combined_worklist(monkeypatch):
    monkeypatch.setattr(views, "crown_director_allowed", lambda request: True)
    academic_year = SimpleNamespace(id="year-a")
    monkeypatch.setattr(
        views,
        "resolve_academic_year",
        lambda school_id, year_id: academic_year,
    )
    family_balances = [
        {
            "family_id": f"family-{index}",
            "family__family_name": f"Family {index}",
            "balance_cents": index * 50_000,
        }
        for index in range(1, 11)
    ]
    _configure_empty_priority_sources(
        monkeypatch,
        family_balances=family_balances,
        missing_grade=1,
    )

    response = views.director_priority(
        _request("?school_id=school-a&year_id=year-a")
    )

    assert response.status_code == 200
    worklist = response.data["worklist_top_10"]
    assert len(worklist) == 10
    assert [item["score"] for item in worklist] == sorted(
        [item["score"] for item in worklist], reverse=True
    )
    assert all(item["type"] == "FINANCE_BALANCE_DUE" for item in worklist)
    assert worklist[0]["family_id"] == "family-10"
    assert worklist[-1]["family_id"] == "family-1"
    assert response.data["registrar"] == {
        "enrollments_missing_grade_count": 1
    }
