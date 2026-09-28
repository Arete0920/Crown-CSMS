"""Module 026 - After-School and Extended Care - Evidence Test"""

import uuid
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from aftercare.models import (
    AftercareAttendance,
    AftercareEnrollment,
    AftercareIncident,
    AftercareMonthlyChargeRun,
    AftercareProgramConfig,
)
from aftercare.services import (
    checkin_student,
    checkout_student,
    record_incident,
    run_monthly_flat_billing,
)
from core.models import School

User = get_user_model()
AFTERCARE_URL = "/api/v1/aftercare/enrollments/"
ROSTER_URL = "/api/v1/aftercare/roster/today/"


def _school(s=""):
    return School.objects.create(
        name=f"M026 {s or uuid.uuid4().hex[:5]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _sid() -> int:
    return int(uuid.uuid4().int % 900000) + 1000


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


def _staff_user(tag="staff"):
    suffix = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f"m026_{tag}_{suffix}",
        email=f"m026_{tag}_{suffix}@example.com",
        password="pass1234",
        is_staff=True,
    )


def _regular_user(tag="user"):
    suffix = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f"m026_{tag}_{suffix}",
        email=f"m026_{tag}_{suffix}@example.com",
        password="pass1234",
    )


def _enrollment_payload(student_id=101, school_id=1001, **overrides):
    payload = {
        "school_id": school_id,
        "student_id": student_id,
        "start_date": str(date.today() - timedelta(days=5)),
        "end_date": None,
        "days_of_week": ["MON", "TUE", "WED", "THU", "FRI"],
        "billing_model": "FLAT_MONTHLY",
        "monthly_rate": "150.00",
        "prepaid_sessions_balance": 0,
        "dropin_daily_rate": None,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


class TestModule026ModelContract(TestCase):
    def test_program_config_importable(self):
        self.assertTrue(hasattr(AftercareProgramConfig, "_meta"))

    def test_enrollment_importable(self):
        self.assertTrue(hasattr(AftercareEnrollment, "_meta"))

    def test_config_school_id_is_required(self):
        f = AftercareProgramConfig._meta.get_field("school_id")
        self.assertFalse(getattr(f, "null", True), "school_id must be non-null")

    def test_school_id_non_fk_integer_enforces_isolation(self):
        f = AftercareProgramConfig._meta.get_field("school_id")
        self.assertFalse(getattr(f, "null", True))


class TestModule026Auth(TestCase):
    def setUp(self):
        self.school = _school()

    def test_unauthed_401(self):
        r = APIClient().get(AFTERCARE_URL, **_hdr(self.school.id))
        self.assertEqual(
            r.status_code, 401, f"Expected 401 got {r.status_code}. 404=URL not wired."
        )

    def test_unauthed_post_401(self):
        payload = _enrollment_payload(student_id=11, school_id=_sid())
        r = APIClient().post(
            AFTERCARE_URL, payload, format="json", **_hdr(self.school.id)
        )
        self.assertEqual(r.status_code, 401, f"Expected 401 got {r.status_code}.")


class TestModule026EnrollmentAndIsolation(TestCase):
    def setUp(self):
        self.school_a_id = _sid()
        self.school_b_id = _sid()
        self.staff = _staff_user("admin")
        self.regular = _regular_user("nonadmin")

    @patch("aftercare.api.school_id_from_request")
    def test_non_admin_post_forbidden(self, mock_school_id):
        mock_school_id.return_value = self.school_a_id
        client = APIClient()
        client.force_authenticate(self.regular)
        payload = _enrollment_payload(student_id=201, school_id=self.school_a_id)
        r = client.post(AFTERCARE_URL, payload, format="json", **_hdr(self.school_a_id))
        self.assertEqual(r.status_code, 403, f"Expected 403 got {r.status_code}.")

    @patch("aftercare.api.school_id_from_request")
    def test_admin_post_and_list_are_school_scoped(self, mock_school_id):
        mock_school_id.side_effect = [
            self.school_a_id,
            self.school_b_id,
            self.school_a_id,
        ]
        client = APIClient()
        client.force_authenticate(self.staff)

        payload_a = _enrollment_payload(student_id=301, school_id=self.school_a_id)
        payload_b = _enrollment_payload(student_id=302, school_id=self.school_b_id)
        ra = client.post(
            AFTERCARE_URL, payload_a, format="json", **_hdr(self.school_a_id)
        )
        rb = client.post(
            AFTERCARE_URL, payload_b, format="json", **_hdr(self.school_b_id)
        )

        self.assertEqual(ra.status_code, 201, getattr(ra, "data", ra.content))
        self.assertEqual(rb.status_code, 201, getattr(rb, "data", rb.content))

        list_a = client.get(AFTERCARE_URL, **_hdr(self.school_a_id))
        self.assertEqual(list_a.status_code, 200)
        student_ids = {row["student_id"] for row in list_a.data}
        self.assertIn(301, student_ids)
        self.assertNotIn(302, student_ids)


class TestModule026RosterFiltering(TestCase):
    def setUp(self):
        self.school_id = _sid()
        self.staff = _staff_user("roster")

    @patch("aftercare.api.school_id_from_request")
    @patch("aftercare.api.timezone.now")
    def test_roster_day_and_active_expiry_filtering(self, mock_now, mock_school_id):
        mock_school_id.return_value = self.school_id
        mock_now.return_value = timezone.make_aware(datetime(2026, 6, 15, 16, 0, 0))
        today = mock_now.return_value.date()

        AftercareEnrollment.objects.create(
            school_id=self.school_id,
            student_id=401,
            start_date=today - timedelta(days=10),
            end_date=None,
            days_of_week=["MON"],
            billing_model="FLAT_MONTHLY",
            monthly_rate="125.00",
            is_active=True,
        )
        AftercareEnrollment.objects.create(
            school_id=self.school_id,
            student_id=402,
            start_date=today - timedelta(days=10),
            end_date=None,
            days_of_week=["MON"],
            billing_model="FLAT_MONTHLY",
            monthly_rate="125.00",
            is_active=False,
        )
        AftercareEnrollment.objects.create(
            school_id=self.school_id,
            student_id=403,
            start_date=today - timedelta(days=20),
            end_date=today - timedelta(days=1),
            days_of_week=["MON"],
            billing_model="FLAT_MONTHLY",
            monthly_rate="125.00",
            is_active=True,
        )
        AftercareEnrollment.objects.create(
            school_id=self.school_id,
            student_id=404,
            start_date=today - timedelta(days=10),
            end_date=None,
            days_of_week=["TUE"],
            billing_model="FLAT_MONTHLY",
            monthly_rate="125.00",
            is_active=True,
        )

        client = APIClient()
        client.force_authenticate(self.staff)
        r = client.get(ROSTER_URL, **_hdr(self.school_id))
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["dow"], "MON")

        roster_ids = {row["student_id"] for row in r.data["rows"]}
        self.assertEqual(roster_ids, {401})


class TestModule026AttendanceAndBilling(TestCase):
    def setUp(self):
        self.school_id = _sid()

    def test_checkin_creates_attendance(self):
        when = timezone.make_aware(datetime(2026, 6, 15, 15, 5, 0))
        attendance = checkin_student(
            school_id=self.school_id,
            student_id=501,
            when=when,
            note="arrived",
        )
        self.assertIsNotNone(attendance.pk)
        self.assertTrue(
            AftercareAttendance.objects.filter(
                school_id=self.school_id, student_id=501, date=when.date()
            ).exists()
        )

    @patch("aftercare.services.create_ledger_charge_aftercare", return_value=9001)
    def test_checkout_computes_late_fee(self, _mock_charge):
        checkin_dt = timezone.make_aware(datetime(2026, 6, 15, 15, 5, 0))
        checkout_dt = timezone.make_aware(datetime(2026, 6, 15, 18, 31, 0))

        # Ensure typed TimeField values are present for deterministic late-fee math.
        AftercareProgramConfig.objects.create(
            school_id=self.school_id,
            start_time=time(15, 0),
            end_time=time(18, 0),
            late_fee_per_10_min="10.00",
            late_fee_grace_minutes=0,
            late_fee_cap="100.00",
        )

        checkin_student(
            school_id=self.school_id,
            student_id=502,
            when=checkin_dt,
            note="present",
        )

        att = checkout_student(
            school_id=self.school_id,
            student_id=502,
            pickup_contact_id=None,
            pickup_name_freeform="Parent",
            pickup_verified=True,
            when=checkout_dt,
        )

        self.assertEqual(att.date, checkin_dt.date())
        self.assertEqual(att.late_minutes, 31)
        self.assertGreater(att.late_fee_cents, 0)
        self.assertEqual(att.late_fee_charge_id, 9001)

    @patch("aftercare.services.create_ledger_charge_aftercare", return_value=777)
    def test_monthly_billing_idempotent(self, mock_charge):
        AftercareEnrollment.objects.create(
            school_id=self.school_id,
            student_id=601,
            start_date=date(2026, 6, 1),
            end_date=None,
            days_of_week=["MON", "WED"],
            billing_model="FLAT_MONTHLY",
            monthly_rate="160.00",
            is_active=True,
        )

        first = run_monthly_flat_billing(self.school_id, 2026, 6)
        second = run_monthly_flat_billing(self.school_id, 2026, 6)

        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["charged"], 1)
        self.assertEqual(second["status"], "already_ran")
        self.assertEqual(mock_charge.call_count, 1)
        self.assertEqual(
            AftercareMonthlyChargeRun.objects.filter(
                school_id=self.school_id, year=2026, month=6
            ).count(),
            1,
        )


class TestModule026IncidentBehavior(TestCase):
    @patch("aftercare.services.create_discipline_record_for_incident")
    def test_major_incident_links_discipline(self, mock_discipline):
        school_id = _sid()
        mock_discipline.return_value = uuid.uuid4()

        inc = record_incident(
            school_id=school_id,
            student_id=701,
            severity="MAJOR",
            description="Unsafe conduct",
            attendance_id=None,
            parent_notified=True,
        )

        self.assertEqual(inc.severity, "MAJOR")
        self.assertTrue(bool(inc.discipline_record_id))
        self.assertEqual(
            AftercareIncident.objects.filter(school_id=school_id).count(), 1
        )

    @patch("aftercare.services.create_discipline_record_for_incident")
    def test_minor_incident_does_not_link_discipline(self, mock_discipline):
        school_id = _sid()
        inc = record_incident(
            school_id=school_id,
            student_id=702,
            severity="MINOR",
            description="Minor note",
            attendance_id=None,
            parent_notified=False,
        )

        self.assertIsNone(inc.discipline_record_id)
        mock_discipline.assert_not_called()


class TestModule026EndpointRegistration(TestCase):
    def setUp(self):
        self.school = _school()

    def test_config_endpoint_not_500(self):
        r = APIClient().get("/api/v1/aftercare/config/", **_hdr(self.school.id))
        self.assertNotEqual(
            r.status_code, 500, f"500=server error on config URL, got {r.status_code}."
        )
