"""Finance Setup fixture seeding must never invent school IDs or write without consent."""
from datetime import date
from io import StringIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from core.models import AcademicYear, School
from finance_setup.models import FinancePolicyVersion
from finance_setup.services import lock_finance_policies

pytestmark = pytest.mark.django_db
YEAR = "2026-2027"


@pytest.fixture
def demo_school():
    school = School.objects.create(name="Fictional Finance Setup Academy")
    AcademicYear.objects.create(
        school=school, name=YEAR,
        start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
    )
    return school


def _seed(school, *flags):
    return call_command(
        "seed_finance_setup_demo", "--school-id", str(school.id),
        "--year", YEAR, *flags, stdout=StringIO(),
    )


def test_no_implicit_school_ids():
    with pytest.raises(CommandError, match="school-id"):
        call_command("seed_finance_setup_demo", stdout=StringIO())
    assert School.objects.count() == 0
    assert FinancePolicyVersion.objects.count() == 0


def test_legacy_numeric_school_flag_fails_closed():
    with pytest.raises(CommandError, match="Legacy"):
        call_command("seed_finance_setup_demo", "--schools", "2", stdout=StringIO())
    assert FinancePolicyVersion.objects.count() == 0


def test_invalid_uuid_or_foreign_demo_rejected(demo_school):
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        with pytest.raises(CommandError, match="canonical UUID"):
            call_command(
                "seed_finance_setup_demo", "--school-id", "1",
                "--confirm-demo-write", stdout=StringIO(),
            )
        with pytest.raises(CommandError, match="configured"):
            call_command(
                "seed_finance_setup_demo", "--school-id", str(uuid4()),
                "--confirm-demo-write", stdout=StringIO(),
            )
    assert FinancePolicyVersion.objects.count() == 0


def test_missing_configured_school_does_not_provision():
    school_id = uuid4()
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(school_id)):
        with pytest.raises(CommandError, match="Existing fictional demo School"):
            call_command(
                "seed_finance_setup_demo", "--school-id", str(school_id),
                "--confirm-demo-write", stdout=StringIO(),
            )
    assert School.objects.count() == 0


def test_missing_year_does_not_provision():
    school = School.objects.create(name="Fictional Finance Setup Without Year")
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(school.id)):
        with pytest.raises(CommandError, match="AcademicYear"):
            _seed(school, "--confirm-demo-write")
    assert FinancePolicyVersion.objects.count() == 0


def test_dry_run_is_read_only_even_when_debug_false(demo_school):
    with override_settings(DEBUG=False, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        _seed(demo_school, "--dry-run")
    assert FinancePolicyVersion.objects.count() == 0


def test_write_requires_confirmation(demo_school):
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        with pytest.raises(CommandError, match="confirm-demo-write"):
            _seed(demo_school)
    assert FinancePolicyVersion.objects.count() == 0


def test_write_requires_local_debug(demo_school):
    with override_settings(DEBUG=False, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        with pytest.raises(CommandError, match="DEBUG"):
            _seed(demo_school, "--confirm-demo-write")
    assert FinancePolicyVersion.objects.count() == 0


def test_seed_canonical_uuid_once_only(demo_school):
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        _seed(demo_school, "--confirm-demo-write")
        _seed(demo_school, "--confirm-demo-write")
    policy = FinancePolicyVersion.objects.get(school_id=str(demo_school.id), academic_year=YEAR)
    assert policy.aid.application_fee_cents == 5500  # Existing fictional sample, not pricing.
    assert FinancePolicyVersion.objects.count() == 1


def test_locked_policy_cannot_be_replaced(demo_school):
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        _seed(demo_school, "--confirm-demo-write")
        lock_finance_policies(school_id=demo_school.id, academic_year=YEAR)
        with pytest.raises(CommandError, match="locked"):
            _seed(demo_school, "--confirm-demo-write")
    assert FinancePolicyVersion.objects.get(school_id=str(demo_school.id)).is_locked


def test_legacy_integer_policies_remain_unassigned(demo_school):
    legacy = FinancePolicyVersion.objects.create(school_id=1, academic_year=YEAR)
    with override_settings(DEBUG=True, CROWN_DEMO_SCHOOL_ID=str(demo_school.id)):
        _seed(demo_school, "--confirm-demo-write")
    legacy.refresh_from_db()
    assert legacy.school_id == "1"
    assert FinancePolicyVersion.objects.count() == 2
