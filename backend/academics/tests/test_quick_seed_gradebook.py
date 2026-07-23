import runpy
from pathlib import Path

import pytest

from academics.models import Enrollment
from core.models import School
from gradebook.models import GradeEntry
from households.models import Student


pytestmark = pytest.mark.django_db


def test_quick_gradebook_seed_uses_current_student_and_grade_fields(monkeypatch):
    school = School.objects.create(name="Quick Seed Christian Academy")
    monkeypatch.setenv("DEMO_SCHOOL_ID", str(school.id))

    script = Path(__file__).resolve().parents[2] / "quick_seed_gradebook.py"
    runpy.run_path(str(script), run_name="__main__")

    students = Student.objects.filter(school_id=school.id)
    enrollments = Enrollment.objects.filter(school_id=school.id)
    grades = GradeEntry.objects.filter(school_id=school.id)

    assert students.count() == 3
    assert enrollments.count() == 3
    assert grades.count() == 9
    assert not grades.filter(points_earned__isnull=True).exists()
    assert not grades.filter(points_possible__isnull=True).exists()

    sample = grades.get(assignment_name="Quiz 1", student__last_name="Test1")
    assert sample.points_earned == 9
    assert sample.points_possible == 10
