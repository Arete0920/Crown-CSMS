"""Synthetic, DB-backed AM/PM extended-care contract and release regressions."""
from datetime import datetime, date

import pytest
from django.utils import timezone

from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercarePickupContact
from aftercare.services import checkin_student, checkout_student, handoff_student_to_school
from core.models import School, UserAccount
from households.models import Household, Student

pytestmark = pytest.mark.django_db
DAY = date(2025, 9, 3)


def at(hour, minute=0):
    return timezone.make_aware(datetime(2025, 9, 3, hour, minute))


def setup_family():
    school = School.objects.create(name="Extended Care Session Test")
    household = Household.objects.create(school_id=school.id, name="One Household")
    child = Student.objects.create(
        school_id=school.id, household=household,
        first_name="One", last_name="Child", grade_level="4",
    )
    for care_session in ("AM", "PM"):
        AftercareEnrollment.objects.create(
            school_fk=school, student_fk=child, care_session=care_session,
            start_date=date(2025, 1, 1), days_of_week=["WED"],
            billing_model="FLAT_MONTHLY",
        )
    receiver = UserAccount.objects.create_user(
        username="extended-care-receiver", password="test", school=school, is_staff=True,
    )
    return school, household, child, receiver


def test_one_child_has_independent_am_and_pm_attendance_and_handoff():
    school, household, child, receiver = setup_family()
    am = checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    handoff = handoff_student_to_school(school.id, child.id, receiver, when=at(8, 25))
    assert handoff.pk == am.pk
    assert handoff.handoff_verified and handoff.handoff_recipient_id == receiver.pk
    assert handoff.checkout_time == at(8, 25)
    pm = checkin_student(school.id, child.id, when=at(15, 5), care_session="PM")
    assert am.pk != pm.pk and pm.handoff_time is None
    assert child.household_id == household.pk
    assert AftercareAttendance.objects.filter(school_fk=school, student_fk=child, date=DAY).count() == 2
    contact = AftercarePickupContact.objects.create(school_fk=school, student_fk=child, name="Guardian")
    released = checkout_student(school.id, child.id, pickup_contact_id=contact.pk,
                                pickup_name_freeform="", pickup_verified=True, when=at(17, 30))
    assert released.pk == pm.pk and released.pickup_verified
    assert released.handoff_time is None


def test_pm_cannot_be_implicitly_checked_in_by_am():
    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    contact = AftercarePickupContact.objects.create(school_fk=school, student_fk=child, name="Guardian")
    with pytest.raises(AftercareAttendance.DoesNotExist):
        checkout_student(school.id, child.id, pickup_contact_id=contact.pk,
                         pickup_name_freeform="", pickup_verified=True, when=at(17, 30))
    assert AftercareAttendance.objects.filter(school_fk=school, student_fk=child).count() == 1


def test_am_handoff_rejects_invalid_receiver_and_replay():
    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    foreign_school = School.objects.create(name="Foreign School")
    other = UserAccount.objects.create_user(username="different-receiver", password="test",
                                             school=foreign_school, is_staff=True)
    with pytest.raises(ValueError, match="this school"):
        handoff_student_to_school(school.id, child.id, other, when=at(8, 15))
    attendance = AftercareAttendance.objects.get(school_fk=school, student_fk=child)
    assert attendance.handoff_time is None
    handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    with pytest.raises(ValueError, match="already"):
        handoff_student_to_school(school.id, child.id, receiver, when=at(8, 20))


def test_am_checkout_denied_and_pm_legacy_default_preserved():
    school, _household, child, _receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    with pytest.raises(ValueError, match="school handoff"):
        checkout_student(school.id, child.id, pickup_contact_id=1,
                         pickup_name_freeform="", pickup_verified=True,
                         when=at(8, 15), care_session="AM")
    pm = checkin_student(school.id, child.id, when=at(15, 0))
    assert pm.care_session == "PM"


def test_absent_am_does_not_block_pm():
    school, _household, child, _receiver = setup_family()
    pm = checkin_student(school.id, child.id, when=at(15, 5), care_session="PM")
    assert pm.care_session == "PM"
    assert not AftercareAttendance.objects.filter(
        school_fk=school, student_fk=child, date=DAY, care_session="AM"
    ).exists()
