import uuid

import pytest
from django.db.models.query import QuerySet
from django.utils import timezone

from academics.models import Course, Enrollment, Section
from core.models import School
from households.models import Household, Student

pytestmark = pytest.mark.django_db(databases=["default", "section_alias"])
ALIAS = "section_alias"


def _alias_graph():
    school = School.objects.using(ALIAS).create(name="Alias Academy")
    course = Course.objects.using(ALIAS).create(
        school_id=school.id,
        code=f"ALIAS-{uuid.uuid4().hex[:6]}",
        name="Alias Course",
    )
    section = Section.objects.using(ALIAS).create(
        school_id=school.id,
        course_id=course.id,
        term="FALL",
    )
    household = Household.objects.using(ALIAS).create(
        school_id=school.id,
        name="Alias Household",
    )
    student = Student.objects.using(ALIAS).create(
        school_id=school.id,
        household_id=household.id,
        first_name="Alias",
        last_name="Student",
    )
    return school, section, student


def test_enrollment_uses_explicit_and_inferred_database_alias():
    school, section, student = _alias_graph()
    enrollment = Enrollment(
        school_id=school.id,
        section_id=section.id,
        student_id=student.id,
    )
    enrollment.save(using=ALIAS)
    assert enrollment._state.db == ALIAS

    enrollment.updated_at = timezone.now()
    enrollment.save(update_fields=["updated_at"])

    persisted = Enrollment.objects.using(ALIAS).get(pk=enrollment.pk)
    assert persisted.school_id == school.id
    assert persisted.section_id == section.id
    assert persisted.student_id == student.id
    assert not Enrollment.objects.using("default").filter(pk=enrollment.pk).exists()


def test_enrollment_preserves_positional_null_alias():
    school, section, student = _alias_graph()
    enrollment = Enrollment.objects.using(ALIAS).create(
        school_id=school.id,
        section_id=section.id,
        student_id=student.id,
    )

    enrollment.updated_at = timezone.now()
    enrollment.save(False, False, None, ["updated_at"])

    assert Enrollment.objects.using(ALIAS).filter(pk=enrollment.pk).exists()
    assert not Enrollment.objects.using("default").filter(pk=enrollment.pk).exists()


def test_enrollment_save_locks_existing_and_authority_rows(monkeypatch):
    locked_models = []
    original_select_for_update = QuerySet.select_for_update

    def recording_select_for_update(self, *args, **kwargs):
        locked_models.append(self.model)
        return original_select_for_update(self, *args, **kwargs)

    monkeypatch.setattr(QuerySet, "select_for_update", recording_select_for_update)

    school = School.objects.create(name="Lock Academy")
    course = Course.objects.create(school_id=school.id, code="LOCK-101", name="Lock")
    section = Section.objects.create(school_id=school.id, course=course, term="FALL")
    household = Household.objects.create(school_id=school.id, name="Lock Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Lock",
        last_name="Student",
    )

    locked_models.clear()
    enrollment = Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )
    assert Section in locked_models
    assert Student in locked_models

    locked_models.clear()
    enrollment.updated_at = timezone.now()
    enrollment.save(update_fields=["updated_at"])
    assert Enrollment in locked_models
    assert Section in locked_models
    assert Student in locked_models
