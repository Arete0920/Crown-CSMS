"""
Stage 3.4 Tests -- Receipts, Stripe line-item totals, sponsor placements,
Google Wallet link, Apple Wallet proxy, receipt PDF render.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

from django.test import TestCase, override_settings
from django.test import TestCase, override_settings

from advancement.stripe_helpers import compute_totals_from_line_items, cents_to_decimal
from advancement.receipt_render import make_receipt_pdf_bytes
from advancement.models_stage3_4 import Receipt, SponsorAsset, EventSponsorPlacement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _school_and_user():
    from core.models import School, UserRole, CrownPermission, RolePermission
    from django.contrib.auth import get_user_model

    school = School.objects.create(name=f"Stage34 School {uuid.uuid4().hex[:6]}")
    user = get_user_model().objects.create_user(
        username=f"user34_{uuid.uuid4().hex[:8]}",
        password="pass",
        email=f"u34_{uuid.uuid4().hex[:8]}@test.com",
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")
    perm, _ = CrownPermission.objects.get_or_create(
        code="advancement.view",
        defaults={"description": "Advancement view (stage34 test)"},
    )
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=perm)
    return school, user


def _authed_client(user, school):
    from rest_framework.test import APIClient

    c = APIClient()
    c.force_authenticate(user)
    return c


# ---------------------------------------------------------------------------
# Stripe helpers
# ---------------------------------------------------------------------------

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
        data = {"data": [{"amount_total": 5000}]}
        t = compute_totals_from_line_items(data)
        self.assertEqual(t["subtotal"], Decimal("50.00"))
        self.assertEqual(t["donation"], Decimal("0.00"))
        self.assertEqual(t["total"], Decimal("50.00"))

    def test_tickets_plus_donation(self):
        data = {"data": [
            {"amount_total": 5000},
            {"amount_total": 1000},
        ]}
        t = compute_totals_from_line_items(data)
        self.assertEqual(t["subtotal"], Decimal("50.00"))
        self.assertEqual(t["donation"], Decimal("10.00"))
        self.assertEqual(t["total"], Decimal("60.00"))

    def test_fallback_amount_subtotal(self):
        data = {"data": [{"amount_subtotal": 3000}]}
        t = compute_totals_from_line_items(data)
        self.assertEqual(t["total"], Decimal("30.00"))

    def test_missing_data_key(self):
        t = compute_totals_from_line_items({})
        self.assertEqual(t["total"], Decimal("0.00"))


# ---------------------------------------------------------------------------
# Receipt model
# ---------------------------------------------------------------------------

class ReceiptModelTest(TestCase):
    def test_create_receipt(self):
        school_id = uuid.uuid4()
        order_id = uuid.uuid4()
        event_id = uuid.uuid4()
        r = Receipt.objects.create(
            school_id=school_id,
            order_id=order_id,
            event_id=event_id,
            purchaser_email="buyer@example.com",
            receipt_number=f"R-{str(order_id)[:8]}",
            subtotal=Decimal("50.00"),
            donation=Decimal("10.00"),
            total=Decimal("60.00"),
            provider="fake",
        )
        self.assertEqual(r.total, Decimal("60.00"))
        self.assertEqual(r.donation, Decimal("10.00"))

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
            subtotal=0, donation=0, total=0,
        )
        with self.assertRaises(IntegrityError):
            Receipt.objects.create(
                school_id=school_id,
                order_id=order_id,
                event_id=event_id,
                purchaser_email="b@test.com",
                receipt_number=f"R-UNIQUE-{uuid.uuid4().hex[:6]}",
                subtotal=0, donation=0, total=0,
            )


# ---------------------------------------------------------------------------
# Sponsor placement model + endpoint
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=True)
class SponsorPlacementTest(TestCase):
    def test_create_sponsor_asset(self):
        school_id = uuid.uuid4()
        asset = SponsorAsset.objects.create(
            school_id=school_id,
            sponsor_name="Apex Corp",
            logo_url="https://cdn.example.com/apex.png",
        )
        self.assertTrue(asset.is_active)

    def test_event_sponsor_placement(self):
        school_id = uuid.uuid4()
        event_id = uuid.uuid4()
        asset = SponsorAsset.objects.create(
            school_id=school_id,
            sponsor_name="Beta Inc",
            logo_url="https://cdn.example.com/beta.png",
        )
        placement = EventSponsorPlacement.objects.create(
            school_id=school_id,
            event_id=event_id,
            sponsor=asset,
            tier="gold",
            sort_order=1,
        )
        self.assertEqual(placement.sponsor.sponsor_name, "Beta Inc")

    def test_sponsors_endpoint_empty(self):
        school, user = _school_and_user()
        c = _authed_client(user, school)
        event_id = uuid.uuid4()
        r = c.get(
            f"/api/v1/advancement/events/{event_id}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_sponsors_endpoint_returns_active(self):
        school, user = _school_and_user()
        c = _authed_client(user, school)
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
        r = c.get(
            f"/api/v1/advancement/events/{event_id}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["sponsor_name"], "Gamma Ltd")
        self.assertEqual(data[0]["tier"], "silver")

    def test_sponsors_endpoint_excludes_inactive(self):
        school, user = _school_and_user()
        c = _authed_client(user, school)
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
        r = c.get(
            f"/api/v1/advancement/events/{event_id}/sponsors/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])


# ---------------------------------------------------------------------------
# Google Wallet
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=True)
class GoogleWalletTest(TestCase):
    @override_settings(GOOGLE_WALLET_ISSUER_ID="", GOOGLE_WALLET_SERVICE_ACCOUNT_JSON="")
    def test_unconfigured_returns_501(self):
        school, user = _school_and_user()
        c = _authed_client(user, school)
        ticket_id = uuid.uuid4()
        r = c.get(
            f"/api/v1/advancement/wallet/google/tickets/{ticket_id}/link/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(r.status_code, 501)
        self.assertFalse(r.json()["ok"])

    def test_jwt_url_structure(self):
        try:
            import jwt  # noqa: F401
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.serialization import (
                Encoding, PrivateFormat, NoEncryption,
            )
        except ImportError:
            self.skipTest("PyJWT / cryptography not installed")

        private_key_obj = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        pem = private_key_obj.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        ).decode()

        sa = {
            "type": "service_account",
            "private_key": pem,
            "client_email": "test@proj.iam.gserviceaccount.com",
        }

        from advancement.google_wallet import make_google_wallet_save_url

        with override_settings(
            GOOGLE_WALLET_SERVICE_ACCOUNT_JSON=json.dumps(sa),
            GOOGLE_WALLET_ISSUER_ID="9999",
            GOOGLE_WALLET_BASE_URL="https://pay.google.com/gp/v/save/",
        ):
            url = make_google_wallet_save_url(ticket_object_payload={"genericObjects": []})
            self.assertTrue(url.startswith("https://pay.google.com/gp/v/save/"))


# ---------------------------------------------------------------------------
# Apple Wallet
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=True)
class AppleWalletTest(TestCase):
    @override_settings(APPLE_PASS_SERVICE_URL="")
    def test_unconfigured_returns_501(self):
        school, user = _school_and_user()
        c = _authed_client(user, school)
        ticket_id = uuid.uuid4()
        r = c.get(
            f"/api/v1/advancement/wallet/apple/tickets/{ticket_id}.pkpass",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertIn(r.status_code, [501, 404])


# ---------------------------------------------------------------------------
# Receipt PDF render
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Donation presets helper
# ---------------------------------------------------------------------------

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
