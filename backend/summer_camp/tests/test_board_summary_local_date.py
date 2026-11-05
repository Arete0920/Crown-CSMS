"""Camp board reporting must use the school-local civil date."""
from datetime import date, datetime, time, timedelta, timezone as utc
from decimal import Decimal

import pytest
from django.utils import timezone
from core.models import School
from summer_camp import services

pytestmark = pytest.mark.django_db

def test_board_summary_uses_school_local_date_across_utc_midnight(monkeypatch):
    school = School.objects.create(name="Fictional reporting boundary", timezone="America/New_York")
    monkeypatch.setattr(
        services.timezone, "now",
        lambda: datetime(2026, 11, 3, 1, 30, tzinfo=utc.utc),
    )
    result = services.board_summary(school.id)
    assert result["as_of"] == "2026-11-02"

def test_board_summary_fails_closed_on_invalid_school_timezone(monkeypatch):
    school = School.objects.create(name="Fictional invalid timezone", timezone="Invalid/NoSuchZone")
    with pytest.raises(ValueError, match="valid school timezone"):
        services.board_summary(school.id)

def test_board_summary_incidents_use_local_month_and_observed_time(monkeypatch):
    from summer_camp.models import SummerCampIncident, SummerCampProgram, SummerCampSession

    # 03:30 UTC November 1 is still October 31 in New York.
    observed = datetime(2026, 11, 1, 3, 30, tzinfo=utc.utc)
    monkeypatch.setattr(services.timezone, "now", lambda: observed)
    school = School.objects.create(
        name="Fictional incident month boundary", timezone="America/New_York",
    )
    program = SummerCampProgram.objects.create(school=school, name="Fictional Camp")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="Fictional month session",
        start_date=date(2026, 10, 1), end_date=date(2026, 11, 30),
        start_time=time(8), end_time=time(15),
    )
    stamps = [
        datetime(2026, 10, 1, 3, 59, tzinfo=utc.utc),  # Sept 30 locally
        datetime(2026, 10, 1, 4, 0, tzinfo=utc.utc),  # Oct 1 locally
        observed - timedelta(minutes=1),             # Oct 31, before observation
        observed + timedelta(minutes=1),             # Oct 31, future
        datetime(2026, 11, 1, 4, 0, tzinfo=utc.utc), # Nov 1 locally
    ]
    for stamp in stamps:
        SummerCampIncident.objects.create(
            school=school, session=session, created_at=stamp,
            description="Fictional local-month incident evidence",
        )

    foreign = School.objects.create(name="Foreign fictional Camp")
    foreign_program = SummerCampProgram.objects.create(school=foreign, name="Other Camp")
    foreign_session = SummerCampSession.objects.create(
        school=foreign, program=foreign_program, name="Other session",
        start_date=date(2026, 10, 1), end_date=date(2026, 11, 30),
        start_time=time(8), end_time=time(15),
    )
    SummerCampIncident.objects.create(
        school=foreign, session=foreign_session, created_at=observed,
        description="Foreign school's private incident",
    )

    summary = services.board_summary(school.id)
    assert summary["as_of"] == "2026-10-31"
    assert summary["incidents_mtd"] == 2
    assert summary["sessions"] == 1



def test_camp_board_requires_verified_ledger_charge_and_deduplicates_links():
    from households.models import Household, Student
    from ledger.models import Charge, LedgerAccount
    from summer_camp.models import (
        SummerCampBillingLedgerLink, SummerCampEnrollment,
        SummerCampProgram, SummerCampSession,
    )

    school = School.objects.create(
        name="Fictional assessed charge school", timezone="America/New_York",
    )
    household = Household.objects.create(school_id=school.id, name="Fictional Camp household")
    child = Student.objects.create(
        school_id=school.id, household=household,
        first_name="Synthetic", last_name="Camper",
    )
    program = SummerCampProgram.objects.create(school=school, name="Fictional Camp")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="Fictional Charge Session",
        start_date=date(2026, 10, 1), end_date=date(2026, 11, 30),
        start_time=time(8), end_time=time(15),
    )
    enrollment = SummerCampEnrollment.objects.create(
        school=school, session=session, student=child, household=household,
    )
    assert services.board_summary(school.id)["gross_revenue_cents"] is None

    account = LedgerAccount.objects.create(school_id=school.id, household=household)
    charge = Charge.objects.create(
        school_id=school.id, account=account, amount=Decimal("125.00"),
        description="Synthetic noncash assessed Camp obligation",
    )
    link = SummerCampBillingLedgerLink.objects.create(
        school=school, enrollment=enrollment,
        charge_id=str(charge.id), amount_cents=12500,
    )
    SummerCampBillingLedgerLink.objects.create(
        school=school, enrollment=enrollment,
        charge_id=str(charge.id), amount_cents=12500,
    )
    assert services.board_summary(school.id)["gross_revenue_cents"] == 12500

    # One inaccurate link invalidates the complete total, not just one row.
    link.amount_cents = 12999
    link.save(update_fields=["amount_cents"])
    assert services.board_summary(school.id)["gross_revenue_cents"] is None
    link.amount_cents = 12500
    link.save(update_fields=["amount_cents"])

    # A syntactically valid UUID that is not a linked school charge is denied.
    from uuid import uuid4
    link.charge_id = str(uuid4())
    link.save(update_fields=["charge_id"])
    assert services.board_summary(school.id)["gross_revenue_cents"] is None


def test_camp_board_cannot_count_foreign_school_ledger_link():
    from households.models import Household, Student
    from ledger.models import Charge, LedgerAccount
    from summer_camp.models import (
        SummerCampBillingLedgerLink, SummerCampEnrollment,
        SummerCampProgram, SummerCampSession,
    )

    school = School.objects.create(name="Synthetic Camp owner", timezone="America/New_York")
    other = School.objects.create(name="Other synthetic Camp owner")
    household = Household.objects.create(school_id=school.id, name="Owned household")
    child = Student.objects.create(
        school_id=school.id, household=household,
        first_name="Synthetic", last_name="Owner",
    )
    program = SummerCampProgram.objects.create(school=school, name="Owned camp")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="Owned session",
        start_date=date(2026, 10, 1), end_date=date(2026, 11, 30),
        start_time=time(8), end_time=time(15),
    )
    enrollment = SummerCampEnrollment.objects.create(
        school=school, session=session, student=child, household=household,
    )
    foreign_household = Household.objects.create(school_id=other.id, name="Foreign household")
    foreign_account = LedgerAccount.objects.create(
        school_id=other.id, household=foreign_household,
    )
    foreign_charge = Charge.objects.create(
        school_id=other.id, account=foreign_account,
        amount=Decimal("75.00"), description="Other school's charge",
    )
    SummerCampBillingLedgerLink.objects.create(
        school=school, enrollment=enrollment,
        charge_id=str(foreign_charge.id), amount_cents=7500,
    )
    assert services.board_summary(school.id)["gross_revenue_cents"] is None
