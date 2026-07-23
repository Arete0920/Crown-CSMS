import uuid
from datetime import date

import pytest
from django.core.exceptions import ValidationError

from academics.models import Term
from core.models import AcademicYear, School


pytestmark = pytest.mark.django_db


def _school(name):
    return School.objects.create(name=name)


def _academic_year(school, name="2026-2027"):
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
    )


def _term(school_id, academic_year_id):
    return Term(
        school_id=school_id,
        academic_year_id=academic_year_id,
        code="FALL",
        name="Fall",
    )


def test_same_school_term_create_succeeds():
    school = _school("Heritage Christian Academy")
    academic_year = _academic_year(school)

    term = _term(school.id, academic_year.id)
    term.save()

    assert Term.objects.filter(pk=term.pk).exists()


def test_same_school_term_accepts_string_uuid_ids():
    school = _school("Harvest Christian School")
    academic_year = _academic_year(school)

    term = _term(str(school.id), str(academic_year.id))
    term.save()

    term.refresh_from_db()
    assert term.school_id == school.id
    assert term.academic_year_id == academic_year.id


def test_cross_school_academic_year_is_rejected_without_persistence():
    school = _school("Faith Christian Academy")
    other_school = _school("Calvary Christian School")
    academic_year = _academic_year(other_school)

    term = _term(school.id, academic_year.id)

    with pytest.raises(ValidationError, match="same school"):
        term.save()

    assert not Term.objects.filter(pk=term.pk).exists()


def test_missing_academic_year_is_rejected():
    school = _school("St. Anne Christian Academy")
    term = _term(school.id, uuid.uuid4())

    with pytest.raises(ValidationError, match="does not exist"):
        term.save()

    assert not Term.objects.filter(pk=term.pk).exists()


def test_partial_relationship_update_is_rejected_and_persistence_is_unchanged():
    school = _school("Grace Covenant School")
    other_school = _school("Providence Christian School")
    academic_year = _academic_year(school)
    other_year = _academic_year(other_school, name="2027-2028")
    term = _term(school.id, academic_year.id)
    term.save()

    term.school_id = other_school.id
    term.academic_year_id = other_year.id
    with pytest.raises(ValidationError, match="updated together"):
        term.save(update_fields=["school_id"])

    term.refresh_from_db()
    assert term.school_id == school.id
    assert term.academic_year_id == academic_year.id


def test_paired_relationship_update_accepts_model_field_name():
    school = _school("Redeemer Christian School")
    other_school = _school("Cornerstone Christian School")
    academic_year = _academic_year(school)
    other_year = _academic_year(other_school, name="2027-2028")
    term = _term(school.id, academic_year.id)
    term.save()

    term.school_id = other_school.id
    term.academic_year = other_year
    term.save(update_fields=["school_id", "academic_year"])

    term.refresh_from_db()
    assert term.school_id == other_school.id
    assert term.academic_year_id == other_year.id
