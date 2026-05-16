"""
Aftercare service unit tests — ensure_config, checkin_student,
checkout_student, record_incident.

Tests for compute_late_fee live in test_aftercare_late_fee.py.
Tenant scoping tests live in test_aftercare_tenant_scoping.py.
"""
import pytest
from datetime import date, datetime

from django.utils import timezone

from aftercare.services import (
    ensure_config,
    checkin_student,
    checkout_student,
    record_incident,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ensure_config — idempotency
# ---------------------------------------------------------------------------

def test_ensure_config_creates_once():
    """Calling ensure_config twice for the same school returns the same pk."""
    cfg1 = ensure_config(school_id=9001)
    cfg2 = ensure_config(school_id=9001)
    assert cfg1.pk == cfg2.pk


def test_ensure_config_separate_schools():
    """Two different schools get separate AftercareProgramConfig rows."""
    c1 = ensure_config(school_id=9001)
    c2 = ensure_config(school_id=9002)
    assert c1.pk != c2.pk


# ---------------------------------------------------------------------------
# checkin_student / checkout_student — state machine
# ---------------------------------------------------------------------------

def test_checkin_creates_attendance():
    when = timezone.make_aware(datetime(2025, 9, 3, 15, 5))
    ensure_config(school_id=42)
    att = checkin_student(school_id=42, student_id=1001, when=when)
    assert att.pk is not None
    assert att.checkin_time == when
    assert att.checkout_time is None


def test_checkin_idempotent():
    """Checking in the same student twice returns the same attendance row."""
    when = timezone.make_aware(datetime(2025, 9, 3, 15, 5))
    ensure_config(school_id=42)
    att1 = checkin_student(school_id=42, student_id=1002, when=when)
    att2 = checkin_student(school_id=42, student_id=1002, when=when)
    assert att1.pk == att2.pk


def test_checkout_sets_time_and_late_minutes():
    """checkout_student sets checkout_time and records positive late_minutes."""
    cin = timezone.make_aware(datetime(2025, 9, 3, 15, 0))
    cout = timezone.make_aware(datetime(2025, 9, 3, 18, 30))
    ensure_config(school_id=42)
    checkin_student(school_id=42, student_id=1003, when=cin)
    att = checkout_student(
        school_id=42, student_id=1003,
        pickup_contact_id=None, pickup_name_freeform="Parent", pickup_verified=True,
        when=cout,
    )
    assert att.checkout_time is not None
    assert att.late_minutes > 0


# ---------------------------------------------------------------------------
# record_incident — severity routing
# ---------------------------------------------------------------------------

def test_minor_incident_created():
    inc = record_incident(
        school_id=55, student_id=2001,
        severity="MINOR", description="Scuffle",
    )
    assert inc.severity == "MINOR"
    assert inc.parent_notified is False


def test_major_incident_has_discipline_hook():
    """Major incident gets a discipline_record_id set (stub returns 0 in no-op hook)."""
    inc = record_incident(
        school_id=55, student_id=2001,
        severity="MAJOR", description="Serious incident",
    )
    assert inc.severity == "MAJOR"
    assert inc.discipline_record_id is not None
