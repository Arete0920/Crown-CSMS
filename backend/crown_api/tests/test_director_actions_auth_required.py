from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

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


@pytest.mark.django_db
@override_settings(CROWN_ENV='dev', DEV_SEED_KEY='test-dev-seed-key')
def test_force_seed_user_security():
    """Regression test for force_seed_user endpoint security."""
    client = Client()

    url = "/api/director/force_seed_user/"

    # 1) Outside dev -> 404
    with override_settings(CROWN_ENV='prod'):
        resp = client.post(url)
        assert resp.status_code == 404

    # 2) In dev, anonymous POST -> 403
    resp = client.post(url)
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Forbidden."}

    # 3) Wrong key -> 403
    resp = client.post(url, headers={"X-Dev-Seed-Key": "wrong-key"})
    assert resp.status_code == 403

    # 4) Correct key -> 200, no credentials in response
    resp = client.post(url, headers={"X-Dev-Seed-Key": "test-dev-seed-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "password" not in str(data).lower()
    assert "Crown2026!" not in str(data)
    assert "admin" not in str(data).lower() or "admin_created" in data  # allow admin_created flag but not password

    # 5) JWT staff -> 200
    User = get_user_model()
    staff = User.objects.create_user(
        username="seed_staff",
        password="password123",
        is_staff=True,
    )
    client.force_login(staff)
    resp = client.post(url)
    assert resp.status_code == 200
    client.logout()


@pytest.mark.django_db
@override_settings(CROWN_ENV="prod", DEV_SEED_KEY="test-dev-seed-key")
def test_force_seed_user_prod_always_404():
    """Absolute deny: force_seed_user returns 404 in prod even with valid key."""
    client = Client()
    resp = client.post("/api/director/force_seed_user/", headers={"X-Dev-Seed-Key": "test-dev-seed-key"})
    assert resp.status_code == 404
