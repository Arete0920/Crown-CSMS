"""Camp board reporting must use the school-local civil date."""
from datetime import datetime, timezone as utc

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
