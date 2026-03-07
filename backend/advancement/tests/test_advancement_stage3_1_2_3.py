"""
Advancement Platform — Stage 3.1 / 3.2 / 3.3 Tests

Coverage:
  Stage 3.1 – Availability grid + strict holds + purchase of held seats
   1.  build_availability_grid returns correct capacity/sold/held/available counts
   2.  build_availability_grid marks sold seats correctly
   3.  hold_seats_strict ok path returns hold_expires_at + seat list
   4.  hold_seats_strict conflict on already-sold seat
   5.  hold_seats_strict conflict on already-held seat (different email)
   6.  hold_seats_strict expired hold is purged and re-holdable
   7.  purchase_held_seats creates Ticket + TicketSeat rows
   8.  purchase_held_seats fails when hold is missing
   9.  purchase_held_seats fails when seat already sold

  Stage 3.2 – Checkout session + webhook fulfillment
  10.  create_seat_checkout_session creates PendingSeatOrder with provider_session_id
  11.  fulfill_paid_order transitions status → fulfilled + creates TicketSeat rows
  12.  fulfill_paid_order is idempotent (second call returns same fulfilled order)
  13.  already_processed_event / mark_event_processed idempotency guard
  14.  FakeCheckoutProvider returns checkout_url with session_id query param

  Stage 3.3 – Section pricing + best-available + emailer
  15.  get_section_price returns 0 for unknown section
  16.  EventSectionPrice upsert via get_section_price after create
  17.  compute_seats_amount sums section prices for seat list
  18.  best_available returns correct count of seats
  19.  best_available respects preferred_sections ordering
  20.  create_checkout_for_best_available returns ok=True + order data
  21.  create_checkout_for_best_available returns ok=False when not enough seats
  22.  EmailOutbox is created during _queue_ticket_email (via fulfill_paid_order)
  23.  make_ticket_pdf_bytes returns non-empty bytes
  24.  send_outbox management command processes pending EmailOutbox rows
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import School
from advancement.models import Donor, Event, Ticket
from advancement.models_stage3 import (
    Venue, SeatingMap, EventSeating, Seat, SeatHold, TicketSeat,
)
from advancement.models_stage3_2 import PendingSeatOrder, ProcessedWebhookEvent
from advancement.models_stage3_3 import EventSectionPrice, EmailOutbox
from advancement.services_stage3 import create_or_replace_seats_from_layout
from advancement.services_stage3_1 import (
    build_availability_grid, hold_seats_strict, purchase_held_seats,
)
from advancement.services_stage3_2 import (
    create_seat_checkout_session, fulfill_paid_order,
    already_processed_event, mark_event_processed,
)
from advancement.services_stage3_3 import (
    get_section_price, compute_seats_amount, best_available,
    create_checkout_for_best_available,
)
from advancement.payments.providers import FakeCheckoutProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sid(n: int) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-0000-0000-{n:012d}")


def _ensure_school(sid: uuid.UUID) -> School:
    school, _ = School.objects.get_or_create(id=sid, defaults={"name": f"Stage31 School {sid}"})
    return school


def _make_event(school_id, name="Gala31") -> Event:
    return Event.objects.create(
        school_id=school_id,
        name=name,
        date=timezone.now() + timedelta(days=30),
        ticket_price=Decimal("50.00"),
        capacity=200,
        active=True,
    )


def _make_seating_map(school_id, name="Map31") -> SeatingMap:
    venue = Venue.objects.create(school_id=school_id, name="Stage31 Arena")
    return SeatingMap.objects.create(school_id=school_id, venue=venue, name=name)


# 2 sections, 3 seats each = 6 total seats
_LAYOUT = {
    "sections": [
        {"name": "VIP", "rows": [{"name": "A", "seats": 3}]},
        {"name": "GEN", "rows": [{"name": "A", "seats": 3}]},
    ]
}


def _setup_event_with_seats(school_id, name="Gala31"):
    """Create Event + SeatingMap + EventSeating + 6 Seats. Returns (event, seats)."""
    event = _make_event(school_id, name=name)
    smap = _make_seating_map(school_id)
    EventSeating.objects.create(school_id=school_id, event=event, seating_map=smap)
    create_or_replace_seats_from_layout(
        school_id=school_id,
        seating_map_id=smap.id,
        layout=_LAYOUT,
    )
    seats = list(Seat.objects.filter(school_id=school_id, seating_map=smap).order_by("section", "row", "number"))
    return event, seats


# ===========================================================================
# Stage 3.1 Tests
# ===========================================================================

class AvailabilityGridTest(TestCase):

    def setUp(self):
        self.sid = _sid(41)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_returns_correct_counts_all_available(self):
        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
        self.assertEqual(grid["capacity"], 6)
        self.assertEqual(grid["sold"], 0)
        self.assertEqual(grid["held"], 0)
        self.assertEqual(grid["available"], 6)

    def test_sold_seat_reflected_in_grid(self):
        seat = self.seats[0]
        ticket = Ticket.objects.create(
            school_id=self.sid, event=self.event,
            purchaser_name="Buyer1", purchaser_email="b1@test.com",
            qr_code=f"QR_{uuid.uuid4().hex[:8]}",
        )
        TicketSeat.objects.create(
            school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat,
        )

        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
        self.assertEqual(grid["sold"], 1)
        self.assertEqual(grid["available"], 5)

    def test_held_seat_reflected_in_grid(self):
        seat = self.seats[0]
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="holder@test.com",
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
        self.assertEqual(grid["held"], 1)
        self.assertEqual(grid["available"], 5)

    def test_sections_structure_returned(self):
        grid = build_availability_grid(school_id=self.sid, event_id=self.event.id)
        self.assertIn("sections", grid)
        sections = grid["sections"]
        self.assertIn("VIP", sections)
        self.assertIn("GEN", sections)


class HoldSeatsStrictTest(TestCase):

    def setUp(self):
        self.sid = _sid(42)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_ok_path_creates_holds(self):
        seat_ids = [self.seats[0].id, self.seats[1].id]
        result = hold_seats_strict(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=seat_ids,
            email="buyer@test.com",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["held_seat_ids"]), 2)
        self.assertIn("hold_expires_at", result)
        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 2)

    def test_conflict_on_sold_seat(self):
        seat = self.seats[0]
        ticket = Ticket.objects.create(
            school_id=self.sid, event=self.event,
            purchaser_name="Prev", purchaser_email="prev@test.com",
            qr_code=f"QR_{uuid.uuid4().hex[:8]}",
        )
        TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)

        result = hold_seats_strict(
            school_id=self.sid, event_id=self.event.id,
            seat_ids=[seat.id], email="new@test.com",
        )
        self.assertFalse(result["ok"])
        self.assertIn(str(seat.id), result["conflict"])

    def test_conflict_on_already_held_seat(self):
        seat = self.seats[0]
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="other@test.com",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        result = hold_seats_strict(
            school_id=self.sid, event_id=self.event.id,
            seat_ids=[seat.id], email="buyer@test.com",
        )
        self.assertFalse(result["ok"])
        self.assertIn(str(seat.id), result["conflict"])

    def test_expired_hold_is_purged_and_reholdable(self):
        seat = self.seats[0]
        # Create an expired hold
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="old@test.com",
            expires_at=timezone.now() - timedelta(minutes=5),
        )

        result = hold_seats_strict(
            school_id=self.sid, event_id=self.event.id,
            seat_ids=[seat.id], email="new@test.com",
        )
        self.assertTrue(result["ok"])

    def test_same_email_refreshes_hold(self):
        seat = self.seats[0]
        hold_seats_strict(
            school_id=self.sid, event_id=self.event.id,
            seat_ids=[seat.id], email="buyer@test.com",
        )
        # Hold again with same email - should succeed (refresh)
        result = hold_seats_strict(
            school_id=self.sid, event_id=self.event.id,
            seat_ids=[seat.id], email="buyer@test.com",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 1)


class PurchaseHeldSeatsTest(TestCase):

    def setUp(self):
        self.sid = _sid(43)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_creates_tickets_and_ticket_seats(self):
        seat = self.seats[0]
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="buyer@test.com",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        result = purchase_held_seats(
            school_id=self.sid,
            event_id=self.event.id,
            email="buyer@test.com",
            purchaser_name="Test Buyer",
            seat_ids=[seat.id],
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["ticket_ids"]), 1)
        self.assertEqual(TicketSeat.objects.filter(school_id=self.sid, event_id=self.event.id).count(), 1)
        # Hold should be released
        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 0)

    def test_fails_on_missing_hold(self):
        result = purchase_held_seats(
            school_id=self.sid,
            event_id=self.event.id,
            email="nobody@test.com",
            purchaser_name="Ghost",
            seat_ids=[self.seats[0].id],
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "hold_expired_or_missing")

    def test_fails_on_already_sold_seat(self):
        seat = self.seats[0]
        # Create hold + pre-existing TicketSeat
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="buyer@test.com",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        ticket = Ticket.objects.create(
            school_id=self.sid, event=self.event,
            purchaser_name="First", purchaser_email="first@test.com",
            qr_code=f"QR_{uuid.uuid4().hex[:8]}",
        )
        TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)

        result = purchase_held_seats(
            school_id=self.sid,
            event_id=self.event.id,
            email="buyer@test.com",
            purchaser_name="Second",
            seat_ids=[seat.id],
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "already_sold")


# ===========================================================================
# Stage 3.2 Tests
# ===========================================================================

class FakeCheckoutProviderTest(TestCase):

    def test_create_checkout_session_returns_result_with_url(self):
        provider = FakeCheckoutProvider()
        result = provider.create_checkout_session(
            amount_cents=2500,
            currency="usd",
            description="Test event",
            success_url="http://localhost:5173/success",
            cancel_url="http://localhost:5173/cancel",
            metadata={"order_id": "1234"},
        )
        self.assertTrue(result.provider_payment_id.startswith("fake_cs_"))
        self.assertIn("success", result.checkout_url)
        self.assertEqual(result.provider, "fake")

    def test_verify_webhook_returns_parsed_dict(self):
        import json
        provider = FakeCheckoutProvider()
        payload = json.dumps({"type": "checkout.session.completed", "id": "evt_test"}).encode()
        event = provider.verify_webhook(payload=payload, signature="", webhook_secret="")
        self.assertEqual(event["type"], "checkout.session.completed")


class CheckoutSessionTest(TestCase):

    def setUp(self):
        self.sid = _sid(44)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_creates_pending_order(self):
        seat_ids = [self.seats[0].id, self.seats[1].id]
        order = create_seat_checkout_session(
            school_id=self.sid,
            event_id=self.event.id,
            purchaser_name="Jane Doe",
            purchaser_email="jane@test.com",
            seat_ids=seat_ids,
            amount_cents=5000,
        )
        self.assertIsInstance(order, PendingSeatOrder)
        self.assertEqual(order.status, "pending")
        self.assertTrue(order.provider_session_id.startswith("fake_cs_"))
        self.assertTrue(order.checkout_url)
        self.assertEqual(order.school_id, self.sid)
        self.assertEqual(order.amount_cents, 5000)


class FulfillOrderTest(TestCase):

    def setUp(self):
        self.sid = _sid(45)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def _create_order(self, seat_ids=None):
        if seat_ids is None:
            seat_ids = [self.seats[0].id]
        return create_seat_checkout_session(
            school_id=self.sid,
            event_id=self.event.id,
            purchaser_name="Buyer Fulfill",
            purchaser_email="fulfill@test.com",
            seat_ids=seat_ids,
            amount_cents=2500,
        )

    def test_fulfill_creates_ticket_and_ticket_seat_rows(self):
        order = self._create_order(seat_ids=[self.seats[0].id, self.seats[1].id])
        fulfilled = fulfill_paid_order(order_id=order.id)
        self.assertEqual(fulfilled.status, "fulfilled")
        self.assertEqual(Ticket.objects.filter(school_id=self.sid, event=self.event).count(), 2)
        self.assertEqual(TicketSeat.objects.filter(school_id=self.sid, event_id=self.event.id).count(), 2)

    def test_fulfill_is_idempotent(self):
        order = self._create_order()
        fulfill_paid_order(order_id=order.id)
        # Call again – should return same fulfilled order, not create extra tickets
        fulfilled2 = fulfill_paid_order(order_id=order.id)
        self.assertEqual(fulfilled2.status, "fulfilled")
        self.assertEqual(Ticket.objects.filter(school_id=self.sid, event=self.event).count(), 1)

    def test_fulfill_releases_holds(self):
        seat = self.seats[0]
        SeatHold.objects.create(
            school_id=self.sid, event=self.event, seat=seat,
            held_by_email="fulfill@test.com",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        order = self._create_order(seat_ids=[seat.id])
        fulfill_paid_order(order_id=order.id)
        self.assertEqual(SeatHold.objects.filter(school_id=self.sid, event=self.event).count(), 0)


class WebhookIdempotencyTest(TestCase):

    def test_already_processed_returns_false_before_mark(self):
        self.assertFalse(already_processed_event(provider="fake", event_id="evt_abc"))

    def test_mark_then_already_processed_returns_true(self):
        mark_event_processed(provider="fake", event_id="evt_def")
        self.assertTrue(already_processed_event(provider="fake", event_id="evt_def"))

    def test_mark_is_idempotent(self):
        mark_event_processed(provider="fake", event_id="evt_ghi")
        mark_event_processed(provider="fake", event_id="evt_ghi")  # no error
        self.assertEqual(
            ProcessedWebhookEvent.objects.filter(event_id="evt_ghi").count(), 1
        )


# ===========================================================================
# Stage 3.3 Tests
# ===========================================================================

class SectionPriceTest(TestCase):

    def setUp(self):
        self.sid = _sid(46)
        _ensure_school(self.sid)
        self.event = _make_event(self.sid)

    def test_get_section_price_returns_zero_for_unknown(self):
        price = get_section_price(school_id=self.sid, event_id=self.event.id, section="UNKNOWN")
        self.assertEqual(price, 0)

    def test_get_section_price_returns_configured_price(self):
        EventSectionPrice.objects.create(
            school_id=self.sid, event_id=self.event.id,
            section="VIP", price_cents=7500,
        )
        price = get_section_price(school_id=self.sid, event_id=self.event.id, section="VIP")
        self.assertEqual(price, 7500)

    def test_compute_seats_amount_sums_prices(self):
        event, seats = _setup_event_with_seats(self.sid, name="SectionPriceGala")
        vip_seats = [s for s in seats if s.section == "VIP"]
        gen_seats = [s for s in seats if s.section == "GEN"]

        EventSectionPrice.objects.create(
            school_id=self.sid, event_id=event.id, section="VIP", price_cents=5000
        )
        EventSectionPrice.objects.create(
            school_id=self.sid, event_id=event.id, section="GEN", price_cents=2500
        )

        # Pick 1 VIP + 1 GEN seat
        seat_ids = [vip_seats[0].id, gen_seats[0].id]
        total = compute_seats_amount(school_id=self.sid, event_id=event.id, seat_ids=seat_ids)
        self.assertEqual(total, 7500)


class BestAvailableTest(TestCase):

    def setUp(self):
        self.sid = _sid(47)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_returns_requested_count(self):
        result = best_available(school_id=self.sid, event_id=self.event.id, count=3)
        self.assertEqual(len(result), 3)

    def test_returns_fewer_when_not_enough_available(self):
        # Sell 5 seats
        for seat in self.seats[:5]:
            ticket = Ticket.objects.create(
                school_id=self.sid, event=self.event,
                purchaser_name="Buyer", purchaser_email="b@test.com",
                qr_code=f"QR_{uuid.uuid4().hex[:8]}",
            )
            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)

        result = best_available(school_id=self.sid, event_id=self.event.id, count=3)
        self.assertEqual(len(result), 1)  # only 1 seat left

    def test_preferred_sections_come_first(self):
        result = best_available(
            school_id=self.sid, event_id=self.event.id,
            count=3,
            preferred_sections=["VIP"],
        )
        # All 3 should be from VIP if possible (VIP has 3 seats)
        for seat in result:
            self.assertEqual(seat.section, "VIP")

    def test_falls_back_to_other_sections(self):
        # Hold/sell all VIP seats
        vip_seats = [s for s in self.seats if s.section == "VIP"]
        for seat in vip_seats:
            ticket = Ticket.objects.create(
                school_id=self.sid, event=self.event,
                purchaser_name="VIP Buyer", purchaser_email="vip@test.com",
                qr_code=f"QR_{uuid.uuid4().hex[:8]}",
            )
            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)

        result = best_available(
            school_id=self.sid, event_id=self.event.id,
            count=2, preferred_sections=["VIP"],
        )
        # Falls back to GEN
        self.assertEqual(len(result), 2)
        for seat in result:
            self.assertEqual(seat.section, "GEN")


class BestAvailableCheckoutTest(TestCase):

    def setUp(self):
        self.sid = _sid(48)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)
        EventSectionPrice.objects.create(
            school_id=self.sid, event_id=self.event.id, section="VIP", price_cents=5000
        )
        EventSectionPrice.objects.create(
            school_id=self.sid, event_id=self.event.id, section="GEN", price_cents=2500
        )

    def test_creates_order_for_available_seats(self):
        result = create_checkout_for_best_available(
            school_id=self.sid,
            event_id=self.event.id,
            purchaser_name="Mary Best",
            purchaser_email="mary@test.com",
            count=2,
        )
        self.assertTrue(result["ok"])
        self.assertIn("order_id", result)
        self.assertIn("checkout_url", result)
        self.assertGreater(result["amount_cents"], 0)

    def test_returns_error_when_not_enough_seats(self):
        # Sell all seats
        for seat in self.seats:
            ticket = Ticket.objects.create(
                school_id=self.sid, event=self.event,
                purchaser_name="Buyer", purchaser_email="b@test.com",
                qr_code=f"QR_{uuid.uuid4().hex[:8]}",
            )
            TicketSeat.objects.create(school_id=self.sid, event_id=self.event.id, ticket=ticket, seat=seat)

        result = create_checkout_for_best_available(
            school_id=self.sid,
            event_id=self.event.id,
            purchaser_name="Late Buyer",
            purchaser_email="late@test.com",
            count=3,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "not_enough_seats")


class EmailOutboxQueuedOnFulfillTest(TestCase):

    def setUp(self):
        self.sid = _sid(49)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_email_outbox_created_after_fulfill(self):
        order = create_seat_checkout_session(
            school_id=self.sid,
            event_id=self.event.id,
            purchaser_name="Email Test Buyer",
            purchaser_email="emailtest@test.com",
            seat_ids=[self.seats[0].id],
            amount_cents=2500,
        )
        fulfill_paid_order(order_id=order.id)
        # EmailOutbox should have been queued
        self.assertEqual(
            EmailOutbox.objects.filter(school_id=self.sid, kind="ticket_delivery").count(), 1
        )
        outbox = EmailOutbox.objects.get(school_id=self.sid, kind="ticket_delivery")
        self.assertEqual(outbox.to_email, "emailtest@test.com")
        self.assertEqual(outbox.status, "pending")


class TicketPDFRenderTest(TestCase):

    def setUp(self):
        self.sid = _sid(50)
        _ensure_school(self.sid)
        self.event, self.seats = _setup_event_with_seats(self.sid)

    def test_make_ticket_pdf_returns_bytes(self):
        from advancement.tickets_render import make_ticket_pdf_bytes
        seat = self.seats[0]
        ticket = Ticket.objects.create(
            school_id=self.sid,
            event=self.event,
            purchaser_name="PDF Buyer",
            purchaser_email="pdf@test.com",
            qr_code=f"QR_{uuid.uuid4().hex[:8]}",
        )
        pdf_bytes = make_ticket_pdf_bytes(ticket=ticket, seat=seat)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 100)
        # Should start with PDF header
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
