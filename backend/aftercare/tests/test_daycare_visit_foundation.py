"""Synthetic, fail-closed custody visit foundation tests.

No re-entry endpoint or service activation is included in this slice.
"""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from aftercare.models import DaycareAttendance, DaycareReentryAuthorization
from aftercare.daycare_checkin import CheckinRefused
from aftercare.tests.test_daycare_checkin import setup, check
from aftercare.tests.test_daycare_release import release
from core.models import UserRole
from audit.models import AuditLog

pytestmark = pytest.mark.django_db


def test_first_visit_preserves_number_and_never_reenters_without_approval():
    data = setup()
    first = check(data)
    assert first.visit_number == 1
    assert first.reentry_approval_id is None
    release(data, first)
    with pytest.raises(CheckinRefused, match="repeat_same_day_requires_review"):
        check(data)
    assert DaycareAttendance.objects.filter(child=data["child"]).count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count() == 1


def test_director_approval_is_append_only_and_cannot_authorize_unreleased_visit():
    data = setup()
    first = check(data)
    UserRole.objects.create(school=data["school"], user=data["director"], role_code="DAYCARE_DIRECTOR")
    now = timezone.now()
    args = dict(
        school=data["school"], site=data["site"], child=data["child"],
        previous_attendance=first, director=data["director"],
        care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
        approved_at=now, expires_at=now+timedelta(minutes=10),
    )
    with pytest.raises(ValidationError):
        DaycareReentryAuthorization.objects.create(**args)
    assert not DaycareReentryAuthorization.objects.exists()
    release(data, first)
    approval = DaycareReentryAuthorization.objects.create(**args)
    assert approval.previous_attendance_id == first.id
    with pytest.raises(ValidationError):
        approval.save()
    with pytest.raises(ValidationError):
        approval.delete()
    # Approval persistence alone does not activate the check-in service.
    with pytest.raises(CheckinRefused, match="repeat_same_day_requires_review"):
        check(data)
    assert DaycareAttendance.objects.count() == 1


def test_unassigned_staff_cannot_authorize_reentry():
    data = setup()
    first = check(data)
    release(data, first)
    now = timezone.now()
    with pytest.raises(ValidationError):
        DaycareReentryAuthorization.objects.create(
            school=data["school"], site=data["site"], child=data["child"],
            previous_attendance=first, director=data["actor"],
            care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
            approved_at=now, expires_at=now+timedelta(minutes=10),
        )
    assert not DaycareReentryAuthorization.objects.exists()


def test_direct_second_visit_without_approval_denied():
    data = setup()
    first = check(data)
    release(data, first)
    with pytest.raises(ValidationError):
        DaycareAttendance.objects.create(
            school=data["school"], site=data["site"], room=data["room"],
            child=data["child"], program=data["program"],
            enrollment=data["enrollment"], actor=data["actor"],
            care_date=first.care_date, checked_in_at=timezone.now(),
            visit_number=2,
        )
    assert DaycareAttendance.objects.count() == 1
