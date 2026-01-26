from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from aid.models import AidAward
from core.models import AcademicYear, Family, School, Student
from finance.models import ChartAccount


@pytest.mark.django_db
def test_director_actions_requires_auth_and_staff():
    client = Client()

    school = School.objects.create(name="Auth Test School")
    year = AcademicYear.objects.create(
        school=school,
        name="2024-2025",
        start_date=date(2024, 8, 15),
        end_date=date(2025, 6, 10),
        is_current=True,
    )

    # Required for mark_accepted_and_post()
    ChartAccount.objects.get_or_create(
        school=school,
        code="AID",
        defaults={"name": "Financial Aid", "account_type": "INCOME", "is_active": True},
    )

    family = Family.objects.create(school=school, family_name="Auth Test Family")
    student = Student.objects.create(
        school=school,
        family=family,
        student_number="S10000",
        first_name="Test",
        last_name="Student",
        dob=date(2010, 1, 1),
    )

    award = AidAward.objects.create(
        school=school,
        student=student,
        academic_year=year,
        awarded_cents=50000,
        decision_status=AidAward.DECISION_ACCEPTED,
    )

    payload = {
        "action": "POST_ACCEPTED_AWARDS",
        "school_id": str(school.id),
        "year_id": str(year.id),
        "ids": [str(award.id)],
    }

    # 1) Unauthenticated -> 401
    resp = client.post("/api/director/actions/", data=payload, content_type="application/json")
    assert resp.status_code == 401

    award.refresh_from_db()
    assert award.ledger_entry_id is None

    # 2) Authenticated but non-staff -> 403
    User = get_user_model()
    nonstaff = User.objects.create_user(
        username="director_actions_nonstaff",
        email="director_actions_nonstaff@test.com",
        password="password123",
    )
    client.force_login(nonstaff)
    resp = client.post("/api/director/actions/", data=payload, content_type="application/json")
    assert resp.status_code == 403

    award.refresh_from_db()
    assert award.ledger_entry_id is None

    # 3) Staff -> 200
    staff = User.objects.create_user(
        username="director_actions_staff",
        email="director_actions_staff@test.com",
        password="password123",
        is_staff=True,
    )
    client.force_login(staff)
    resp = client.post("/api/director/actions/", data=payload, content_type="application/json")
    assert resp.status_code == 200

    award.refresh_from_db()
    assert award.ledger_entry_id is not None
