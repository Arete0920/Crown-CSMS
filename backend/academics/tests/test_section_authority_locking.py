import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from academics.models import Course, Section, Term
from core.models import AcademicYear, School


pytestmark = pytest.mark.django_db
User = get_user_model()


def test_section_save_locks_all_related_authority_rows(monkeypatch):
    locked_models = []
    original_select_for_update = QuerySet.select_for_update

    def recording_select_for_update(self, *args, **kwargs):
        locked_models.append(self.model)
        return original_select_for_update(self, *args, **kwargs)

    monkeypatch.setattr(QuerySet, "select_for_update", recording_select_for_update)

    school = School.objects.create(name="Authority Lock Christian Academy")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="FALL",
        name="Fall",
    )
    course = Course.objects.create(
        school_id=school.id,
        code="LOCK-101",
        name="Authority Lock Course",
    )
    teacher = User.objects.create_user(
        username=f"authority-lock-{uuid.uuid4()}",
        email="authority-lock@example.test",
        password="pass12345!",
        school=school,
    )

    locked_models.clear()
    section = Section(
        school_id=school.id,
        course_id=course.id,
        term_ref_id=term.id,
        term="FALL",
        teacher_id=teacher.id,
    )
    section.save()

    assert Course in locked_models
    assert Term in locked_models
    assert User in locked_models

    locked_models.clear()
    section.teacher_name = "Authority Lock Teacher"
    section.save(update_fields=["teacher_name"])

    assert Section in locked_models
    assert Course in locked_models
    assert Term in locked_models
    assert User in locked_models
    section.refresh_from_db()
    assert section.teacher_name == "Authority Lock Teacher"
