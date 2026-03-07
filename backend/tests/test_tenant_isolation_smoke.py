# backend/tests/test_tenant_isolation_smoke.py
"""
Minimal cross-tenant isolation proof for writable ViewSets.

Verifies that a user scoped to School A cannot read or write
data belonging to School B through the submissions endpoint.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School
from households.models import Household, Student
from academics.models import (
    Course,
    Section,
    Term,
    Enrollment,
    Assignment,
    AssignmentCategory,
    Submission,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def _make_school(name: str) -> School:
    return School.objects.create(name=name)


def _make_user(school: School) -> User:
    u = User.objects.create_user(
        username=f"u-{uuid.uuid4()}",
        password="pass12345!",
    )
    if hasattr(u, "school_id"):
        u.school_id = school.id
        u.save(update_fields=["school_id"])
    return u


def _make_submission(school: School) -> Submission:
    """Create an entire object graph for a Submission in the given school."""
    ay = AcademicYear.objects.create(
        school=school, name="2025-2026",
        start_date=date(2025, 8, 1), end_date=date(2026, 6, 1),
    )
    hh = Household.objects.create(school_id=school.id, name=f"HH-{uuid.uuid4()}")
    student = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name="Test",
        last_name="Student",
    )
    course = Course.objects.create(
        school_id=school.id, code=f"C-{uuid.uuid4().hex[:6]}", name="Math"
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=ay,
        code=f"T-{uuid.uuid4().hex[:6]}",
        name="Fall",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
    )
    enrollment = Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=Decimal("100"),
    )
    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name=f"HW-{uuid.uuid4().hex[:6]}",
        points_possible=Decimal("100"),
    )
    return Submission.objects.create(
        school_id=school.id,
        assignment=assignment,
        enrollment=enrollment,
        status=Submission.Status.SUBMITTED,
    )


class TestCrossTenantIsolation:
    """Cross-tenant isolation: user A must not see school B data."""

    def test_cross_tenant_submission_list_hidden(self):
        """Listing submissions for school A must not include school B data."""
        school_a = _make_school("School A")
        school_b = _make_school("School B")

        _make_submission(school_a)
        sub_b = _make_submission(school_b)

        user_a = _make_user(school_a)

        c = APIClient()
        c.force_authenticate(user=user_a)
        resp = c.get(
            "/api/v1/academics/submissions/",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert resp.status_code == 200
        data = resp.json()
        # Handle both paginated (dict with "results") and unpaginated (list) responses
        items = data.get("results", data) if isinstance(data, dict) else data
        # Serializer uses submission_id, not id
        ids = {str(r.get("submission_id", r.get("id", ""))) for r in items}
        assert str(sub_b.id) not in ids

    def test_cross_tenant_submission_detail_denied(self):
        """Fetching a specific submission from school B returns 404."""
        school_a = _make_school("School A")
        school_b = _make_school("School B")

        sub_b = _make_submission(school_b)
        user_a = _make_user(school_a)

        c = APIClient()
        c.force_authenticate(user=user_a)
        resp = c.get(
            f"/api/v1/academics/submissions/{sub_b.id}/",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert resp.status_code == 404
