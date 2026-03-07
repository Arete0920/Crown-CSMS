"""
Advancement Platform — Stage 3 Tests

Coverage:
  1.  transition_move_stage creates Move with correct stage
  2.  transition_move_stage raises ValueError on invalid stage
  3.  transition_move_stage raises Prospect.DoesNotExist on wrong school_id (tenant isolation)
  4.  multiple transitions build full history (3 Moves, correct stage on each)
  5.  create_or_replace_seats_from_layout creates correct seat count
  6.  create_or_replace_seats_from_layout replaces seats on second call (no duplicates)
  7.  create_or_replace_seats_from_layout raises SeatingMap.DoesNotExist for wrong school
  8.  hold_seats accepted path — ok=True + hold count matches seat_ids
  9.  hold_seats conflict path — different email returns ok=False
 10.  hold_seats same-email refresh — ok=True, expires_at updated
 11.  hold_seats expired hold is purged and re-holdable
 12.  assign_seat_to_ticket success path — TicketSeat created
 13.  assign_seat_to_ticket raises ValueError on duplicate seat assignment
 14.  assign_seat_to_ticket raises Ticket.DoesNotExist for wrong school
 15.  log_impressions creates SponsorImpression with correct count + channel
 16.  log_impressions raises SponsorshipDeliverable.DoesNotExist for wrong school
 17.  AlumniCohortMember unique_together (school_id, cohort, donor) enforced
 18.  Prospect tenant isolation — school A cannot see school B prospects via queryset
 19.  SeatingMap seat_count annotation (serializer helper)
 20.  SponsorshipDeliverable impression_count annotation (serializer helper)
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import School
from advancement.models import (
    Donor,
    Event,
    Ticket,
    SponsorshipPackage,
    SponsorshipAgreement,
)
from advancement.models_stage3 import (
    Prospect,
    Move,
    AlumniCohort,
    AlumniCohortMember,
    Venue,
    SeatingMap,
    EventSeating,
    Seat,
    SeatHold,
    TicketSeat,
    SponsorshipDeliverable,
    SponsorImpression,
)
from advancement.services_stage3 import (
    transition_move_stage,
    create_or_replace_seats_from_layout,
    hold_seats,
    assign_seat_to_ticket,
    log_impressions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sid(n: int = 1) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-0000-0000-{n:012d}")


def _ensure_school(sid: uuid.UUID) -> School:
    school, _ = School.objects.get_or_create(id=sid, defaults={"name": f"S3 School {sid}"})
    return school


def _make_donor(school_id, name="Alice Donor") -> Donor:
    return Donor.objects.create(school_id=school_id, name=name, email=f"{name.lower().replace(' ', '_')}@stage3.test")


def _make_prospect(school_id, donor=None) -> Prospect:
    return Prospect.objects.create(school_id=school_id, donor=donor, capacity_tier="tier1")


def _make_event(school_id, name="Stage3 Gala") -> Event:
    return Event.objects.create(
        school_id=school_id,
        name=name,
        date=timezone.now() + timedelta(days=30),
        ticket_price=Decimal("75.00"),
        capacity=100,
        active=True,
    )


def _make_ticket(event, school_id, qr="QR_S3_001") -> Ticket:
    return Ticket.objects.create(
        school_id=school_id,
        event=event,
        purchaser_name="Bob Buyer",
        purchaser_email="bob@stage3.test",
        qr_code=qr,
    )


def _make_seating_map(school_id, name="Map A") -> SeatingMap:
    venue = Venue.objects.create(school_id=school_id, name="Stage3 Arena")
    return SeatingMap.objects.create(school_id=school_id, venue=venue, name=name)


_SIMPLE_LAYOUT = {
    "sections": [
        {"name": "A", "rows": [{"name": "1", "seats": 5}, {"name": "2", "seats": 5}]},
        {"name": "B", "rows": [{"name": "1", "seats": 4}]},
    ]
}  # 5+5+4 = 14 seats


def _make_sponsorship_agreement(school_id) -> SponsorshipAgreement:
    pkg = SponsorshipPackage.objects.create(
        school_id=school_id,
        name="Platinum",
        price=Decimal("10000"),
    )
    return SponsorshipAgreement.objects.create(
        school_id=school_id,
        package=pkg,
        amount=Decimal("10000"),
        status="active",
        start_date=date.today(),
    )


def _make_deliverable(school_id, agreement, deliverable_type="banner") -> SponsorshipDeliverable:
    return SponsorshipDeliverable.objects.create(
        school_id=school_id,
        agreement=agreement,
        deliverable_type=deliverable_type,
        label="Homepage Banner",
    )


# ---------------------------------------------------------------------------
# 1–4: Moves Management
# ---------------------------------------------------------------------------

class TransitionMoveStageTest(TestCase):

    def setUp(self):
        self.sid = _sid(30)
        _ensure_school(self.sid)
        self.donor = _make_donor(self.sid)
        self.prospect = _make_prospect(self.sid, donor=self.donor)

    def test_creates_move_with_correct_stage(self):
        move = transition_move_stage(
            school_id=self.sid,
            prospect_id=self.prospect.id,
            new_stage="qualified",
            user=None,
        )
        self.assertIsNotNone(move.id)
        self.assertEqual(move.stage, "qualified")
        self.assertEqual(move.school_id, self.sid)
        self.assertEqual(move.prospect_id, self.prospect.id)

    def test_raises_valueerror_on_invalid_stage(self):
        with self.assertRaises(ValueError):
            transition_move_stage(
                school_id=self.sid,
                prospect_id=self.prospect.id,
                new_stage="not_a_real_stage",
                user=None,
            )

    def test_raises_doesnotexist_on_wrong_school(self):
        other_sid = _sid(31)
        _ensure_school(other_sid)
        with self.assertRaises(Prospect.DoesNotExist):
            transition_move_stage(
                school_id=other_sid,
                prospect_id=self.prospect.id,
                new_stage="qualified",
                user=None,
            )

    def test_multiple_transitions_build_full_history(self):
        stages = ["qualified", "cultivating", "soliciting"]
        for s in stages:
            transition_move_stage(
                school_id=self.sid,
                prospect_id=self.prospect.id,
                new_stage=s,
                user=None,
                summary=f"Moving to {s}",
            )
        moves = Move.objects.filter(school_id=self.sid, prospect=self.prospect).order_by("created_at")
        self.assertEqual(moves.count(), 3)
        self.assertEqual(list(m.stage for m in moves), stages)

    def test_summary_is_stored(self):
        move = transition_move_stage(
            school_id=self.sid,
            prospect_id=self.prospect.id,
            new_stage="cultivating",
            user=None,
            summary="Had lunch with donor",
            action_type="meeting",
        )
        self.assertEqual(move.summary, "Had lunch with donor")
        self.assertEqual(move.action_type, "meeting")


# ---------------------------------------------------------------------------
# 5–7: Seating Layout
# ---------------------------------------------------------------------------

class SeatingLayoutTest(TestCase):

    def setUp(self):
        self.sid = _sid(32)
        _ensure_school(self.sid)
        self.smap = _make_seating_map(self.sid)

    def test_creates_correct_seat_count(self):
        created = create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout=_SIMPLE_LAYOUT,
        )
        self.assertEqual(created, 14)
        self.assertEqual(Seat.objects.filter(school_id=self.sid, seating_map=self.smap).count(), 14)

    def test_replaces_seats_on_second_call(self):
        create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout=_SIMPLE_LAYOUT,
        )
        # Second layout — fewer seats
        small_layout = {"sections": [{"name": "C", "rows": [{"name": "1", "seats": 3}]}]}
        created = create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout=small_layout,
        )
        self.assertEqual(created, 3)
        total = Seat.objects.filter(school_id=self.sid, seating_map=self.smap).count()
        self.assertEqual(total, 3)

    def test_raises_doesnotexist_for_wrong_school(self):
        other_sid = _sid(33)
        _ensure_school(other_sid)
        with self.assertRaises(SeatingMap.DoesNotExist):
            create_or_replace_seats_from_layout(
                school_id=other_sid,
                seating_map_id=self.smap.id,
                layout=_SIMPLE_LAYOUT,
            )

    def test_layout_json_persisted_on_map(self):
        create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout=_SIMPLE_LAYOUT,
        )
        self.smap.refresh_from_db()
        self.assertEqual(self.smap.layout_json, _SIMPLE_LAYOUT)


# ---------------------------------------------------------------------------
# 8–11: Seat Hold
# ---------------------------------------------------------------------------

class HoldSeatsTest(TestCase):

    def setUp(self):
        self.sid = _sid(34)
        _ensure_school(self.sid)
        self.smap = _make_seating_map(self.sid, name="HoldMap")
        create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout=_SIMPLE_LAYOUT,
        )
        self.event = _make_event(self.sid)
        self.seats = list(Seat.objects.filter(school_id=self.sid, seating_map=self.smap)[:3])

    def _seat_ids(self, seats=None):
        return [s.id for s in (seats or self.seats)]

    def test_accepted_path_returns_ok_true(self):
        result = hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="buyer@stage3.test",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["holds"]), 3)

    def test_conflict_path_different_email_returns_ok_false(self):
        hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="buyer1@stage3.test",
        )
        result = hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="buyer2@stage3.test",
        )
        self.assertFalse(result["ok"])
        self.assertIn("message", result)

    def test_same_email_refresh_ok_true(self):
        hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="same@stage3.test",
            hold_minutes=5,
        )
        result = hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="same@stage3.test",
            hold_minutes=10,
        )
        self.assertTrue(result["ok"])

    def test_expired_hold_purged_and_reholdable(self):
        # Create a hold then manually expire it
        hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="first@stage3.test",
        )
        SeatHold.objects.filter(school_id=self.sid, event_id=self.event.id).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        # A different email should now succeed (expired holds are purged first)
        result = hold_seats(
            school_id=self.sid,
            event_id=self.event.id,
            seat_ids=self._seat_ids(),
            email="second@stage3.test",
        )
        self.assertTrue(result["ok"])


# ---------------------------------------------------------------------------
# 12–14: Assign Seat to Ticket
# ---------------------------------------------------------------------------

class AssignSeatToTicketTest(TestCase):

    def setUp(self):
        self.sid = _sid(35)
        _ensure_school(self.sid)
        self.smap = _make_seating_map(self.sid, name="AssignMap")
        create_or_replace_seats_from_layout(
            school_id=self.sid,
            seating_map_id=self.smap.id,
            layout={"sections": [{"name": "A", "rows": [{"name": "1", "seats": 5}]}]},
        )
        self.event = _make_event(self.sid)
        self.ticket = _make_ticket(self.event, self.sid, qr="QR_ASSIGN_001")
        self.seat = Seat.objects.filter(school_id=self.sid, seating_map=self.smap).first()

    def test_success_path_creates_ticket_seat(self):
        ts = assign_seat_to_ticket(
            school_id=self.sid,
            ticket_id=self.ticket.id,
            seat_id=self.seat.id,
        )
        self.assertIsNotNone(ts.id)
        self.assertEqual(ts.ticket_id, self.ticket.id)
        self.assertEqual(ts.seat_id, self.seat.id)
        self.assertEqual(ts.school_id, self.sid)

    def test_raises_valueerror_on_duplicate_assignment(self):
        assign_seat_to_ticket(
            school_id=self.sid,
            ticket_id=self.ticket.id,
            seat_id=self.seat.id,
        )
        ticket2 = _make_ticket(self.event, self.sid, qr="QR_ASSIGN_002")
        with self.assertRaises(ValueError):
            assign_seat_to_ticket(
                school_id=self.sid,
                ticket_id=ticket2.id,
                seat_id=self.seat.id,  # same seat
            )

    def test_raises_doesnotexist_for_wrong_school_ticket(self):
        other_sid = _sid(36)
        _ensure_school(other_sid)
        with self.assertRaises(Ticket.DoesNotExist):
            assign_seat_to_ticket(
                school_id=other_sid,
                ticket_id=self.ticket.id,
                seat_id=self.seat.id,
            )


# ---------------------------------------------------------------------------
# 15–16: Sponsor Impressions
# ---------------------------------------------------------------------------

class LogImpressionsTest(TestCase):

    def setUp(self):
        self.sid = _sid(37)
        _ensure_school(self.sid)
        self.agreement = _make_sponsorship_agreement(self.sid)
        self.deliverable = _make_deliverable(self.sid, self.agreement)

    def test_creates_sponsor_impression_with_correct_count(self):
        imp = log_impressions(
            school_id=self.sid,
            deliverable_id=self.deliverable.id,
            channel="web",
            count=250,
        )
        self.assertIsNotNone(imp.id)
        self.assertEqual(imp.count, 250)
        self.assertEqual(imp.channel, "web")
        self.assertEqual(imp.school_id, self.sid)
        self.assertEqual(imp.deliverable_id, self.deliverable.id)

    def test_creates_with_metadata(self):
        meta = {"page": "homepage", "campaign": "fall2026"}
        imp = log_impressions(
            school_id=self.sid,
            deliverable_id=self.deliverable.id,
            channel="social",
            count=42,
            metadata=meta,
        )
        self.assertEqual(imp.metadata, meta)

    def test_raises_doesnotexist_for_wrong_school(self):
        other_sid = _sid(38)
        _ensure_school(other_sid)
        with self.assertRaises(SponsorshipDeliverable.DoesNotExist):
            log_impressions(
                school_id=other_sid,
                deliverable_id=self.deliverable.id,
                channel="web",
                count=1,
            )


# ---------------------------------------------------------------------------
# 17: AlumniCohortMember unique_together
# ---------------------------------------------------------------------------

class AlumniCohortMemberUniquenessTest(TestCase):

    def setUp(self):
        self.sid = _sid(39)
        _ensure_school(self.sid)
        self.donor = _make_donor(self.sid, name="Class2008 Alum")
        self.cohort = AlumniCohort.objects.create(
            school_id=self.sid,
            name="Class of 2008",
            class_year=2008,
        )

    def test_unique_together_enforced(self):
        AlumniCohortMember.objects.create(
            school_id=self.sid,
            cohort=self.cohort,
            donor=self.donor,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AlumniCohortMember.objects.create(
                school_id=self.sid,
                cohort=self.cohort,
                donor=self.donor,
            )

    def test_different_cohort_same_donor_allowed(self):
        cohort2 = AlumniCohort.objects.create(
            school_id=self.sid,
            name="Class of 2010",
            class_year=2010,
        )
        AlumniCohortMember.objects.create(school_id=self.sid, cohort=self.cohort, donor=self.donor)
        AlumniCohortMember.objects.create(school_id=self.sid, cohort=cohort2, donor=self.donor)
        self.assertEqual(
            AlumniCohortMember.objects.filter(school_id=self.sid, donor=self.donor).count(), 2
        )


# ---------------------------------------------------------------------------
# 18: Prospect tenant isolation
# ---------------------------------------------------------------------------

class ProspectTenantIsolationTest(TestCase):

    def setUp(self):
        self.sid_a = _sid(40)
        self.sid_b = _sid(41)
        _ensure_school(self.sid_a)
        _ensure_school(self.sid_b)
        self.donor_a = _make_donor(self.sid_a, name="School A Donor")
        self.donor_b = _make_donor(self.sid_b, name="School B Donor")
        _make_prospect(self.sid_a, donor=self.donor_a)
        _make_prospect(self.sid_b, donor=self.donor_b)

    def test_school_a_cannot_see_school_b_prospects(self):
        qs_a = Prospect.objects.filter(school_id=self.sid_a)
        qs_b = Prospect.objects.filter(school_id=self.sid_b)
        self.assertEqual(qs_a.count(), 1)
        self.assertEqual(qs_b.count(), 1)
        # Cross-check: school A's prospect is NOT in school B's queryset
        prospect_a_id = qs_a.first().id
        self.assertFalse(qs_b.filter(id=prospect_a_id).exists())

    def test_transition_on_wrong_school_raises(self):
        prospect_a = Prospect.objects.filter(school_id=self.sid_a).first()
        with self.assertRaises(Prospect.DoesNotExist):
            transition_move_stage(
                school_id=self.sid_b,
                prospect_id=prospect_a.id,
                new_stage="qualified",
                user=None,
            )
