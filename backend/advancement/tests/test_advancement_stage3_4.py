from __future__ import annotations

import json
import uuid
from decimal import Decimal

from django.test import TestCase, override_settings

from advancement.models_stage3_4 import EventSponsorPlacement, Receipt, SponsorAsset
from advancement.receipt_render import make_receipt_pdf_bytes
from advancement.stripe_helpers import cents_to_decimal, compute_totals_from_line_items


def _school_and_user():
    from django.contrib.auth import get_user_model

    from core.models import CrownPermission, RolePermission, School, UserRole

    school = School.objects.create(name=f"Stage34 School {uuid.uuid4().hex[:6]}")
    user = get_user_model().objects.create_user(
        username=f"user34_{uuid.uuid4().hex[:8]}",
        password="pass",
        email=f"u34_{uuid.uuid4().hex[:8]}@test.com",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(
        code="advancement.view",
        defaults={"description": "Advancement view (stage34 test)"},
    )
    RolePermission.objects.get_or_create(
        role_code="HEAD_OF_SCHOOL",
        permission=permission,
    )
    return school, user


def _authed_client(user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user)
    return client


class StripeHelpersTest(TestCase):
    def test_cents_to_decimal(self):
        self.assertEqual(cents_to_decimal(2500), Decimal("25.00"))
        self.assertEqual(cents_to_decimal(0), Decimal("0.00"))

    def test_empty_line_items(self):
        totals = compute_totals_from_line_items({"data": []})
        self.assertEqual(totals["subtotal"], Decimal("0.00"))
        self.assertEqual(totals["donation"], Decimal("0.00"))
        self.assertEqual(totals["total"], Decimal("0.00"))

    def test_tickets_only(self):
        totals = compute_totals_from_line_items({"data": [{"amount_total": 5000}]})
        self.assertEqual(totals["subtotal"], Decimal("50.00"))
        self.assertEqual(totals["donation"], Decimal("0.00"))
        self.assertEqual(totals["total"], Decimal("50.00"))

    def test_tickets_plus_donation(self):
        totals = compute_totals_from_line_items(
            {"data": [{"amount_total": 5000}, {"amount_total": 1000}]}
        )
        self.assertEqual(totals["subtotal"], Decimal("50.00"))
        self.assertEqual(totals["donation"], Decimal("10.00"))
        self.assertEqual(totals["total"], Decimal("60.00"))

    def test_fallback_amount_subtotal(self):
        totals = compute_totals_from_line_items({"data": [{"amount_subtotal": 3000}]})
        self.assertEqual(totals["total"], Decimal("30.00"))

    def test_missing_data_key(self):
        self.assertEqual(compute_totals_from_line_items({})["total"], Decimal("0.00"))


class ReceiptModelTest(TestCase):
    def test_create_receipt(self):
        order_id = uuid.uuid4()
        receipt = Receipt.objects.create(
            school_id=uuid.uuid4(),
            order_id=order_id,
            event_id=uuid.uuid4(),
            purchaser_email="buyer@example.com",
            receipt_number=f"R-{str(order_id)[:8]}",
            subtotal=Decimal("50.00"),
            donation=Decimal("10.00"),
            total=Decimal("60.00"),
            provider="fake",
        )
        self.assertEqual(receipt.total, Decimal("60.00"))
        self.assertEqual(receipt.donation, Decimal("10.00"))

    def test_receipt_order_id_unique(self):
        from django.db import IntegrityError

        school_id = uuid.uuid4()
        order_id = uuid.uuid4()
        event_id = uuid.uuid4()
        Receipt.objects.create(
            school_id=school_id,
            order_id=order_id,
            event_id=event_id,
            purchaser_email="a@test.com",
            receipt_number=f"R-UNIQUE-{uuid.uuid4().hex[:6]}",
            subtotal=0,
            donation=0,
            total=0,
        )
        with self.assertRaises(IntegrityError):
            Receipt.objects.create(
                school_id=school_id,
                order_id=order_id,
                event_id=event_id,
                purchaser_email="b@test.com",
                receipt_number=f"R-UNIQUE-{uuid.uuid4().hex[:6]}",
                subtotal=0,
                donation=0,
                total=0,
            )


@override_settings(TENANT_HEADER_REQUIRED=True)
class SponsorPlacementTest(TestCase):
    def test_create_sponsor_asset(self):
        asset = SponsorAsset.objects.create(
            school_id=uuid.uuid4(),
            sponsor_name="Apex Corp",
            logo_url="https://cdn.example.com/apex.png",
        )
        self.assertTrue(asset.is_active)

    def test_event_sponsor_placement(self):
        school_id = uuid.uuid4()
        asset = SponsorAsset.objects.create(
            school_id=school_id,
            sponsor_name="Beta Inc",
            logo_url="https://cdn.example.com/beta.png",
        )
        placement = EventSponsorPlacement.objects.create(
            school_id=school_id,
            event_id=uuid.uuid4(),
            sponsor=asset,
            tier="gold",
            sort_order=1,
        )
        self.assertEqual(placement.sponsor.sponsor_name, "Beta Inc")

    def test_sponsors_endpoint_empty(self):
        school, user = _school_and_user()
        response = _authed_client(user).get(
            f"/api/v1/advancement/events/{uuid.uuid4()}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_sponsors_endpoint_returns_active(self):
        school, user = _school_and_user()
        event_id = uuid.uuid4()
        asset = SponsorAsset.objects.create(
            school_id=school.id,
            sponsor_name="Gamma Ltd",
            logo_url="https://cdn.example.com/gamma.png",
        )
        EventSponsorPlacement.objects.create(
            school_id=school.id,
            event_id=event_id,
            sponsor=asset,
            tier="silver",
        )
        response = _authed_client(user).get(
            f"/api/v1/advancement/events/{event_id}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["sponsor_name"], "Gamma Ltd")
        self.assertEqual(data[0]["tier"], "silver")

    def test_sponsors_endpoint_excludes_inactive(self):
        school, user = _school_and_user()
        event_id = uuid.uuid4()
        asset = SponsorAsset.objects.create(
            school_id=school.id,
            sponsor_name="Inactive Corp",
            logo_url="https://cdn.example.com/inactive.png",
            is_active=False,
        )
        EventSponsorPlacement.objects.create(
            school_id=school.id,
            event_id=event_id,
            sponsor=asset,
            tier="standard",
        )
        response = _authed_client(user).get(
            f"/api/v1/advancement/events/{event_id}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


@override_settings(TENANT_HEADER_REQUIRED=True)
class GoogleWalletTest(TestCase):
    @override_settings(GOOGLE_WALLET_ISSUER_ID="", GOOGLE_WALLET_SERVICE_ACCOUNT_JSON="")
    def test_unconfigured_returns_501(self):
        school, user = _school_and_user()
        response = _authed_client(user).get(
            f"/api/v1/advancement/wallet/google/tickets/{uuid.uuid4()}/link/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(response.status_code, 501)
        self.assertFalse(response.json()["ok"])

    def test_jwt_url_structure(self):
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
        except ImportError:
            self.skipTest("PyJWT / cryptography not installed")

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        ).private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()
        service_account = {
            "type": "service_account",
            "private_key": private_key,
            "client_email": "test@proj.iam.gserviceaccount.com",
        }
        from advancement.google_wallet import make_google_wallet_save_url

        with override_settings(
            GOOGLE_WALLET_SERVICE_ACCOUNT_JSON=json.dumps(service_account),
            GOOGLE_WALLET_ISSUER_ID="9999",
            GOOGLE_WALLET_BASE_URL="https://pay.google.com/gp/v/save/",
        ):
            url = make_google_wallet_save_url(ticket_object_payload={"genericObjects": []})
            self.assertTrue(url.startswith("https://pay.google.com/gp/v/save/"))


@override_settings(TENANT_HEADER_REQUIRED=True)
class AppleWalletTest(TestCase):
    @override_settings(APPLE_PASS_SERVICE_URL="")
    def test_unconfigured_returns_501(self):
        school, user = _school_and_user()
        response = _authed_client(user).get(
            f"/api/v1/advancement/wallet/apple/tickets/{uuid.uuid4()}.pkpass",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertIn(response.status_code, [501, 404])


class ReceiptPDFRenderTest(TestCase):
    def test_pdf_bytes_non_empty(self):
        pdf = make_receipt_pdf_bytes(
            school_name="Test School",
            receipt_no="R-TESTRECEIPT-001",
            event_name="Spring Gala 2026",
            purchaser_name="Jane Buyer",
            purchaser_email="jane@example.com",
            subtotal="50.00",
            donation="10.00",
            total="60.00",
            seat_labels=["VIP-A-1", "VIP-A-2"],
            sponsor_names=["Apex Corp", "Beta Inc"],
        )
        self.assertIsInstance(pdf, bytes)
        self.assertGreater(len(pdf), 500)
        self.assertEqual(pdf[:4], b"%PDF")

    def test_pdf_no_optional_fields(self):
        pdf = make_receipt_pdf_bytes(
            school_name="Minimal School",
            receipt_no="R-MIN-001",
            event_name="Test Event",
            purchaser_name="Bob",
            purchaser_email="bob@example.com",
            subtotal="0.00",
            donation="0.00",
            total="0.00",
        )
        self.assertEqual(pdf[:4], b"%PDF")


class DonationPresetsTest(TestCase):
    @override_settings(DONATION_PRESETS_USD="5,15,50")
    def test_custom_presets(self):
        from advancement.services_stage3_2 import _donation_presets_cents

        self.assertEqual(_donation_presets_cents(), [500, 1500, 5000])

    @override_settings(DONATION_PRESETS_USD="10,25,50")
    def test_default_presets(self):
        from advancement.services_stage3_2 import _donation_presets_cents

        presets = _donation_presets_cents()
        self.assertIn(1000, presets)
        self.assertIn(2500, presets)

    @override_settings(DONATION_PRESETS_USD="bad,data,!!")
    def test_invalid_presets_skipped(self):
        from advancement.services_stage3_2 import _donation_presets_cents

        result = _donation_presets_cents()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])
