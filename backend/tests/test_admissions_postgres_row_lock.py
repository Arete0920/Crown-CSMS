import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication, AdmissionsAuditEvent
from applications.models import Application, ApplicationEvent, ApplicationStatus
from applications.views_admissions import CONTRACT_COUNTERSIGNED, DEPOSIT_PAID, ENROLLMENT_STATE_EVENT_TYPE
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, UserRole
from households.models import Household


User = get_user_model()


class AdmissionsPostgresRowLockTests(TestCase):
    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL-specific SELECT FOR UPDATE regression proof")

        self.school = School.objects.create(
            name=f"Admissions PostgreSQL {uuid.uuid4().hex[:8]}",
            timezone="America/New_York",
            is_active=True,
        )
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 15),
            end_date=date(2027, 6, 15),
            is_current=True,
        )
        family = Family.objects.create(
            school=self.school,
            family_name=f"Family {uuid.uuid4().hex[:6]}",
        )
        self.application = AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=self.year,
            family=family,
            status=AdmissionsApplication.STATUS_ACCEPTED,
            sis_student=None,
        )
        household = Household.objects.create(
            school_id=self.school.id,
            name=f"Canonical Family {uuid.uuid4().hex[:6]}",
        )
        canonical = Application.objects.create(
            school_id=self.school.id,
            household=household,
            status=ApplicationStatus.DECIDED,
        )
        ApplicationEvent.objects.create(
            school_id=self.school.id,
            application=canonical,
            event_type="decision_made",
            payload={"decision": "accepted"},
        )
        ApplicationEvent.objects.create(
            school_id=self.school.id,
            application=canonical,
            event_type=ENROLLMENT_STATE_EVENT_TYPE,
            payload={"contract_status": CONTRACT_COUNTERSIGNED, "deposit_status": DEPOSIT_PAID},
        )
        self.application.notes_internal = f"canonical_application_id={canonical.id}"
        self.application.save(update_fields=["notes_internal", "updated_at"])

        self.user = User.objects.create_user(
            username=f"registrar-{uuid.uuid4().hex[:8]}@example.test",
            password="AdmissionsPostgresTestOnly!",
        )
        UserRole.objects.create(user=self.user, school=self.school, role_code="REGISTRAR")
        permission, _ = CrownPermission.objects.get_or_create(
            code="admissions.edit",
            defaults={"description": "admissions.edit"},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_enroll_nullable_sis_student_locks_only_application_row(self):
        self.assertIsNone(self.application.sis_student_id)

        response = self.client.post(
            "/api/admissions/enroll/",
            {"application_id": self.application.id},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["already_enrolled"])
        self.assertIsNone(response.data["student_id"])

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, AdmissionsApplication.STATUS_ENROLLED)
        self.assertIsNone(self.application.sis_student_id)
        self.assertTrue(
            AdmissionsAuditEvent.objects.filter(
                school=self.school,
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(self.application.id),
                action="STATUS_ENROLLED",
                details_json__source="admissions_enroll_api",
            ).exists()
        )
