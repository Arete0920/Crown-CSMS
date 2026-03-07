"""
Advancement Platform — Stage 2 Tests

Coverage:
  1.  FakeProvider create_checkout_session returns provider_payment_id
  2.  get_provider() returns FakeProvider when setting is "fake"
  3.  create_gift_checkout creates pending Gift with provider metadata
  4.  mark_gift_paid transitions pending → paid, creates AdvancementTransaction
  5.  mark_gift_paid updates Donor.lifetime_giving
  6.  mark_gift_paid updates Campaign.raised and donors_count
  7.  mark_gift_paid raises ValueError when gift already paid
  8.  create_pledge creates an active Pledge
  9.  cancel_pledge transitions active → cancelled
 10.  cancel_pledge raises ValueError when already cancelled
 11.  create_sponsorship_checkout creates pending SponsorshipAgreement
 12.  mark_sponsorship_paid transitions pending → active, creates AdvancementTransaction
 13.  mark_sponsorship_paid raises ValueError when status is not pending
 14.  check_in_ticket_by_qr accepted path — Ticket.checked_in=True
 15.  check_in_ticket_by_qr duplicate path — result="duplicate", Ticket unchanged
 16.  check_in_ticket_by_qr invalid path — result="invalid", ticket FK is None
 17.  Gift tenant isolation — school A cannot see school B gifts
 18.  Pledge tenant isolation
 19.  SponsorshipAgreement tenant isolation
 20.  TicketScan audit trail created for every scan type
"""
import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import School
from advancement.models import (
    Donor,
    Campaign,
    Event,
    Gift,
    Pledge,
    SponsorshipAgreement,
    SponsorshipPackage,
    Ticket,
    TicketScan,
    AdvancementTransaction,
)
from advancement.payments.providers import FakeProvider
from advancement.payments.service import get_provider
from advancement.services_stage2 import (
    create_gift_checkout,
    mark_gift_paid,
    create_pledge,
    cancel_pledge,
    create_sponsorship_checkout,
    mark_sponsorship_paid,
    check_in_ticket_by_qr,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sid(n: int = 1) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-0000-0000-{n:012d}")


def _ensure_school(sid: uuid.UUID) -> School:
    school, _ = School.objects.get_or_create(id=sid, defaults={"name": f"S2 School {sid}"})
    return school


def _make_donor(school_id, name="Alice Donor") -> Donor:
    return Donor.objects.create(school_id=school_id, name=name, email="alice@donor.test")


def _make_campaign(school_id, goal="50000") -> Campaign:
    return Campaign.objects.create(
        school_id=school_id,
        name="Stage2 Capital Campaign",
        goal=Decimal(goal),
        start_date=date.today(),
    )


def _make_package(school_id, price="1000") -> SponsorshipPackage:
    return SponsorshipPackage.objects.create(
        school_id=school_id,
        name="Gold Package",
        price=Decimal(price),
    )


def _make_event(school_id, capacity=5) -> Event:
    return Event.objects.create(
        school_id=school_id,
        name="Stage2 Gala",
        date=timezone.now() + timezone.timedelta(days=14),
        ticket_price=Decimal("50.00"),
        capacity=capacity,
        active=True,
    )


def _make_ticket(event, school_id, qr="QR_STAGE2_001", checked_in=False) -> Ticket:
    return Ticket.objects.create(
        school_id=school_id,
        event=event,
        purchaser_name="Bob Buyer",
        purchaser_email="bob@buyer.test",
        qr_code=qr,
        checked_in=checked_in,
    )


# ---------------------------------------------------------------------------
# Provider / payment layer
# ---------------------------------------------------------------------------

class FakeProviderTest(TestCase):
    """Tests for FakeProvider and get_provider() factory."""

    def test_create_checkout_session_returns_payment_id(self):
        provider = FakeProvider()
        result = provider.create_checkout_session(
            amount=100.0, currency="usd", metadata={}
        )
        self.assertIn("provider_payment_id", result)
        self.assertTrue(result["provider_payment_id"].startswith("fake_"))

    def test_create_checkout_session_returns_checkout_url(self):
        provider = FakeProvider()
        result = provider.create_checkout_session(100.0, "usd", {})
        self.assertIn("checkout_url", result)

    def test_retrieve_payment_status_returns_pending(self):
        provider = FakeProvider()
        status = provider.retrieve_payment_status("fake_abc123")
        self.assertEqual(status, "pending")

    def test_get_provider_returns_fake_provider(self):
        provider = get_provider()
        self.assertIsInstance(provider, FakeProvider)


# ---------------------------------------------------------------------------
# Gift checkout + mark_paid
# ---------------------------------------------------------------------------

class GiftCheckoutTest(TestCase):

    def setUp(self):
        self.sid = _sid(10)
        _ensure_school(self.sid)

    def test_create_gift_checkout_creates_pending_gift(self):
        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("250.00"))
        self.assertIsNotNone(gift.id)
        self.assertEqual(gift.status, "pending")
        self.assertEqual(gift.school_id, self.sid)

    def test_create_gift_checkout_stores_provider_id(self):
        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("100.00"))
        self.assertTrue(gift.provider_payment_id.startswith("fake_"))
        self.assertEqual(gift.provider, "fake")

    def test_mark_gift_paid_transitions_to_paid(self):
        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("300.00"))
        paid = mark_gift_paid(gift_id=gift.id, school_id=self.sid)
        self.assertEqual(paid.status, "paid")

    def test_mark_gift_paid_creates_advancement_transaction(self):
        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("150.00"))
        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
        txn = AdvancementTransaction.objects.filter(school_id=self.sid, category="donation").last()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, Decimal("150.00"))

    def test_mark_gift_paid_updates_donor_lifetime_giving(self):
        donor = _make_donor(self.sid)
        gift = create_gift_checkout(
            school_id=self.sid, amount=Decimal("500.00"), donor_id=donor.id
        )
        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
        donor.refresh_from_db()
        self.assertEqual(donor.lifetime_giving, Decimal("500.00"))

    def test_mark_gift_paid_updates_campaign_raised_and_count(self):
        campaign = _make_campaign(self.sid)
        gift = create_gift_checkout(
            school_id=self.sid, amount=Decimal("1000.00"), campaign_id=campaign.id
        )
        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
        campaign.refresh_from_db()
        self.assertEqual(campaign.raised, Decimal("1000.00"))
        self.assertEqual(campaign.donors_count, 1)

    def test_mark_gift_paid_raises_on_already_paid(self):
        gift = create_gift_checkout(school_id=self.sid, amount=Decimal("75.00"))
        mark_gift_paid(gift_id=gift.id, school_id=self.sid)
        with self.assertRaises(ValueError):
            mark_gift_paid(gift_id=gift.id, school_id=self.sid)

    def test_gift_tenant_isolation(self):
        sid_a = _sid(10)
        sid_b = _sid(11)
        _ensure_school(sid_b)
        gift_a = create_gift_checkout(school_id=sid_a, amount=Decimal("50.00"))
        self.assertEqual(Gift.objects.filter(school_id=sid_b).count(), 0)
        self.assertEqual(Gift.objects.filter(school_id=sid_a, id=gift_a.id).count(), 1)


# ---------------------------------------------------------------------------
# Pledge create + cancel
# ---------------------------------------------------------------------------

class PledgeTest(TestCase):

    def setUp(self):
        self.sid = _sid(20)
        _ensure_school(self.sid)

    def test_create_pledge_creates_active_pledge(self):
        pledge = create_pledge(
            school_id=self.sid,
            total_amount=Decimal("1200.00"),
            start_date=date.today(),
            frequency="monthly",
        )
        self.assertEqual(pledge.status, "active")
        self.assertEqual(pledge.frequency, "monthly")
        self.assertEqual(pledge.school_id, self.sid)

    def test_cancel_pledge_transitions_to_cancelled(self):
        pledge = create_pledge(
            school_id=self.sid,
            total_amount=Decimal("600.00"),
            start_date=date.today(),
        )
        cancelled = cancel_pledge(pledge_id=pledge.id, school_id=self.sid)
        self.assertEqual(cancelled.status, "cancelled")

    def test_cancel_pledge_raises_on_already_cancelled(self):
        pledge = create_pledge(
            school_id=self.sid,
            total_amount=Decimal("200.00"),
            start_date=date.today(),
        )
        cancel_pledge(pledge_id=pledge.id, school_id=self.sid)
        with self.assertRaises(ValueError):
            cancel_pledge(pledge_id=pledge.id, school_id=self.sid)

    def test_pledge_tenant_isolation(self):
        sid_b = _sid(21)
        _ensure_school(sid_b)
        create_pledge(school_id=self.sid, total_amount=Decimal("400.00"), start_date=date.today())
        self.assertEqual(Pledge.objects.filter(school_id=sid_b).count(), 0)


# ---------------------------------------------------------------------------
# Sponsorship agreement checkout + mark_paid
# ---------------------------------------------------------------------------

class SponsorshipAgreementTest(TestCase):

    def setUp(self):
        self.sid = _sid(30)
        _ensure_school(self.sid)
        self.package = _make_package(self.sid, price="2500")

    def test_create_sponsorship_checkout_creates_pending_agreement(self):
        agreement = create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        self.assertEqual(agreement.status, "pending")
        self.assertEqual(agreement.amount, Decimal("2500"))
        self.assertEqual(agreement.package_id, self.package.id)

    def test_create_sponsorship_checkout_stores_provider_id(self):
        agreement = create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        self.assertTrue(agreement.provider_payment_id.startswith("fake_"))

    def test_mark_sponsorship_paid_transitions_to_active(self):
        agreement = create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        active = mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
        self.assertEqual(active.status, "active")

    def test_mark_sponsorship_paid_creates_advancement_transaction(self):
        agreement = create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
        txn = AdvancementTransaction.objects.filter(
            school_id=self.sid, category="sponsorship"
        ).last()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, Decimal("2500"))

    def test_mark_sponsorship_paid_raises_when_not_pending(self):
        agreement = create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)
        with self.assertRaises(ValueError):
            mark_sponsorship_paid(agreement_id=agreement.id, school_id=self.sid)

    def test_agreement_tenant_isolation(self):
        sid_b = _sid(31)
        _ensure_school(sid_b)
        create_sponsorship_checkout(
            school_id=self.sid,
            package_id=self.package.id,
            start_date=date.today(),
        )
        self.assertEqual(SponsorshipAgreement.objects.filter(school_id=sid_b).count(), 0)


# ---------------------------------------------------------------------------
# QR check-in
# ---------------------------------------------------------------------------

class QRCheckInTest(TestCase):

    def setUp(self):
        self.sid = _sid(40)
        _ensure_school(self.sid)
        self.event = _make_event(self.sid)

    def test_valid_qr_accepted(self):
        ticket = _make_ticket(self.event, self.sid, qr="QR_VALID_001")
        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_VALID_001")
        self.assertEqual(scan.result, "accepted")
        self.assertEqual(scan.ticket_id, ticket.id)
        ticket.refresh_from_db()
        self.assertTrue(ticket.checked_in)
        self.assertIsNotNone(ticket.checked_in_at)

    def test_duplicate_qr_returns_duplicate_result(self):
        _make_ticket(self.event, self.sid, qr="QR_DUP_001", checked_in=True)
        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DUP_001")
        self.assertEqual(scan.result, "duplicate")

    def test_invalid_qr_returns_invalid_result_with_null_ticket(self):
        scan = check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DOES_NOT_EXIST")
        self.assertEqual(scan.result, "invalid")
        self.assertIsNone(scan.ticket)
        self.assertEqual(scan.qr_attempted, "QR_DOES_NOT_EXIST")

    def test_all_scan_types_create_audit_records(self):
        _make_ticket(self.event, self.sid, qr="QR_OK_002")
        _make_ticket(self.event, self.sid, qr="QR_DUP_002", checked_in=True)
        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_OK_002")
        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_DUP_002")
        check_in_ticket_by_qr(school_id=self.sid, qr_code="QR_MISSING")
        scans = TicketScan.objects.filter(school_id=self.sid)
        results = set(scans.values_list("result", flat=True))
        self.assertIn("accepted", results)
        self.assertIn("duplicate", results)
        self.assertIn("invalid", results)

    def test_qr_check_in_wrong_school_does_not_find_ticket(self):
        """Tickets from a different school are invisible to QR check-in."""
        other_sid = _sid(41)
        _ensure_school(other_sid)
        _make_ticket(self.event, self.sid, qr="QR_CROSS_001")
        # Check-in request from a different school → must get "invalid"
        scan = check_in_ticket_by_qr(school_id=other_sid, qr_code="QR_CROSS_001")
        self.assertEqual(scan.result, "invalid")
