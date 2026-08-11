import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication, AdmissionsAuditEvent
from admissions.services import InvalidStageTransition, finalize_enrollment
from applications.models import Application, ApplicationEvent, ApplicationStatus
from applications.views_admissions import (
    CONTRACT_COUNTERSIGNED,
    DEPOSIT_PAID,
    ENROLLMENT_STATE_EVENT_TYPE,
)
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, UserRole
from households.models import Household


User = get_user_model()
WIZARD_BASE = "/api/v1/enrollment-conversion-wizard/sessions/"


def _school(name=None):
    return School.objects.create(
        name=name or f"Admissions {uuid.uuid4().hex[:8]}",
        timezone="America/New_York",
        is_active=True,
    )


def _year(school):
    return AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 15),
        is_current=True,
    )


def _application(school, academic_year, status=AdmissionsApplication.STATUS_ACCEPTED):
    family = Family.objects.create(
        school=school,
        family_name=f"Family {uuid.uuid4().hex[:6]}",
    )
    return AdmissionsApplication.objects.create(
        school=school,
        academic_year=academic_year,
        family=family,
        status=status,
    )


def _link_ready_canonical_application(legacy):
    household = Household.objects.create(
        school_id=legacy.school_id,
        name=f"Canonical Family {uuid.uuid4().hex[:6]}",
    )
    canonical = Application.objects.create(
        school_id=legacy.school_id,
        household=household,
        status=ApplicationStatus.DECIDED,
    )
    ApplicationEvent.objects.create(
        school_id=legacy.school_id,
        application=canonical,
        event_type="decision_made",
        payload={"decision": "accepted"},
    )
    ApplicationEvent.objects.create(
        school_id=legacy.school_id,
        application=canonical,
        event_type=ENROLLMENT_STATE_EVENT_TYPE,
        payload={
            "contract_status": CONTRACT_COUNTERSIGNED,
            "deposit_status": DEPOSIT_PAID,
        },
    )
    legacy.notes_internal = f"canonical_application_id={canonical.id}"
    legacy.save(update_fields=["notes_internal", "updated_at"])
    return canonical


def _user_with_permissions(school, *permission_codes):
    user = User.objects.create_user(
        username=f"registrar-{uuid.uuid4().hex[:8]}@example.test",
        password="AdmissionsTestOnly!",
    )
    UserRole.objects.create(user=user, school=school, role_code="REGISTRAR")
    for code in permission_codes:
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": code},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    return user


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


class AdmissionsEnrollmentServiceTests(TestCase):
    def setUp(self):
        self.school = _school()
        self.year = _year(self.school)
        self.user = _user_with_permissions(self.school, "admissions.edit")

    def test_finalize_enrollment_is_guarded_audited_and_idempotent(self):
        app = _application(self.school, self.year)

        app, converted = finalize_enrollment(
            app,
            actor_user=self.user,
            details={"source": "test"},
        )

        self.assertTrue(converted)
        self.assertEqual(app.status, AdmissionsApplication.STATUS_ENROLLED)

        event = AdmissionsAuditEvent.objects.get(
            school=self.school,
            entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
            entity_id=str(app.id),
            action="STATUS_ENROLLED",
        )
        self.assertEqual(event.actor_user, self.user)
        self.assertEqual(event.details_json["source"], "test")

        _app, converted_again = finalize_enrollment(app, actor_user=self.user)
        self.assertFalse(converted_again)
        self.assertEqual(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
            ).count(),
            1,
        )

    def test_finalize_enrollment_refreshes_stale_instance_before_idempotency_check(self):
        app = _application(self.school, self.year)
        stale_app = AdmissionsApplication.objects.get(pk=app.pk)

        enrolled_app, converted = finalize_enrollment(app, actor_user=self.user)
        self.assertTrue(converted)
        self.assertEqual(enrolled_app.status, AdmissionsApplication.STATUS_ENROLLED)
        self.assertEqual(stale_app.status, AdmissionsApplication.STATUS_ACCEPTED)

        refreshed_app, converted_again = finalize_enrollment(stale_app, actor_user=self.user)

        self.assertFalse(converted_again)
        self.assertEqual(refreshed_app.status, AdmissionsApplication.STATUS_ENROLLED)
        self.assertEqual(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
            ).count(),
            1,
        )

    def test_waitlisted_application_cannot_skip_acceptance(self):
        app = _application(
            self.school,
            self.year,
            status=AdmissionsApplication.STATUS_WAITLISTED,
        )

        with self.assertRaises(InvalidStageTransition):
            finalize_enrollment(app, actor_user=self.user)

        app.refresh_from_db()
        self.assertEqual(app.status, AdmissionsApplication.STATUS_WAITLISTED)
        self.assertFalse(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
            ).exists()
        )


class AdmissionsEnrollmentApiTests(TestCase):
    def setUp(self):
        self.school = _school()
        self.year = _year(self.school)
        self.client = APIClient()

    def test_non_staff_registrar_with_admissions_edit_can_enroll(self):
        user = _user_with_permissions(self.school, "admissions.edit")
        app = _application(self.school, self.year)
        _link_ready_canonical_application(app)
        self.assertFalse(user.is_staff)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/api/admissions/enroll/",
            {"application_id": app.id},
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["already_enrolled"])
        app.refresh_from_db()
        self.assertEqual(app.status, AdmissionsApplication.STATUS_ENROLLED)
        self.assertTrue(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
            ).exists()
        )

    def test_enroll_requires_tenant_scoped_admissions_edit(self):
        user = _user_with_permissions(self.school)
        app = _application(self.school, self.year)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/api/admissions/enroll/",
            {"application_id": app.id},
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 403)
        app.refresh_from_db()
        self.assertEqual(app.status, AdmissionsApplication.STATUS_ACCEPTED)

    def test_non_staff_registrar_with_admissions_view_can_read_linkage_list(self):
        user = _user_with_permissions(self.school, "admissions.view")
        self.client.force_authenticate(user=user)

        response = self.client.get(
            "/api/admissions/applications/",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 200)


class EnrollmentConversionWizardIntegrityTests(TestCase):
    def setUp(self):
        self.school = _school()
        self.year = _year(self.school)
        self.user = _user_with_permissions(self.school, "admissions.edit")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _session(self):
        response = self.client.post(WIZARD_BASE, **_headers(self.school))
        self.assertEqual(response.status_code, 201)
        return response.data["session_id"]

    def _loaded_session(self, app):
        session_id = self._session()
        configured = self.client.post(
            f"{WIZARD_BASE}{session_id}/configure/",
            {"academic_year_label": self.year.name, "from_status": "ACCEPTED"},
            format="json",
            **_headers(self.school),
        )
        self.assertEqual(configured.status_code, 200)
        loaded = self.client.post(
            f"{WIZARD_BASE}{session_id}/load/",
            {},
            format="json",
            **_headers(self.school),
        )
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.data["applicant_count"], 1)
        return session_id

    def test_waitlisted_cannot_be_configured_for_direct_conversion(self):
        session_id = self._session()
        response = self.client.post(
            f"{WIZARD_BASE}{session_id}/configure/",
            {"academic_year_label": self.year.name, "from_status": "WAITLISTED"},
            format="json",
            **_headers(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_commit_uses_guarded_audited_enrollment_service(self):
        app = _application(self.school, self.year)
        session_id = self._loaded_session(app)

        response = self.client.post(
            f"{WIZARD_BASE}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["converted"], 1)
        self.assertEqual(response.data["selected"], 1)
        app.refresh_from_db()
        self.assertEqual(app.status, AdmissionsApplication.STATUS_ENROLLED)
        self.assertTrue(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
                details_json__source="enrollment_conversion_wizard",
            ).exists()
        )

        verify = self.client.get(
            f"{WIZARD_BASE}{session_id}/verify/",
            **_headers(self.school),
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.data["all_enrolled"])
        self.assertEqual(verify.data["enrolled_count"], 1)
        self.assertEqual(verify.data["selected_count"], 1)

    def test_commit_fails_closed_if_loaded_application_status_drifts(self):
        app = _application(self.school, self.year)
        session_id = self._loaded_session(app)
        app.status = AdmissionsApplication.STATUS_WAITLISTED
        app.save(update_fields=["status"])

        response = self.client.post(
            f"{WIZARD_BASE}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 409)
        app.refresh_from_db()
        self.assertEqual(app.status, AdmissionsApplication.STATUS_WAITLISTED)
        self.assertFalse(
            AdmissionsAuditEvent.objects.filter(
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id=str(app.id),
                action="STATUS_ENROLLED",
            ).exists()
        )
