from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from aid.models import AidApplication
from core.models import AcademicYear, Family, School


@pytest.mark.django_db
def test_generate_needs_info_emails_action_success():
    client = Client()

    school = School.objects.create(name="Test School")
    academic_year = AcademicYear.objects.create(
        school=school,
        name="2024-2025",
        start_date=date(2024, 8, 15),
        end_date=date(2025, 6, 10),
        is_current=True,
    )

    family = Family.objects.create(school=school, family_name="Test Family for Needs Info")
    app = AidApplication.objects.create(
        school=school,
        family=family,
        academic_year=academic_year,
        status=AidApplication.STATUS_NEEDS_INFO,
    )

    User = get_user_model()
    admin = User.objects.create_superuser(
        username="director_admin",
        email="director_admin@test.com",
        password="password123",
    )

    client.force_login(admin)

    resp = client.post(
        "/api/director/actions/",
        data={
            "action": "AID_GENERATE_NEEDS_INFO_EMAILS",
            "school_id": str(school.id),
            "year_id": str(academic_year.id),
            "ids": [str(app.id)],
        },
        content_type="application/json",
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "AID_GENERATE_NEEDS_INFO_EMAILS"
    assert data["draft_count"] == 1
    assert data["failure_count"] == 0
    assert isinstance(data.get("drafts"), list)
    assert data["drafts"][0]["application_id"] == str(app.id)
