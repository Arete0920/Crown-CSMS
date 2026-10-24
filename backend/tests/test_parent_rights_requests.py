from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.compliance.api.parent_rights import ParentDataRightsRequestView
from apps.compliance.models import ConsentAudit
from core.models import School


class ParentDataRightsRequestTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.school = School.objects.create(name="Rights Request School")
        self.other_school = School.objects.create(name="Other Rights School")
        self.user = get_user_model().objects.create_user(
            username="rights-requester",
            email="rights-requester@example.com",
            password=None,
            school=self.school,
        )

    def submit(self, payload=None, *, user=None, school_id=None, legacy_tenant=None):
        headers = {}
        if school_id is not None:
            headers["HTTP_X_SCHOOL_ID"] = str(school_id)
        request = self.factory.post(
            "/api/v1/compliance/parent-rights/",
            {"request_type": "export"} if payload is None else payload,
            format="json",
            **headers,
        )
        if legacy_tenant is not None:
            request.tenant = legacy_tenant
        force_authenticate(request, user=self.user if user is None else user)
        return ParentDataRightsRequestView.as_view()(request)

    def test_each_request_is_a_receipt_and_never_parental_consent(self):
        for request_type in ("export", "correction", "deletion"):
            with self.subTest(request_type=request_type):
                response = self.submit({"request_type": request_type})
                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.data["status"], "received")
                receipt = ConsentAudit.objects.get(pk=response.data["request_id"])
                self.assertEqual(receipt.consent_type, "data_rights_request")
                self.assertEqual(receipt.tenant_id, str(self.school.pk))
                self.assertEqual(receipt.user_id, self.user.pk)
                self.assertEqual(
                    receipt.metadata,
                    {"request_type": request_type, "status": "received"},
                )
                self.assertIsNone(receipt.ip_address)
        self.assertFalse(
            ConsentAudit.objects.filter(consent_type="parental_consent").exists()
        )

    def test_legacy_tenant_and_payload_cannot_spoof_receipt_authority(self):
        response = self.submit(
            {
                "request_type": "deletion",
                "tenant_id": str(self.other_school.pk),
                "user_id": "another-user",
                "consent_type": "parental_consent",
                "metadata": {"status": "completed"},
            },
            legacy_tenant=SimpleNamespace(id=self.other_school.pk),
        )
        self.assertEqual(response.status_code, 202)
        receipt = ConsentAudit.objects.get(pk=response.data["request_id"])
        self.assertEqual(receipt.tenant_id, str(self.school.pk))
        self.assertEqual(receipt.user_id, self.user.pk)
        self.assertEqual(receipt.metadata["status"], "received")
        self.assertEqual(receipt.consent_type, "data_rights_request")

    def test_cross_school_selection_creates_no_receipt(self):
        response = self.submit(school_id=self.other_school.pk)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ConsentAudit.objects.exists())

    def test_staff_flag_is_not_cross_school_authority(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.submit(school_id=self.other_school.pk)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ConsentAudit.objects.exists())

    def test_missing_school_creates_no_unknown_tenant_receipt(self):
        user = get_user_model().objects.create_user(
            username="unassigned-rights-requester",
            email="unassigned-rights@example.com",
            password=None,
            school=None,
        )
        response = self.submit(user=user)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ConsentAudit.objects.exists())

    def test_invalid_header_creates_no_receipt(self):
        response = self.submit(school_id="not-a-school-uuid")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ConsentAudit.objects.exists())

    def test_inactive_school_creates_no_receipt(self):
        self.school.is_active = False
        self.school.save(update_fields=["is_active"])
        response = self.submit()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ConsentAudit.objects.exists())

    def test_malformed_and_unsupported_requests_create_no_receipt(self):
        for payload in ({}, {"request_type": "consent"}, {"request_type": None}, []):
            with self.subTest(payload=payload):
                response = self.submit(payload)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(ConsentAudit.objects.exists())

    def test_anonymous_request_creates_no_receipt(self):
        request = self.factory.post(
            "/api/v1/compliance/parent-rights/",
            {"request_type": "export"},
            format="json",
        )
        response = ParentDataRightsRequestView.as_view()(request)
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(ConsentAudit.objects.exists())

    def test_storage_failure_never_returns_success(self):
        with patch(
            "apps.compliance.api.parent_rights.ConsentAudit.objects.create",
            side_effect=DatabaseError("synthetic storage failure"),
        ):
            with self.assertRaises(DatabaseError):
                self.submit()
        self.assertFalse(ConsentAudit.objects.exists())

    def test_both_route_aliases_preserve_receipt_contract(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        for path in (
            "/api/compliance/parent-rights/",
            "/api/v1/compliance/parent-rights/",
        ):
            with self.subTest(path=path):
                response = client.post(
                    path,
                    {"request_type": "export"},
                    format="json",
                    HTTP_X_SCHOOL_ID=str(self.school.pk),
                )
                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.data["status"], "received")
                receipt = ConsentAudit.objects.get(pk=response.data["request_id"])
                self.assertEqual(receipt.tenant_id, str(self.school.pk))
