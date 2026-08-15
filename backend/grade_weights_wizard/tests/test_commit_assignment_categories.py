from academics.models import AssignmentCategory, Course, Section

from .test_views import BASE_URL, _client, _h, _school


def test_commit_persists_section_assignment_categories():
    school = _school()
    client = _client(school)
    headers = _h(school.id)
    course = Course.objects.create(school_id=school.id, code="E2E-MATH", name="E2E Math")
    section = Section.objects.create(school_id=school.id, course=course, term="E2E-Q1")

    created = client.post(BASE_URL, **headers)
    session_id = created.data["session_id"]

    configured = client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"section_id": str(section.id), "marking_period": "Q1-E2E"},
        format="json",
        **headers,
    )
    assert configured.status_code == 200
    assert configured.data["section_id"] == str(section.id)

    staged = client.post(
        f"{BASE_URL}{session_id}/stage_categories/",
        {"categories_staged": [
            {"name": "Tests E2E", "weight_pct": 60},
            {"name": "Homework E2E", "weight_pct": 40},
        ]},
        format="json",
        **headers,
    )
    assert staged.status_code == 200

    committed = client.post(
        f"{BASE_URL}{session_id}/commit/",
        {"confirm": True},
        format="json",
        **headers,
    )
    assert committed.status_code == 200
    assert committed.data["section_id"] == str(section.id)
    assert committed.data["active_count"] == 2
    assert committed.data["total_weight_pct"] == 100.0
    assert committed.data["errors"] == []

    categories = AssignmentCategory.objects.filter(school_id=school.id, section=section, is_active=True).order_by("sort_order")
    assert list(categories.values_list("name", flat=True)) == ["Tests E2E", "Homework E2E"]
    assert [float(value) for value in categories.values_list("weight_percent", flat=True)] == [60.0, 40.0]

    verified = client.get(f"{BASE_URL}{session_id}/verify/", **headers)
    assert verified.status_code == 200
    assert verified.data["status"] == "verified"
    assert verified.data["active_count"] == 2
    assert verified.data["total_weight_pct"] == 100.0
