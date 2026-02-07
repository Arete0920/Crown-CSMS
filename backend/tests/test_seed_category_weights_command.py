"""
Tests for seed_category_weights management command.

Validates:
- Creates 4 categories per section with correct weights
- Categories sum to 100%
- Idempotent (re-running doesn't duplicate)
- Only seeds sections with enrollments
"""
from __future__ import annotations

from decimal import Decimal
from io import StringIO
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase

from core.models import School
from academics.models import Section, AssignmentCategory, Enrollment, Course
from households.models import Student, Household


class SeedCategoryWeightsCommandTest(TestCase):
    """Test seed_category_weights management command."""

    def setUp(self):
        """Create test school and course for sections."""
        self.school = School.objects.create(
            id=uuid4(),
            name="Test School",
            timezone="America/New_York",
            is_active=True
        )
        
        self.course = Course.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            code="MATH101",
            name="Mathematics 101"
        )
        
        self.household = Household.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            name="Test Household"
        )
        
        self.student = Student.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            household=self.household,
            first_name="Test",
            last_name="Student"
        )

    def test_seed_creates_4_categories_with_correct_weights(self):
        """Test that seed creates exactly 4 categories with weights summing to 100%."""
        # Create section with enrollment (required for seeding)
        section = Section.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL"
        )
        Enrollment.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            section=section,
            student=self.student
        )

        # Run seed command
        out = StringIO()
        call_command("seed_category_weights", "--school-id", str(self.school.id), stdout=out)

        # Verify 4 categories created
        categories = AssignmentCategory.objects.filter(
            school_id=self.school.id,
            section=section
        ).order_by("sort_order")

        self.assertEqual(categories.count(), 4)

        # Verify category names and weights
        expected = [
            ("Homework", Decimal("20.00"), 1),
            ("Quizzes", Decimal("30.00"), 2),
            ("Projects", Decimal("25.00"), 3),
            ("Exams", Decimal("25.00"), 4),
        ]

        for idx, (name, weight, sort_order) in enumerate(expected):
            cat = categories[idx]
            self.assertEqual(cat.name, name)
            self.assertEqual(cat.weight_percent, weight)
            self.assertEqual(cat.sort_order, sort_order)
            self.assertTrue(cat.is_active)

        # Verify weights sum to 100
        total_weight = sum(cat.weight_percent for cat in categories)
        self.assertEqual(total_weight, Decimal("100.00"))

        # Verify output message
        output = out.getvalue()
        self.assertIn("sections_scanned=1", output)
        self.assertIn("categories_created=4", output)
        self.assertIn("categories_skipped=0", output)

    def test_seed_is_idempotent(self):
        """Test that re-running seed doesn't duplicate categories."""
        # Create section with enrollment
        section = Section.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL"
        )
        Enrollment.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            section=section,
            student=self.student
        )

        # Run seed command twice
        call_command("seed_category_weights", "--school-id", str(self.school.id))
        
        first_count = AssignmentCategory.objects.filter(
            school_id=self.school.id,
            section=section
        ).count()

        out = StringIO()
        call_command("seed_category_weights", "--school-id", str(self.school.id), stdout=out)

        second_count = AssignmentCategory.objects.filter(
            school_id=self.school.id,
            section=section
        ).count()

        # Count should stay the same
        self.assertEqual(first_count, 4)
        self.assertEqual(second_count, 4)

        # Second run should report all skipped
        output = out.getvalue()
        self.assertIn("categories_created=0", output)
        self.assertIn("categories_skipped=4", output)

    def test_seed_skips_sections_without_enrollments(self):
        """Test that seed only creates categories for sections with enrollments."""
        # Create section WITHOUT enrollment
        Section.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL"
        )

        # Run seed command
        out = StringIO()
        call_command("seed_category_weights", "--school-id", str(self.school.id), stdout=out)

        # No categories should be created
        category_count = AssignmentCategory.objects.filter(school_id=self.school.id).count()
        self.assertEqual(category_count, 0)

        # Output should show 0 sections scanned
        output = out.getvalue()
        self.assertIn("sections_scanned=0", output)

    def test_seed_dry_run_does_not_create(self):
        """Test that --dry-run shows what would be created without creating."""
        # Create section with enrollment
        section = Section.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL"
        )
        Enrollment.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            section=section,
            student=self.student
        )

        # Run with --dry-run
        out = StringIO()
        call_command("seed_category_weights", "--school-id", str(self.school.id), "--dry-run", stdout=out)

        # No categories should actually be created
        category_count = AssignmentCategory.objects.filter(school_id=self.school.id).count()
        self.assertEqual(category_count, 0)

        # Output should show dry-run mode
        output = out.getvalue()
        self.assertIn("[DRY-RUN]", output)
        self.assertIn("CREATE", output)
        self.assertIn("Homework", output)

    def test_seed_wipe_deletes_existing_categories(self):
        """Test that --wipe deletes existing categories before seeding."""
        # Create section with enrollment
        section = Section.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL"
        )
        Enrollment.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            section=section,
            student=self.student
        )

        # Create an existing category manually
        AssignmentCategory.objects.create(
            id=uuid4(),
            school_id=self.school.id,
            section=section,
            name="Old Category",
            weight_percent=Decimal("50.00"),
            sort_order=99
        )

        # Verify old category exists
        self.assertEqual(AssignmentCategory.objects.filter(school_id=self.school.id).count(), 1)

        # Run with --wipe
        out = StringIO()
        call_command("seed_category_weights", "--school-id", str(self.school.id), "--wipe", stdout=out)

        # Old category should be deleted, new ones created
        categories = AssignmentCategory.objects.filter(school_id=self.school.id)
        self.assertEqual(categories.count(), 4)
        self.assertFalse(categories.filter(name="Old Category").exists())

        # Output should show wipe happened
        output = out.getvalue()
        self.assertIn("WIPED", output)
        self.assertIn("deleted=1", output)
