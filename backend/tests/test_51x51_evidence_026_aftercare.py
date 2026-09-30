"""Extended-care evidence using canonical students and persistent tenant grants."""
import uuid
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from aftercare.models import (
    AftercareAttendance, AftercareEnrollment, AftercareIncident,
    AftercareMonthlyChargeRun, AftercareProgramConfig,
)
from aftercare.services import checkin_student, checkout_student, record_incident, run_monthly_flat_billing
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Household, Student

AFTERCARE_URL = "/api/v1/aftercare/enrollments/"
ROSTER_URL = "/api/v1/aftercare/roster/today/"


def _school():
    return School.objects.create(name=f"M026 {uuid.uuid4().hex[:8]}")


def _student(school):
    household = Household.objects.create(school_id=school.id, name="Evidence household")
    return Student.objects.create(school_id=school.id, household=household,
                                  first_name="Student", last_name="Evidence", grade_level="4")


def _user(school, *, grants=(), is_staff=False):
    token = uuid.uuid4().hex
    user = get_user_model().objects.create_user(username=token, email=f"{token}@example.test",
                                               password="pass1234", school=school, is_staff=is_staff)
    role = f"m026_{token[:8]}"
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in grants:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.create(role_code=role, permission=permission)
    return user


def _client(user, school):
    client = APIClient()
    client.force_authenticate(user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _payload(student):
    return {"student_id": str(student.id), "start_date": "2026-06-01",
            "days_of_week": ["MON", "TUE", "WED", "THU", "FRI"],
            "billing_model": "FLAT_MONTHLY", "monthly_rate": "160.00", "is_active": True}


def _enroll(school, student, **overrides):
    values = dict(school_fk=school, student_fk=student, start_date=date(2026, 6, 1),
                  days_of_week=["MON", "TUE", "WED", "THU", "FRI"],
                  billing_model="FLAT_MONTHLY", monthly_rate="160.00", is_active=True)
    values.update(overrides)
    return AftercareEnrollment.objects.create(**values)


class TestModule026ModelContract(TestCase):
    def test_program_config_uses_canonical_school(self):
        school = _school()
        config = AftercareProgramConfig.objects.create(school_fk=school)
        self.assertEqual(config.school_fk_id, school.id)
        self.assertIsNone(config.school_id)
        self.assertEqual(AftercareProgramConfig._meta.get_field("school_fk").related_model, School)

    def test_enrollment_uses_canonical_student_and_school(self):
        school = _school()
        student = _student(school)
        enrollment = _enroll(school, student)
        self.assertEqual(enrollment.school_fk_id, school.id)
        self.assertEqual(enrollment.student_fk_id, student.id)
        self.assertIsNone(enrollment.student_id)


class TestModule026EnrollmentAndIsolation(TestCase):
    def setUp(self):
        self.school = _school()
        self.student = _student(self.school)

    def test_unauthed_read_and_write_401(self):
        client = APIClient()
        header = {"HTTP_X_SCHOOL_ID": str(self.school.id)}
        self.assertEqual(client.get(AFTERCARE_URL, **header).status_code, 401)
        self.assertEqual(client.post(AFTERCARE_URL, _payload(self.student), format="json", **header).status_code, 401)

    def test_staff_flag_without_persistent_grant_is_forbidden(self):
        client = _client(_user(self.school, is_staff=True), self.school)
        self.assertEqual(client.post(AFTERCARE_URL, _payload(self.student), format="json").status_code, 403)

    def test_granted_write_and_list_are_school_scoped(self):
        foreign = _school()
        foreign_student = _student(foreign)
        _enroll(foreign, foreign_student)
        user = _user(self.school, grants=("extended_care.view", "extended_care.edit"))
        client = _client(user, self.school)
        created = client.post(AFTERCARE_URL, _payload(self.student), format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(client.post(AFTERCARE_URL, _payload(foreign_student), format="json").status_code, 400)
        listed = client.get(AFTERCARE_URL)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual({str(row["student_id"]) for row in listed.data}, {str(self.student.id)})
        self.assertEqual(_client(user, foreign).get(AFTERCARE_URL).status_code, 404)

    @patch("aftercare.api.timezone.now")
    def test_roster_day_and_active_expiry_filtering(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime(2026, 6, 15, 16))
        today = mock_now.return_value.date()
        _enroll(self.school, self.student, days_of_week=["MON"])
        _enroll(self.school, _student(self.school), is_active=False)
        _enroll(self.school, _student(self.school), end_date=today-timedelta(days=1))
        _enroll(self.school, _student(self.school), days_of_week=["TUE"])
        client = _client(_user(self.school, grants=("extended_care.view",)), self.school)
        response = client.get(ROSTER_URL)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["dow"], "MON")
        self.assertEqual({str(row["student_id"]) for row in response.data["rows"]}, {str(self.student.id)})


class TestModule026AttendanceAndBilling(TestCase):
    def setUp(self):
        self.school = _school()
        self.student = _student(self.school)
        _enroll(self.school, self.student)
        self.when = timezone.make_aware(datetime(2026, 6, 15, 15, 5))

    def test_checkin_creates_canonical_attendance(self):
        attendance = checkin_student(self.school.id, self.student.id, when=self.when)
        self.assertTrue(AftercareAttendance.objects.filter(pk=attendance.pk,
                        school_fk=self.school, student_fk=self.student, date=self.when.date()).exists())

    @patch("aftercare.services.create_ledger_charge_aftercare", return_value="obligation-9001")
    def test_checkout_computes_late_fee(self, charge):
        AftercareProgramConfig.objects.create(school_fk=self.school, start_time=time(15), end_time=time(18),
                                             late_fee_per_10_min="10.00", late_fee_cap="100.00")
        checkin_student(self.school.id, self.student.id, when=self.when)
        attendance = checkout_student(self.school.id, self.student.id, pickup_contact_id=None,
                     pickup_name_freeform="Parent", pickup_verified=True,
                     when=timezone.make_aware(datetime(2026, 6, 15, 18, 31)))
        self.assertEqual(attendance.late_minutes, 31)
        self.assertEqual(attendance.late_fee_cents, 4000)
        self.assertEqual(attendance.late_fee_charge_id, "obligation-9001")
        self.assertEqual(charge.call_args.kwargs["student_id"], self.student.id)

    @patch("aftercare.services.create_ledger_charge_aftercare", return_value="obligation-777")
    def test_monthly_billing_idempotent(self, charge):
        first = run_monthly_flat_billing(self.school.id, 2026, 6)
        second = run_monthly_flat_billing(self.school.id, 2026, 6)
        self.assertEqual(first, {"status": "ok", "charged": 1})
        self.assertEqual(second["status"], "already_ran")
        charge.assert_called_once()
        self.assertEqual(charge.call_args.kwargs["student_id"], self.student.id)
        self.assertEqual(AftercareMonthlyChargeRun.objects.filter(school_fk=self.school, year=2026, month=6).count(), 1)


class TestModule026IncidentBehavior(TestCase):
    @patch("aftercare.services.create_discipline_record_for_incident")
    def test_major_incident_links_discipline(self, bridge):
        school = _school()
        student = _student(school)
        bridge.return_value = uuid.uuid4()
        incident = record_incident(school.id, student.id, "MAJOR", "Unsafe conduct")
        self.assertEqual(incident.discipline_record_id, bridge.return_value)
        self.assertEqual(incident.school_fk_id, school.id)
        self.assertEqual(incident.student_fk_id, student.id)
        bridge.assert_called_once()

    @patch("aftercare.services.create_discipline_record_for_incident")
    def test_minor_incident_does_not_link_discipline(self, bridge):
        school = _school()
        incident = record_incident(school.id, _student(school).id, "MINOR", "Minor note")
        self.assertIsNone(incident.discipline_record_id)
        bridge.assert_not_called()
        self.assertEqual(AftercareIncident.objects.filter(school_fk=school).count(), 1)
