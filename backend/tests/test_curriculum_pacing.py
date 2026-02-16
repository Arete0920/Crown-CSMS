"""
Test for curriculum pacing endpoint.
Verifies pacing-summary returns correct aggregation and school scoping.
"""

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import School, UserAccount
from curriculum.views import CurriculumCourseViewSet


@pytest.mark.django_db
def test_curriculum_pacing_summary_endpoint():
    """
    Verify pacing-summary endpoint:
    - Returns status 200
    - Includes pacing calculations (total, due, pct_due)
    - Respects school scoping via X-School-Id header
    - CRITICAL: wrong school returns empty (proves scoping works)
    """
    # Create test data
    school_a = School.objects.create(name="Test School A")
    school_b = School.objects.create(name="Test School B")

    # Get or create a user for authentication
    user = UserAccount.objects.first() or UserAccount.objects.create_user(
        username="test_curriculum_pacing", password="test"
    )

    from curriculum.models import CurriculumCourse

    # Create a course ONLY under school_a
    course_a = CurriculumCourse.objects.create(
        school=school_a,
        code="TEST-A",
        name="Test Course A",
        subject="Test",
        grade_level="9",
        worldview_theme="Test theme",
        anchor_scripture_ref="Test ref",
        anchor_scripture_text="Test text"
    )

    factory = APIRequestFactory()
    
    # Test 1: request with school_a (has courses)
    req = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )
    force_authenticate(req, user=user)
    view = CurriculumCourseViewSet.as_view({"get": "pacing_summary"})
    resp = view(req)

    assert resp.status_code == 200
    data = resp.data
    assert "count" in data
    assert "results" in data
    # School A should see at least 1 course
    assert data["count"] >= 1, "School A should see its own course"

    # Verify pacing structure
    if data["results"]:
        course_result = data["results"][0]
        assert "course_id" in course_result
        assert "code" in course_result
        assert "name" in course_result
        assert "pacing" in course_result

        pacing = course_result["pacing"]
        assert "as_of" in pacing
        assert "total_lessons" in pacing
        assert "due_lessons" in pacing
        assert "pct_due" in pacing
        assert isinstance(pacing["pct_due"], int)
        assert 0 <= pacing["pct_due"] <= 100

    # Test 2: CRITICAL SCOPING TEST - request with school_b (no courses)
    req_wrong = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    force_authenticate(req_wrong, user=user)
    resp_wrong = view(req_wrong)

    assert resp_wrong.status_code == 200, "Should return 200 even with empty results"
    assert resp_wrong.data["count"] == 0, "School B sees NO courses (school_a's course is hidden)"


@pytest.mark.django_db
def test_curriculum_pacing_detail_endpoint():
    """
    Verify pacing detail endpoint for a single course.
    CRITICAL: wrong school gets 404 (proves scoping works)
    """
    # Create test data with TWO schools
    school_a = School.objects.create(name="Test School A")
    school_b = School.objects.create(name="Test School B")

    from curriculum.models import CurriculumCourse

    # Create course under school_a ONLY
    course_a = CurriculumCourse.objects.create(
        school=school_a,
        code="TEST-A",
        name="Test Course A",
        subject="Test",
        grade_level="9",
        worldview_theme="Test theme",
        anchor_scripture_ref="Test ref",
        anchor_scripture_text="Test text"
    )

    user = UserAccount.objects.first() or UserAccount.objects.create_user(
        username="test_curriculum_detail", password="test"
    )

    factory = APIRequestFactory()

    # Test 1: correct school can access the course
    req = factory.get(
        f"/api/curriculum/courses/{course_a.id}/pacing/",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )
    force_authenticate(req, user=user)

    view = CurriculumCourseViewSet.as_view({"get": "pacing"})
    resp = view(req, pk=str(course_a.id))

    assert resp.status_code == 200
    data = resp.data
    assert data["course_id"] == str(course_a.id)
    assert "pacing" in data
    assert isinstance(data["pacing"]["pct_due"], int)

    # Test 2: CRITICAL SCOPING TEST - wrong school gets 404
    req_wrong = factory.get(
        f"/api/curriculum/courses/{course_a.id}/pacing/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    force_authenticate(req_wrong, user=user)
    resp_wrong = view(req_wrong, pk=str(course_a.id))

    assert resp_wrong.status_code == 404, "School B cannot access School A's course"
