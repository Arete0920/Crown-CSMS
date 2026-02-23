"""
Stage 2 – Financial Invariant Lock
===================================
Aid Award Ledger Invariant Tests

Invariants proved:
  1. Ledger credit sign     – mark_accepted_and_post() always posts amount_cents < 0
  2. Magnitude preserved    – abs(amount_cents) == awarded_cents exactly
  3. Double-post prevented  – second call returns the existing entry; no new row created
  4. Reversal nets to zero  – original + reversal amount_cents sum to 0
  5. Reversal is flagged    – reversal entry has is_reversal=True
  6. Audit trail – post     – AWARD_ACCEPTED and LEDGER_POSTED events exist after posting
  7. Audit trail – decline  – AWARD_DECLINED and LEDGER_REVERSED events exist after reversal
"""

from datetime import date

from django.test import TestCase

from aid.models import AidAuditEvent, AidAward
from core.models import AcademicYear, Family, LedgerEntry, School, Student
from finance.models import ChartAccount


# ---------------------------------------------------------------------------
# Shared fixture factory
# ---------------------------------------------------------------------------

def _make_fixtures():
    """Return (school, academic_year, student) with ChartAccount code='AID' ready."""
    school = School.objects.create(name="Invariant Test School")
    ay = AcademicYear.objects.create(
        school=school,
        name="2026-27",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
    )
    family = Family.objects.create(school=school, family_name="Doe")
    student = Student.objects.create(
        school=school,
        family=family,
        student_number="S001",
        first_name="Jane",
        last_name="Doe",
        dob=date(2012, 3, 15),
    )
    # ChartAccount with code="AID" must exist before mark_accepted_and_post() is called.
    ChartAccount.objects.create(
        school=school,
        code="AID",
        name="Financial Aid",
        account_type="INCOME",
    )
    return school, ay, student


def _make_award(school, ay, student, *, awarded_cents=50_000):
    return AidAward.objects.create(
        school=school,
        academic_year=ay,
        student=student,
        award_type=AidAward.TYPE_NEED,
        awarded_cents=awarded_cents,
    )


# ---------------------------------------------------------------------------
# 1 & 2: Ledger credit sign + magnitude preserved
# ---------------------------------------------------------------------------

class TestAidLedgerSign(TestCase):
    """The LedgerEntry posted by mark_accepted_and_post() must be negative (credit)
    and its absolute value must equal awarded_cents exactly."""

    def setUp(self):
        self.school, self.ay, self.student = _make_fixtures()

    def test_amount_cents_is_negative(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=50_000)
        entry = award.mark_accepted_and_post()
        self.assertLess(
            entry.amount_cents,
            0,
            f"AID ledger entry must be a credit (negative); got {entry.amount_cents}",
        )

    def test_magnitude_matches_awarded_cents(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=75_000)
        entry = award.mark_accepted_and_post()
        self.assertEqual(
            abs(entry.amount_cents),
            75_000,
            f"abs(amount_cents) must equal awarded_cents exactly; "
            f"got abs({entry.amount_cents}) != 75000",
        )

    def test_full_sign_and_magnitude_combined(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=12_345)
        entry = award.mark_accepted_and_post()
        self.assertEqual(
            entry.amount_cents,
            -12_345,
            f"Expected amount_cents=-12345; got {entry.amount_cents}",
        )


# ---------------------------------------------------------------------------
# 3: Double-post prevention (idempotency)
# ---------------------------------------------------------------------------

class TestAidDoublePostPrevented(TestCase):
    """Calling mark_accepted_and_post() twice must not create a second LedgerEntry."""

    def setUp(self):
        self.school, self.ay, self.student = _make_fixtures()

    def test_second_call_returns_same_entry(self):
        award = _make_award(self.school, self.ay, self.student)
        entry_a = award.mark_accepted_and_post()
        entry_b = award.mark_accepted_and_post()
        self.assertEqual(
            entry_a.id,
            entry_b.id,
            "Second call must return the existing entry, not create a new one",
        )

    def test_exactly_one_ledger_entry_after_two_calls(self):
        award = _make_award(self.school, self.ay, self.student)
        award.mark_accepted_and_post()
        award.mark_accepted_and_post()
        count = LedgerEntry.objects.filter(
            school=self.school,
            student=self.student,
            source=LedgerEntry.SOURCE_AID_AWARD,
        ).count()
        self.assertEqual(
            count,
            1,
            f"Exactly 1 AID LedgerEntry must exist after two post() calls; found {count}",
        )


# ---------------------------------------------------------------------------
# 4 & 5: Reversal nets to zero + is_reversal flag
# ---------------------------------------------------------------------------

class TestAidReversalNetsToZero(TestCase):
    """post → decline: sum of all LedgerEntry rows for this student must be 0."""

    def setUp(self):
        self.school, self.ay, self.student = _make_fixtures()

    def test_net_balance_is_zero_after_reversal(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=30_000)
        award.mark_accepted_and_post()
        award.mark_declined_and_reverse()

        entries = LedgerEntry.objects.filter(school=self.school, student=self.student)
        net = sum(e.amount_cents for e in entries)
        self.assertEqual(
            net,
            0,
            f"Net of original + reversal must equal 0; got {net}",
        )

    def test_reversal_entry_flagged_is_reversal_true(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=10_000)
        award.mark_accepted_and_post()
        award.mark_declined_and_reverse()

        reversals = LedgerEntry.objects.filter(
            school=self.school,
            student=self.student,
            is_reversal=True,
        )
        self.assertEqual(
            reversals.count(),
            1,
            "Exactly one entry must be flagged is_reversal=True after decline",
        )

    def test_two_entries_exist_total(self):
        award = _make_award(self.school, self.ay, self.student, awarded_cents=20_000)
        award.mark_accepted_and_post()
        award.mark_declined_and_reverse()

        total = LedgerEntry.objects.filter(school=self.school, student=self.student).count()
        self.assertEqual(total, 2, "Exactly 2 entries (original + reversal) must exist")


# ---------------------------------------------------------------------------
# 6 & 7: Audit trail
# ---------------------------------------------------------------------------

class TestAidAuditTrail(TestCase):
    """AidAuditEvent rows are created at every planned transition."""

    def setUp(self):
        self.school, self.ay, self.student = _make_fixtures()

    def _events(self, award):
        return set(
            AidAuditEvent.objects.filter(
                school=self.school,
                entity_type=AidAuditEvent.ENTITY_AWARD,
                entity_id=award.id,
            ).values_list("action", flat=True)
        )

    def test_post_emits_accepted_and_ledger_posted_events(self):
        award = _make_award(self.school, self.ay, self.student)
        award.mark_accepted_and_post()
        actions = self._events(award)
        self.assertIn("AWARD_ACCEPTED", actions, "AWARD_ACCEPTED event must be logged on post")
        self.assertIn("LEDGER_POSTED", actions, "LEDGER_POSTED event must be logged on post")

    def test_decline_emits_declined_and_ledger_reversed_events(self):
        award = _make_award(self.school, self.ay, self.student)
        award.mark_accepted_and_post()
        award.mark_declined_and_reverse()
        actions = self._events(award)
        self.assertIn("AWARD_DECLINED", actions, "AWARD_DECLINED event must be logged on decline")
        self.assertIn("LEDGER_REVERSED", actions, "LEDGER_REVERSED event must be logged on reversal")

    def test_full_lifecycle_event_count(self):
        """post + decline = at least 4 events (accepted, posted, declined, reversed)."""
        award = _make_award(self.school, self.ay, self.student)
        award.mark_accepted_and_post()
        award.mark_declined_and_reverse()
        count = AidAuditEvent.objects.filter(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=award.id,
        ).count()
        self.assertGreaterEqual(count, 4, f"Full lifecycle must produce >=4 audit events; got {count}")
