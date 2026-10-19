"""Execution and denial tests for the isolated Heritage scheduling fixture."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.core.management.base import CommandError

from academics.models import Course, Enrollment, Section, Term
from core.legacy_demo_seed_safety import require_local_legacy_fixture_seed
from core.models import AcademicYear, School
from scripts import seed_scheduling


@pytest.fixture
def authorized_seed_env(monkeypatch):
    """Opt in only to local scheduling seeding, without hosted markers."""
    for key in (
        "DJANGO_ENV",
        "ENVIRONMENT",
        "APP_ENV",
        "AZURE_ENVIRONMENT",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_ALLOW_LEGACY_FIXTURE_SEED",
        "CROWN_LEGACY_SCHEDULING_SCHOOL_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", "true")


@pytest.fixture
def local_sqlite_seed(authorized_seed_env, settings):
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        pytest.skip("Legacy fixture execution is permitted only on local SQLite")


@pytest.fixture
def heritage_year(local_sqlite_seed, monkeypatch):
    school = School.objects.create(name="Heritage Christian Academy")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(school.id))
    return school, year


def test_explicit_school_selection_required_before_queries(local_sqlite_seed):
    with pytest.raises(CommandError, match="SCHOOL_ID is required"):
        seed_scheduling.run()


@pytest.mark.parametrize("invalid_id", ["not-a-uuid", "none", ""])
def test_malformed_school_selection_is_refused(local_sqlite_seed, monkeypatch, invalid_id):
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", invalid_id)
    with pytest.raises(CommandError, match="SCHOOL_ID"):
        seed_scheduling.run()


@pytest.mark.django_db
def test_unknown_school_uuid_is_refused_without_writes(local_sqlite_seed, monkeypatch):
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(uuid.uuid4()))
    with pytest.raises(CommandError, match="explicit Heritage demo school"):
        seed_scheduling.run()
    assert not Term.objects.exists()
    assert not Course.objects.exists()
    assert not Section.objects.exists()


@pytest.mark.django_db
def test_non_heritage_school_is_refused(local_sqlite_seed, monkeypatch):
    school = School.objects.create(name="Unrelated School")
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(school.id))
    with pytest.raises(CommandError, match="explicit Heritage demo school"):
        seed_scheduling.run()
    assert not Course.objects.exists()


@pytest.mark.django_db
def test_mixed_school_directory_rejected_without_cross_school_mutations(heritage_year):
    _, heritage_academic_year = heritage_year
    unrelated = School.objects.create(name="Other Christian School")
    other_year = AcademicYear.objects.create(
        school=unrelated,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 10),
        is_current=True,
    )
    with pytest.raises(CommandError, match="single-school"):
        seed_scheduling.run()
    other_year.refresh_from_db()
    heritage_academic_year.refresh_from_db()
    assert other_year.is_current and heritage_academic_year.is_current
    assert Term.objects.count() == 0
    assert Course.objects.count() == 0
    assert Section.objects.count() == 0


@pytest.mark.django_db
def test_requires_exactly_one_current_year(heritage_year):
    school, _ = heritage_year
    AcademicYear.objects.create(
        school=school,
        name="2027-2028",
        start_date=date(2027, 8, 15),
        end_date=date(2028, 6, 10),
        is_current=True,
    )
    with pytest.raises(CommandError, match="Exactly one current"):
        seed_scheduling.run()
    assert not Term.objects.exists()
    assert not Section.objects.exists()


@pytest.mark.django_db
def test_refuses_missing_current_year(heritage_year):
    _, year = heritage_year
    year.is_current = False
    year.save(update_fields=["is_current"])
    with pytest.raises(CommandError, match="Exactly one current"):
        seed_scheduling.run()
    assert not Course.objects.exists()


@pytest.mark.django_db
def test_authorized_heritage_seed_and_replay_are_deterministic(heritage_year):
    school, year = heritage_year
    seed_scheduling.run()
    section_ids = set(Section.objects.values_list("id", flat=True))
    assert len(section_ids) == 4
    assert Term.objects.filter(school_id=school.id, academic_year=year).count() == 1
    assert Course.objects.filter(school_id=school.id).count() == 2
    assert Section.objects.filter(school_id=school.id).count() == 4
    assert Enrollment.objects.count() == 0
    assert all(
        s.term_ref.school_id == school.id
        and s.term_ref.academic_year_id == year.id
        and s.course.school_id == school.id
        and s.teacher_id is None
        for s in Section.objects.select_related("term_ref", "course")
    )
    seed_scheduling.run()
    assert set(Section.objects.values_list("id", flat=True)) == section_ids
    assert Term.objects.count() == 1
    assert Course.objects.count() == 2
    assert Section.objects.count() == 4
    assert Enrollment.objects.count() == 0


@pytest.mark.django_db
def test_reuses_existing_valid_active_term(heritage_year):
    school, year = heritage_year
    existing = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="TERM-1",
        name="First Term",
        school_year=year.name,
        active=True,
        start_date=year.start_date,
        end_date=year.end_date,
        ordering=1,
    )
    seed_scheduling.run()
    assert Term.objects.count() == 1
    assert Section.objects.filter(term_ref=existing).count() == 4
    existing.refresh_from_db()
    assert existing.name == "First Term"


@pytest.mark.django_db
def test_authority_conflict_rolls_back_all_partial_writes(heritage_year):
    school, year = heritage_year
    unrelated_course = Course.objects.create(
        school_id=school.id,
        code="OTHER-101",
        name="Unrelated Fixture",
    )
    conflict_id = seed_scheduling._section_id(school.id, year.id, "ELA-101", "B")
    Section.objects.create(
        id=conflict_id,
        school_id=school.id,
        course=unrelated_course,
        term_ref=None,
        term="UNRELATED",
    )
    with pytest.raises(SystemExit, match="Canonical section authority mismatch"):
        seed_scheduling.run()
    assert not Term.objects.exists()
    assert Course.objects.count() == 1
    assert Section.objects.count() == 1
    assert Section.objects.get(id=conflict_id, school_id=school.id).term == "UNRELATED"


@pytest.mark.parametrize(
    "prod_var",
    ["CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "APP_ENV", "AZURE_ENVIRONMENT"],
)
def test_production_markers_are_refused(authorized_seed_env, monkeypatch, prod_var):
    monkeypatch.setenv(prod_var, "production")
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(uuid.uuid4()))
    with pytest.raises(CommandError, match="production"):
        seed_scheduling.run()


@pytest.mark.parametrize(
    "hosted_marker", ["WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "AZURE_ENVIRONMENT"]
)
def test_hosted_markers_are_refused(authorized_seed_env, monkeypatch, hosted_marker):
    monkeypatch.setenv(hosted_marker, "example.azurewebsites.net")
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(uuid.uuid4()))
    with pytest.raises(CommandError, match="hosted"):
        seed_scheduling.run()


def test_postgresql_rejected_even_when_explicitly_opted_in(
    authorized_seed_env, monkeypatch, settings
):
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(uuid.uuid4()))
    monkeypatch.setitem(
        settings.DATABASES["default"], "ENGINE", "django.db.backends.postgresql"
    )
    with pytest.raises(CommandError, match="SQLite"):
        seed_scheduling.run()


def test_scheduling_requires_its_own_opt_in(authorized_seed_env, monkeypatch):
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "true")
    monkeypatch.delenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED")
    with pytest.raises(CommandError, match="CROWN_ALLOW_LEGACY_SCHEDULING_SEED"):
        seed_scheduling.run()


def test_finance_opt_in_contract_remains_distinct(authorized_seed_env):
    with pytest.raises(CommandError, match="CROWN_ALLOW_LEGACY_FIXTURE_SEED"):
        require_local_legacy_fixture_seed("seed_finance")
