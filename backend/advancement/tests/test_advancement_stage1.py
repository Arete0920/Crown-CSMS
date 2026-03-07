"""
Advancement Platform — Stage 1 Tests

Coverage:
  1. Tenant isolation — data from school A not visible to school B
  2. Ticket purchase creates Ticket + AdvancementTransaction
  3. Ticket QR uniqueness enforced at model level
  4. Ticket purchase fails when sold out
  5. Store purchase decrements inventory
  6. Store purchase raises ValueError on insufficient inventory
  7. Store purchase raises ValueError on inactive item
  8. Sponsorship sale creates AdvancementTransaction (category=sponsorship)
  9. Donation recording updates Donor.lifetime_giving
 10. Donation recording updates Campaign.raised
"""
import uuid
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone

from core.models import School
from advancement.models import (
    Donor, Campaign, Event, Ticket, StoreItem,
    SponsorshipPackage, AdvancementTransaction,
)
from advancement.services import (
    create_ticket_purchase,
    create_store_purchase,
    record_donation,
    create_sponsorship_sale,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sid(n: int = 1) -> uuid.UUID:
    """Stable UUID per integer for repeatable test isolation."""
    return uuid.UUID(f"00000000-0000-0000-0000-{n:012d}")


def _ensure_school(sid: uuid.UUID) -> School:
    school, _ = School.objects.get_or_create(id=sid, defaults={"name": f"Test School {sid}"})
    return school


def _make_event(school_id, *, ticket_price="25.00", capacity=10, active=True) -> Event:
    return Event.objects.create(
        school_id=school_id,
        name="Annual Gala",
        date=timezone.now() + timezone.timedelta(days=30),
        ticket_price=Decimal(ticket_price),
        capacity=capacity,
        active=active,
    )


def _make_donor(school_id, name="Jane Smith") -> Donor:
    return Donor.objects.create(school_id=school_id, name=name, email="jane@example.com")


def _make_campaign(school_id, goal="10000") -> Campaign:
    return Campaign.objects.create(school_id=school_id, name="Capital Campaign", goal=Decimal(goal))


def _make_store_item(school_id, *, price="20.00", inventory=5, active=True) -> StoreItem:
    return StoreItem.objects.create(
        school_id=school_id,
        name="Spirit Hoodie",
        price=Decimal(price),
        inventory=inventory,
        active=active,
    )


def _make_package(school_id, *, price="500.00") -> SponsorshipPackage:
    return SponsorshipPackage.objects.create(
        school_id=school_id,
        name="Gold Sponsor",
        price=Decimal(price),
    )


# ---------------------------------------------------------------------------
# Test: Tenant isolation
# ---------------------------------------------------------------------------

class TenantIsolationTests(TestCase):

    def setUp(self):
        self.sid_a = _sid(1)
        self.sid_b = _sid(2)
        _ensure_school(self.sid_a)
        _ensure_school(self.sid_b)

        Donor.objects.create(school_id=self.sid_a, name="School A Donor", email="a@a.com")
        Donor.objects.create(school_id=self.sid_b, name="School B Donor", email="b@b.com")

        Event.objects.create(school_id=self.sid_a, name="A Gala", date=timezone.now(), ticket_price=10, capacity=100)
        Event.objects.create(school_id=self.sid_b, name="B Gala", date=timezone.now(), ticket_price=10, capacity=100)

    def test_donor_queryset_scoped_by_school(self):
        donors_a = Donor.objects.filter(school_id=self.sid_a)
        self.assertEqual(donors_a.count(), 1)
        self.assertEqual(donors_a.first().name, "School A Donor")

    def test_event_queryset_scoped_by_school(self):
        events_b = Event.objects.filter(school_id=self.sid_b)
        self.assertEqual(events_b.count(), 1)
        self.assertEqual(events_b.first().name, "B Gala")

    def test_cross_school_donor_invisible(self):
        """School B donors must not appear when filtering for school A."""
        donors = Donor.objects.filter(school_id=self.sid_a)
        names = list(donors.values_list("name", flat=True))
        self.assertNotIn("School B Donor", names)


# ---------------------------------------------------------------------------
# Test: Ticket purchase
# ---------------------------------------------------------------------------

class TicketPurchaseTests(TestCase):

    def setUp(self):
        self.sid = _sid(10)
        _ensure_school(self.sid)

    def test_ticket_purchase_creates_ticket(self):
        event = _make_event(self.sid)
        ticket = create_ticket_purchase(
            school_id=self.sid,
            event=event,
            purchaser_name="Bob Jones",
            purchaser_email="bob@example.com",
        )
        self.assertIsInstance(ticket, Ticket)
        self.assertEqual(ticket.school_id, self.sid)
        self.assertEqual(ticket.purchaser_name, "Bob Jones")

    def test_ticket_purchase_creates_advancement_transaction(self):
        event = _make_event(self.sid, ticket_price="30.00")
        create_ticket_purchase(
            school_id=self.sid,
            event=event,
            purchaser_name="Alice",
            purchaser_email="alice@example.com",
        )
        txn = AdvancementTransaction.objects.get(school_id=self.sid, category="event_ticket")
        self.assertEqual(txn.amount, Decimal("30.00"))

    def test_ticket_qr_code_is_unique(self):
        event = _make_event(self.sid, capacity=0)  # unlimited (capacity=0 means no cap check)
        t1 = create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P1", purchaser_email="p1@x.com")
        t2 = create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P2", purchaser_email="p2@x.com")
        self.assertNotEqual(t1.qr_code, t2.qr_code)

    def test_ticket_purchase_increments_tickets_sold(self):
        event = _make_event(self.sid, capacity=50)
        self.assertEqual(event.tickets_sold, 0)
        create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="P", purchaser_email="p@x.com")
        event.refresh_from_db()
        self.assertEqual(event.tickets_sold, 1)

    def test_ticket_purchase_fails_when_sold_out(self):
        event = _make_event(self.sid, capacity=1)
        create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="First", purchaser_email="f@x.com")
        event.refresh_from_db()
        with self.assertRaises(ValueError, msg="Should raise ValueError when sold out"):
            create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="Second", purchaser_email="s@x.com")

    def test_ticket_purchase_fails_for_inactive_event(self):
        event = _make_event(self.sid, active=False)
        with self.assertRaises(ValueError):
            create_ticket_purchase(school_id=self.sid, event=event, purchaser_name="X", purchaser_email="x@x.com")


# ---------------------------------------------------------------------------
# Test: Store purchase
# ---------------------------------------------------------------------------

class StorePurchaseTests(TestCase):

    def setUp(self):
        self.sid = _sid(20)
        _ensure_school(self.sid)

    def test_store_purchase_decrements_inventory(self):
        item = _make_store_item(self.sid, inventory=10)
        create_store_purchase(school_id=self.sid, item=item, quantity=3)
        item.refresh_from_db()
        self.assertEqual(item.inventory, 7)

    def test_store_purchase_creates_advancement_transaction(self):
        item = _make_store_item(self.sid, price="40.00", inventory=5)
        create_store_purchase(school_id=self.sid, item=item, quantity=2)
        txn = AdvancementTransaction.objects.get(school_id=self.sid, category="store_purchase")
        self.assertEqual(txn.amount, Decimal("80.00"))  # 40 * 2

    def test_store_purchase_insufficient_inventory_raises(self):
        item = _make_store_item(self.sid, inventory=2)
        with self.assertRaises(ValueError, msg="Should raise ValueError on insufficient stock"):
            create_store_purchase(school_id=self.sid, item=item, quantity=5)

    def test_store_purchase_inactive_item_raises(self):
        item = _make_store_item(self.sid, active=False)
        with self.assertRaises(ValueError):
            create_store_purchase(school_id=self.sid, item=item)

    def test_store_purchase_inventory_not_decremented_on_error(self):
        """Inventory stays at original value when purchase fails."""
        item = _make_store_item(self.sid, inventory=1)
        try:
            create_store_purchase(school_id=self.sid, item=item, quantity=999)
        except ValueError:
            pass
        item.refresh_from_db()
        self.assertEqual(item.inventory, 1)


# ---------------------------------------------------------------------------
# Test: Sponsorship sale
# ---------------------------------------------------------------------------

class SponsorshipSaleTests(TestCase):

    def setUp(self):
        self.sid = _sid(30)
        _ensure_school(self.sid)

    def test_sponsorship_sale_creates_transaction(self):
        package = _make_package(self.sid, price="750.00")
        txn = create_sponsorship_sale(school_id=self.sid, package=package)
        self.assertEqual(txn.category, "sponsorship")
        self.assertEqual(txn.amount, Decimal("750.00"))
        self.assertEqual(txn.school_id, self.sid)

    def test_sponsorship_transaction_links_to_campaign(self):
        package = _make_package(self.sid, price="500.00")
        campaign = _make_campaign(self.sid)
        txn = create_sponsorship_sale(school_id=self.sid, package=package, campaign=campaign)
        self.assertEqual(txn.campaign_id, campaign.id)


# ---------------------------------------------------------------------------
# Test: Donation recording
# ---------------------------------------------------------------------------

class DonationTests(TestCase):

    def setUp(self):
        self.sid = _sid(40)
        _ensure_school(self.sid)

    def test_donation_creates_transaction(self):
        donor = _make_donor(self.sid)
        txn = record_donation(school_id=self.sid, donor=donor, amount="250.00")
        self.assertEqual(txn.category, "donation")
        self.assertEqual(txn.amount, Decimal("250.00"))

    def test_donation_updates_lifetime_giving(self):
        donor = _make_donor(self.sid)
        initial = donor.lifetime_giving
        record_donation(school_id=self.sid, donor=donor, amount="500.00")
        donor.refresh_from_db()
        self.assertEqual(donor.lifetime_giving, initial + Decimal("500.00"))

    def test_donation_updates_campaign_raised(self):
        donor = _make_donor(self.sid)
        campaign = _make_campaign(self.sid, goal="10000")
        initial_raised = campaign.raised
        record_donation(school_id=self.sid, donor=donor, amount="1000.00", campaign=campaign)
        campaign.refresh_from_db()
        self.assertEqual(campaign.raised, initial_raised + Decimal("1000.00"))

    def test_donation_negative_amount_raises(self):
        donor = _make_donor(self.sid)
        with self.assertRaises(ValueError):
            record_donation(school_id=self.sid, donor=donor, amount="-100.00")

    def test_donation_zero_amount_raises(self):
        donor = _make_donor(self.sid)
        with self.assertRaises(ValueError):
            record_donation(school_id=self.sid, donor=donor, amount="0")
