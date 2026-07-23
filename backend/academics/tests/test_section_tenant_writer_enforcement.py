import json
import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from rest_framework.test import APIClient

from academics.api import sections as legacy_sections
from academics.models import Course, Section, Term
from core.models import AcademicYear, School


pytestmark = pytest.mark.django_db
User = get_user_model()


def _school(name):
    return School.objects.create(name=name)


def _year(school, name="2026-2027"):
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
    )


def _term(school, year, code="FALL"):
    return Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code=code,
        name=code.title(),
    )


def _course(school, code="MATH-101"):
    return Course.objects.create(school_id=school.id, code=code, name=code)


def _teacher(school, email):
    return User.objects.create_user(
        username=f"teacher-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
        school=school,
    )


def _section(school, course, term_ref=None, teacher=None):
    return Section(
        school_id=school.id,
        course=course,
        term_ref=term_ref,
        term=term_ref.code if term_ref else "FALL",
        teacher=teacher,
    )


def test_same_school_section_create_succeeds():
    school = _school("Heritage Christian Academy")
    year = _year(school)
    term = _term(school, year)
    course = _course(school)
    teacher = _teacher(school, "teacher@heritage.test")

    section = _section(school, course, term, teacher)
    section.save()

    assert Section.objects.filter(pk=section.pk).exists()


def test_section_accepts_string_school_uuid():
    school = _school("Harvest Christian School")
    course = _course(school)

    section = Section(
        school_id=str(school.id),
        course_id=str(course.id),
        term="FALL",
    )
    section.save()
    section.refresh_from_db()

    assert section.school_id == school.id
    assert section.course_id == course.id


def test_cross_school_course_is_rejected_without_persistence():
    school = _school("Faith Christian Academy")
    other_school = _school("Calvary Christian School")
    course = _course(other_school)

    section = _section(school, course)
    with pytest.raises(ValidationError, match="same school"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_cross_school_term_is_rejected_without_persistence():
    school = _school("St. Anne Christian Academy")
    other_school = _school("Grace Covenant School")
    year = _year(other_school)
    term = _term(other_school, year)
    course = _course(school)

    section = _section(school, course, term)
    with pytest.raises(ValidationError, match="same school"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_cross_school_teacher_is_rejected_without_persistence():
    school = _school("Providence Christian School")
    other_school = _school("Trinity Classical School")
    course = _course(school)
    teacher = _teacher(other_school, "teacher@trinity.test")

    section = _section(school, course, teacher=teacher)
    with pytest.raises(ValidationError, match="same school"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_teacher_without_school_is_rejected():
    school = _school("Redeemer Christian School")
    course = _course(school)
    teacher = User.objects.create_user(
        username=f"teacher-{uuid.uuid4()}",
        email="teacher@noschool.test",
        password="pass12345!",
        school=None,
    )

    section = _section(school, course, teacher=teacher)
    with pytest.raises(ValidationError, match="must belong to a school"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_missing_course_is_rejected():
    school = _school("Cornerstone Christian School")
    section = Section(
        school_id=school.id,
        course_id=uuid.uuid4(),
        term="FALL",
    )

    with pytest.raises(ValidationError, match="does not exist"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_missing_optional_term_is_rejected():
    school = _school("New Hope Christian School")
    course = _course(school)
    section = Section(
        school_id=school.id,
        course=course,
        term_ref_id=uuid.uuid4(),
        term="FALL",
    )

    with pytest.raises(ValidationError, match="does not exist"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_missing_optional_teacher_is_rejected():
    school = _school("Lighthouse Christian School")
    course = _course(school)
    section = Section(
        school_id=school.id,
        course=course,
        teacher_id=uuid.uuid4(),
        term="FALL",
    )

    with pytest.raises(ValidationError, match="does not exist"):
        section.save()

    assert not Section.objects.filter(pk=section.pk).exists()


def test_partial_course_repoint_is_rejected_and_persistence_unchanged():
    school = _school("Legacy Christian School")
    other_school = _school("Emmanuel Christian School")
    course = _course(school)
    other_course = _course(other_school, code="SCI-101")
    section = _section(school, course)
    section.save()

    section.course = other_course
    with pytest.raises(ValidationError, match="same school"):
        section.save(update_fields=["course"])

    section.refresh_from_db()
    assert section.school_id == school.id
    assert section.course_id == course.id


def test_partial_term_repoint_is_rejected_and_persistence_unchanged():
    school = _school("Covenant Preparatory")
    other_school = _school("Shepherd's Gate Academy")
    year = _year(school)
    other_year = _year(other_school, name="2027-2028")
    term = _term(school, year)
    other_term = _term(other_school, other_year, code="SPRING")
    course = _course(school)
    section = _section(school, course, term_ref=term)
    section.save()

    section.term_ref = other_term
    with pytest.raises(ValidationError, match="same school"):
        section.save(update_fields=["term_ref"])

    section.refresh_from_db()
    assert section.school_id == school.id
    assert section.term_ref_id == term.id


def test_partial_teacher_repoint_is_rejected_and_persistence_unchanged():
    school = _school("Crossroads Christian School")
    other_school = _school("Bethel Christian Academy")
    course = _course(school)
    teacher = _teacher(school, "teacher@crossroads.test")
    other_teacher = _teacher(other_school, "teacher@bethel.test")
    section = _section(school, course, teacher=teacher)
    section.save()

    section.teacher = other_teacher
    with pytest.raises(ValidationError, match="same school"):
        section.save(update_fields=["teacher"])

    section.refresh_from_db()
    assert section.school_id == school.id
    assert section.teacher_id == teacher.id


def test_paired_school_and_course_reparent_succeeds():
    school = _school("King's Way Christian School")
    other_school = _school("Bethel Christian School")
    course = _course(school)
    other_course = _course(other_school, code="ENG-201")
    section = _section(school, course)
    section.save()

    section.school_id = other_school.id
    section.course = other_course
    section.save(update_fields=["school_id", "course"])
    section.refresh_from_db()

    assert section.school_id == other_school.id
    assert section.course_id == other_course.id


def test_all_authorities_can_be_reparented_together():
    school = _school("Veritas Christian School")
    other_school = _school("New Covenant Christian School")
    year = _year(school)
    other_year = _year(other_school, name="2027-2028")
    term = _term(school, year)
    other_term = _term(other_school, other_year)
    course = _course(school)
    other_course = _course(other_school, code="HIST-201")
    teacher = _teacher(school, "teacher@veritas.test")
    other_teacher = _teacher(other_school, "teacher@newcovenant.test")
    section = _section(school, course, term_ref=term, teacher=teacher)
    section.save()

    section.school_id = other_school.id
    section.course = other_course
    section.term_ref = other_term
    section.teacher = other_teacher
    section.save(update_fields=["school_id", "course", "term_ref", "teacher"])
    section.refresh_from_db()

    assert section.school_id == other_school.id
    assert section.course_id == other_course.id
    assert section.term_ref_id == other_term.id
    assert section.teacher_id == other_teacher.id


def test_non_relationship_update_uses_persisted_authority():
    school = _school("Providence Classical Academy")
    course = _course(school)
    section = _section(school, course)
    section.save()

    section.teacher_name = "Updated Teacher"
    section.save(update_fields=["teacher_name"])
    section.refresh_from_db()

    assert section.teacher_name == "Updated Teacher"
    assert section.school_id == school.id
    assert section.course_id == course.id


def test_canonical_sections_api_remains_read_only():
    school = _school("Canonical API School")
    course = _course(school)
    user = User.objects.create_user(
        username=f"admin-{uuid.uuid4()}",
        email="admin@canonical.test",
        password="pass12345!",
        school=school,
        is_staff=True,
    )
    client = APIClient()
    client.force_login(user)

    response = client.post(
        "/api/v1/academics/sections/",
        {"course_id": str(course.id), "term": "FALL"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 405
    assert not Section.objects.filter(school_id=school.id).exists()


def test_legacy_sections_writer_rejects_cross_school_course():
    school = _school("Legacy API School A")
    other_school = _school("Legacy API School B")
    other_course = _course(other_school)
    user = User.objects.create_user(
        username=f"admin-{uuid.uuid4()}",
        email="admin@legacy-a.test",
        password="pass12345!",
        school=school,
        is_staff=True,
    )
    request = RequestFactory().post(
        "/legacy/academics/sections/",
        data=json.dumps({"course_id": str(other_course.id), "term": "FALL"}),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    request.user = user

    response = legacy_sections(request)

    assert response.status_code == 404
    assert not Section.objects.filter(school_id=school.id).exists()
