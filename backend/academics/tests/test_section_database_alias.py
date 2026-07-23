import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from academics.models import Course, Section, Term
from core.models import AcademicYear, School


pytestmark = pytest.mark.django_db(databases=["default", "section_alias"])
User = get_user_model()
ALIAS = "section_alias"


def test_section_authority_validation_uses_explicit_and_inferred_database_alias():
    school = School.objects.using(ALIAS).create(name="Alias Christian Academy")
    year = AcademicYear.objects.using(ALIAS).create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
    )
    term = Term.objects.using(ALIAS).create(
        school_id=school.id,
        academic_year=year,
        code="FALL",
        name="Fall",
    )
    course = Course.objects.using(ALIAS).create(
        school_id=school.id,
        code="ALIAS-101",
        name="Alias Course",
    )
    teacher = User._default_manager.db_manager(ALIAS).create_user(
        username=f"alias-teacher-{uuid.uuid4()}",
        email="teacher@alias.test",
        password="pass12345!",
        school=school,
    )

    section = Section(
        school_id=school.id,
        course_id=course.id,
        term_ref_id=term.id,
        term="FALL",
        teacher_id=teacher.id,
    )
    section.save(using=ALIAS)
    assert section._state.db == ALIAS

    section.teacher_name = "Alias Teacher"
    section.save(update_fields=["teacher_name"])

    persisted = Section.objects.using(ALIAS).get(pk=section.pk)
    assert persisted.school_id == school.id
    assert persisted.course_id == course.id
    assert persisted.term_ref_id == term.id
    assert persisted.teacher_id == teacher.id
    assert persisted.teacher_name == "Alias Teacher"
    assert not Section.objects.using("default").filter(pk=section.pk).exists()


def test_existing_section_can_be_copied_to_alias_when_target_row_is_missing():
    school_id = uuid.uuid4()
    course_id = uuid.uuid4()

    default_school = School.objects.using("default").create(
        id=school_id,
        name="Default Christian Academy",
    )
    alias_school = School.objects.using(ALIAS).create(
        id=school_id,
        name="Alias Christian Academy",
    )
    default_course = Course.objects.using("default").create(
        id=course_id,
        school_id=default_school.id,
        code="COPY-101",
        name="Copy Course",
    )
    Course.objects.using(ALIAS).create(
        id=course_id,
        school_id=alias_school.id,
        code="COPY-101",
        name="Copy Course",
    )

    section = Section.objects.using("default").create(
        school_id=default_school.id,
        course=default_course,
        term="FALL",
    )

    section.save(using=ALIAS)

    assert Section.objects.using("default").filter(pk=section.pk).exists()
    copied = Section.objects.using(ALIAS).get(pk=section.pk)
    assert copied.school_id == school_id
    assert copied.course_id == course_id
    assert copied.term == "FALL"


def test_existing_section_preserves_positional_save_alias():
    school = School.objects.using(ALIAS).create(name="Positional Alias Academy")
    course = Course.objects.using(ALIAS).create(
        school_id=school.id,
        code="POSITIONAL-101",
        name="Positional Course",
    )
    section = Section.objects.using(ALIAS).create(
        school_id=school.id,
        course_id=course.id,
        term="FALL",
    )

    section.teacher_name = "Positional Teacher"
    section.save(False, False, ALIAS, ["teacher_name"])

    persisted = Section.objects.using(ALIAS).get(pk=section.pk)
    assert persisted.teacher_name == "Positional Teacher"
    assert not Section.objects.using("default").filter(pk=section.pk).exists()


def test_existing_section_normalizes_positional_null_alias_to_instance_database():
    school = School.objects.using(ALIAS).create(name="Inferred Positional Alias Academy")
    course = Course.objects.using(ALIAS).create(
        school_id=school.id,
        code="POSITIONAL-NULL-101",
        name="Positional Null Course",
    )
    section = Section.objects.using(ALIAS).create(
        school_id=school.id,
        course_id=course.id,
        term="FALL",
    )

    section.teacher_name = "Inferred Positional Teacher"
    section.save(False, False, None, ["teacher_name"])

    persisted = Section.objects.using(ALIAS).get(pk=section.pk)
    assert persisted.teacher_name == "Inferred Positional Teacher"
    assert not Section.objects.using("default").filter(pk=section.pk).exists()
