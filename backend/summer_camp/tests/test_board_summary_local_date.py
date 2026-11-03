"""Camp board reporting must use the school-local civil date."""
from datetime import date, datetime, time, timedelta, timezone as utc

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
