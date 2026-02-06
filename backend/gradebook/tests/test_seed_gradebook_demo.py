import uuid
import pytest
from io import StringIO
from django.core.management import call_command
from django.contrib.auth import get_user_model

from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student
from academics.models import Course, Enrollment, Section, Term, TeacherAssignment
from gradebook.models import GradeEntry


pytestmark = pytest.mark.django_db


def _seed_academics_data(school: School):
    """Create minimal academics data with sections and enrollments."""
    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026-2027",
        defaults={
            "start_date": "2026-08-15",
            "end_date": "2027-06-10",
            "is_current": True,
        },
    )
    term, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        defaults={
            "name": "Fall 2026",
            "active": True,
        },
    )
    course, _ = Course.objects.get_or_create(
        school_id=school.id,
        code="MATH-101",
        defaults={"name": "Math"},
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher A",
    )

    # Create students and enrollments
    household = Household.objects.create(school_id=school.id, name="Household A")
    students = []
    for i in range(3):
        student = Student.objects.create(
            school_id=school.id,
            household=household,
            first_name=f"Student{i}",
            last_name=f"LastName{i}",
            grade_level="5",
        )
        students.append(student)
        Enrollment.objects.create(school_id=school.id, section=section, student=student)

    return section, students


def test_seed_gradebook_demo_creates_entries():
    """Test that seed command creates grade entries for sections with enrollments."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    # Run seed command
    out = StringIO()
    call_command("seed_gradebook_demo", "--school-id", str(school.id), stdout=out)

    # Verify entries were created
    entries = GradeEntry.objects.filter(school_id=school.id)
    assert entries.count() > 0, "Should create grade entries"

    # Verify entries for each student
    for student in students:
        student_entries = entries.filter(student_id=student.id)
        assert student_entries.count() == 5, f"Should create 5 default assignments for {student.first_name}"

    # Verify assignment names
    assignment_names = set(entries.values_list("assignment_name", flat=True).distinct())
    assert "Quiz 1" in assignment_names
    assert "Homework 1" in assignment_names
    assert "Project 1" in assignment_names


def test_seed_gradebook_demo_idempotent():
    """Test that running seed command twice doesn't create duplicates."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    # Run seed command first time
    out = StringIO()
    call_command("seed_gradebook_demo", "--school-id", str(school.id), stdout=out)
    first_count = GradeEntry.objects.filter(school_id=school.id).count()

    # Run seed command second time
    out = StringIO()
    call_command("seed_gradebook_demo", "--school-id", str(school.id), stdout=out)
    second_count = GradeEntry.objects.filter(school_id=school.id).count()

    # Verify count didn't change
    assert first_count == second_count, "Second run should not create duplicates"
    assert "created_grade_entries=0" in out.getvalue(), "Second run should report 0 new entries"


def test_seed_gradebook_demo_wipe_flag():
    """Test that --wipe flag clears existing entries before seeding."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    # Create initial entries
    call_command("seed_gradebook_demo", "--school-id", str(school.id))
    initial_count = GradeEntry.objects.filter(school_id=school.id).count()
    assert initial_count > 0

    # Run with --wipe, but with --per-section 3 instead of 5
    out = StringIO()
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--wipe", "--per-section", "3", stdout=out)

    # Verify entries were wiped and recreated with new count
    new_count = GradeEntry.objects.filter(school_id=school.id).count()
    assert "WIPED" in out.getvalue(), "Should report wipe action"
    # 3 students × 3 assignments = 9 entries
    assert new_count == 9, f"Should have 9 entries after wipe with --per-section 3, got {new_count}"


def test_seed_gradebook_demo_only_sections_with_enrollments():
    """Test that seed command only creates entries for sections with enrollments."""
    school = School.objects.create(name="Test School")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        active=True,
    )
    course = Course.objects.create(school_id=school.id, code="MATH-101", name="Math")

    # Create section WITH enrollments
    section_with_roster, students = _seed_academics_data(school)

    # Create section WITHOUT enrollments (just section, no students)
    empty_section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher Empty",
    )

    # Run seed command
    call_command("seed_gradebook_demo", "--school-id", str(school.id))

    # Verify entries only for section with roster
    entries = GradeEntry.objects.filter(school_id=school.id)
    assert entries.filter(section_id=section_with_roster.id).exists(), "Should create entries for section with roster"
    assert not entries.filter(section_id=empty_section.id).exists(), "Should NOT create entries for empty section"


def test_seed_gradebook_demo_scopes_to_school():
    """Test that wipe only affects the specified school, not others."""
    school1 = School.objects.create(name="School 1")
    school2 = School.objects.create(name="School 2")

    # Create data for both schools
    section1, students1 = _seed_academics_data(school1)
    section2, students2 = _seed_academics_data(school2)

    # Seed both schools
    call_command("seed_gradebook_demo", "--school-id", str(school1.id))
    call_command("seed_gradebook_demo", "--school-id", str(school2.id))

    school1_count = GradeEntry.objects.filter(school_id=school1.id).count()
    school2_count = GradeEntry.objects.filter(school_id=school2.id).count()
    assert school1_count > 0
    assert school2_count > 0

    # Wipe only school1
    call_command("seed_gradebook_demo", "--school-id", str(school1.id), "--wipe")

    # Verify school2 entries are still there
    assert GradeEntry.objects.filter(school_id=school2.id).count() == school2_count, "School 2 entries should be untouched"
    # School1 should have new entries after reseed
    assert GradeEntry.objects.filter(school_id=school1.id).count() == school1_count, "School 1 should have reseeded entries"


def test_seed_gradebook_demo_deterministic_scores():
    """Test that --seed flag produces deterministic results."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    # First run with seed=1234
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--wipe", "--seed", "1234")
    first_scores = list(
        GradeEntry.objects.filter(school_id=school.id)
        .order_by("student_id", "assignment_name")
        .values_list("points_earned", flat=True)
    )

    # Second run with same seed
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--wipe", "--seed", "1234")
    second_scores = list(
        GradeEntry.objects.filter(school_id=school.id)
        .order_by("student_id", "assignment_name")
        .values_list("points_earned", flat=True)
    )

    # Verify scores are identical
    assert first_scores == second_scores, "Same seed should produce identical scores"


def test_seed_gradebook_demo_per_section_option():
    """Test that --per-section controls number of assignments."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    # Seed with 3 assignments per section
    call_command("seed_gradebook_demo", "--school-id", str(school.id), "--per-section", "3")

    # Verify each student has exactly 3 grade entries
    for student in students:
        count = GradeEntry.objects.filter(school_id=school.id, student_id=student.id).count()
        assert count == 3, f"Should create 3 assignments for {student.first_name}, got {count}"


def test_seed_gradebook_demo_score_range():
    """Test that scores are within realistic 60%-100% range."""
    school = School.objects.create(name="Test School")
    section, students = _seed_academics_data(school)

    call_command("seed_gradebook_demo", "--school-id", str(school.id))

    # Verify all scores are within expected range
    entries = GradeEntry.objects.filter(school_id=school.id)
    for entry in entries:
        percentage = (entry.points_earned / entry.points_possible) * 100
        assert 60 <= percentage <= 100, f"Score {entry.points_earned}/{entry.points_possible} = {percentage}% outside 60-100% range"
