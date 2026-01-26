from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from aid.models import AidApplication
from core.models import AcademicYear, Family, School


@pytest.mark.django_db
def test_director_timeline_endpoint_authorized():
    client = Client()

    school = School.objects.create(name="Timeline Test School")
    academic_year = AcademicYear.objects.create(
        school=school,
        name="2024-2025",
        start_date=date(2024, 8, 15),
        end_date=date(2025, 6, 10),
        is_current=True,
    )

    family = Family.objects.create(school=school, family_name="Timeline Test Family")
    AidApplication.objects.create(
        school=school,
        family=family,
        academic_year=academic_year,
        status=AidApplication.STATUS_NEEDS_INFO,
    )

    User = get_user_model()
    admin = User.objects.create_superuser(
        username="timeline_admin",
        email="timeline_admin@test.com",
        password="password123",
    )

    client.force_login(admin)

    resp = client.get(
        f"/api/director/timeline/?school_id={school.id}&year_id={academic_year.id}&limit=20"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "meta" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)
