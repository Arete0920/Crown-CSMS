"""
Test seed_academics_demo command for idempotency and determinism.

Verifies:
- Command creates courses, sections, and enrollments
- Command is idempotent (double-run safe)
- Sections have enrollments (roster_count > 0)
"""
import uuid
from io import StringIO

import pytest
from django.core.management import call_command

from academics.models import Course, Section, Enrollment
from core.models import School


@pytest.mark.django_db
class TestSeedAcademicsDemo:
    """Test suite for seed_academics_demo management command."""

    @pytest.fixture
    def school_id(self):
        """Create a deterministic test school."""
        school_uuid = uuid.uuid4()
        School.objects.create(
            id=school_uuid,
            name="Test School",
            timezone="America/Chicago",
            is_active=True,
        )
        return school_uuid

    def test_creates_academics_data(self, school_id):
        """Running command once creates courses, sections, and enrollments."""
        # Arrange: verify clean state
        assert Course.objects.filter(school_id=school_id).count() == 0
        assert Section.objects.filter(school_id=school_id).count() == 0
        assert Enrollment.objects.filter(school_id=school_id).count() == 0

        # Act: run command
        out = StringIO()
        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)

        # Assert: data created
        courses = Course.objects.filter(school_id=school_id)
        sections = Section.objects.filter(school_id=school_id)
        enrollments = Enrollment.objects.filter(school_id=school_id)

        assert courses.count() >= 2, "Should create at least 2 courses"
        assert sections.count() >= 2, "Should create at least 2 sections"
        assert enrollments.count() > 0, "Should create enrollments"

        # Verify courses have expected codes
        course_codes = set(courses.values_list("code", flat=True))
        assert "MATH-101" in course_codes
        assert "ENG-101" in course_codes

        # Verify sections have enrollments (roster_count > 0)
        for section in sections:
            enrollment_count = section.enrollments.count()
            assert enrollment_count > 0, f"Section {section.id} has 0 enrollments"

    def test_idempotent_double_run(self, school_id):
        """Running command twice does not duplicate data."""
        # Arrange: run command once
        out = StringIO()
        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)

        # Capture counts after first run
        courses_count_1 = Course.objects.filter(school_id=school_id).count()
        sections_count_1 = Section.objects.filter(school_id=school_id).count()
        enrollments_count_1 = Enrollment.objects.filter(school_id=school_id).count()

        assert courses_count_1 >= 2
        assert sections_count_1 >= 2
        assert enrollments_count_1 > 0

        # Act: run command again (idempotency test)
        out2 = StringIO()
        call_command("seed_academics_demo", school_id=str(school_id), stdout=out2)

        # Assert: counts unchanged (no duplicates)
        courses_count_2 = Course.objects.filter(school_id=school_id).count()
        sections_count_2 = Section.objects.filter(school_id=school_id).count()
        enrollments_count_2 = Enrollment.objects.filter(school_id=school_id).count()

        assert courses_count_2 == courses_count_1, "Courses should not duplicate"
        assert sections_count_2 == sections_count_1, "Sections should not duplicate"
        assert enrollments_count_2 == enrollments_count_1, "Enrollments should not duplicate"

    def test_wipe_and_reseed(self, school_id):
        """Using --wipe flag clears data before reseeding."""
        # Arrange: seed once
        out = StringIO()
        call_command("seed_academics_demo", school_id=str(school_id), stdout=out)

        courses_count_1 = Course.objects.filter(school_id=school_id).count()
        assert courses_count_1 >= 2

        # Act: wipe and reseed
        out2 = StringIO()
        call_command("seed_academics_demo", school_id=str(school_id), wipe=True, stdout=out2)

        # Assert: data recreated (counts should match)
        courses_count_2 = Course.objects.filter(school_id=school_id).count()
        sections_count_2 = Section.objects.filter(school_id=school_id).count()
        enrollments_count_2 = Enrollment.objects.filter(school_id=school_id).count()

        assert courses_count_2 >= 2
        assert sections_count_2 >= 2
        assert enrollments_count_2 > 0

    def test_invalid_school_id_fails_gracefully(self):
        """Command handles invalid UUID gracefully."""
        out = StringIO()
        err = StringIO()
        
        # Act: run with invalid UUID
        call_command("seed_academics_demo", school_id="not-a-uuid", stdout=out, stderr=err)

        # Assert: error message written to stderr
        assert "Invalid UUID" in err.getvalue()
