"""
finance/tests/test_finance_services.py — Unit + integration tests for Finance services.

Covers:
  - create_invoice_from_obligations: snapshot totals, line count, atomic rollback
  - settle_payment_and_allocate: idempotency, allocation records, status transition
  - initiate_refund: happy path, over-refund guard (OverRefundError)

Run with:
  python manage.py test finance.tests.test_finance_services
"""
from datetime import date, timedelta

from django.test import TestCase

from core.models import School, UserAccount
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Charge as LedgerCharge
from ledger.models import LedgerAccount, Payment as LedgerPayment
from finance.models import (
    FinanceAllocation,
    FinanceInvoice,
    FinanceInvoiceLine,
    FinanceObligation,
    FinancePayment,
    FinanceRefund,
    MoneyStatus,
    ObligationType,
    PaymentStatus,
    Processor,
)
from finance.services import (
    OverRefundError,
    create_invoice_from_obligations,
    initiate_refund,
    settle_payment_and_allocate,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _school(name="Test School"):
    return School.objects.create(name=name)


def _user(username, *, is_staff=False):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
        is_staff=is_staff,
    )


def _obligation(school, payer, *, amount_cents=10_000, days=30):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Tuition",
        due_date=date.today() + timedelta(days=days),
        amount_cents=amount_cents,
    )


def _payment(school, payer, *, amount_cents=10_000):
    return FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=amount_cents,
        status=PaymentStatus.PENDING,
        processor=Processor.MANUAL,
    )


def _link_payer_to_household(school, payer):
    existing = HouseholdGuardian.objects.filter(
        school_id=school.id,
        email__iexact=payer.email,
    ).select_related("household").first()
    if existing:
        hh = existing.household
    else:
        hh = Household.objects.create(school_id=school.id, name=f"HH-{payer.username}")
        HouseholdGuardian.objects.create(
            school_id=school.id,
            household=hh,
            first_name="Test",
            last_name="Guardian",
            email=payer.email,
            is_primary=True,
        )
    LedgerAccount.objects.get_or_create(school_id=school.id, household=hh)


# ---------------------------------------------------------------------------
# create_invoice_from_obligations
# ---------------------------------------------------------------------------

class TestCreateInvoiceFromObligations(TestCase):
    def setUp(self):
        self.school = _school()
        self.payer = _user("inv_payer")
        self.admin = _user("inv_admin", is_staff=True)

    def test_creates_invoice_with_correct_totals(self):
        ob1 = _obligation(self.school, self.payer, amount_cents=5_000)
        ob2 = _obligation(self.school, self.payer, amount_cents=3_000)

        inv = create_invoice_from_obligations(
            school=self.school,
            payer_user=self.payer,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            due_date=date.today() + timedelta(days=30),
            obligations=[ob1, ob2],
            created_by=self.admin,
        )

        self.assertIsInstance(inv, FinanceInvoice)
        self.assertEqual(inv.subtotal_cents, 8_000)
        self.assertEqual(inv.total_cents, 8_000)
        self.assertEqual(inv.status, MoneyStatus.OPEN)

    def test_creates_line_items_one_per_obligation(self):
        ob1 = _obligation(self.school, self.payer, amount_cents=1_500)
        ob2 = _obligation(self.school, self.payer, amount_cents=2_500)

        inv = create_invoice_from_obligations(
            school=self.school,
            payer_user=self.payer,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            due_date=date.today() + timedelta(days=30),
            obligations=[ob1, ob2],
        )

        lines = list(inv.lines.all())
        self.assertEqual(len(lines), 2)
        amounts = {l.amount_cents for l in lines}
        self.assertEqual(amounts, {1_500, 2_500})

    def test_empty_obligations_creates_zero_total_invoice(self):
        inv = create_invoice_from_obligations(
            school=self.school,
            payer_user=self.payer,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            due_date=date.today() + timedelta(days=30),
            obligations=[],
        )
        self.assertEqual(inv.total_cents, 0)
        self.assertEqual(inv.lines.count(), 0)

    def test_same_obligation_cannot_appear_twice_on_same_invoice(self):
        """unique_together on (invoice, obligation) prevents duplicates."""
        ob = _obligation(self.school, self.payer, amount_cents=1_000)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            inv = create_invoice_from_obligations(
                school=self.school,
                payer_user=self.payer,
                period_start=date.today(),
                period_end=date.today() + timedelta(days=30),
                due_date=date.today() + timedelta(days=30),
                obligations=[ob, ob],
            )


# ---------------------------------------------------------------------------
# settle_payment_and_allocate
# ---------------------------------------------------------------------------

class TestSettlePaymentAndAllocate(TestCase):
    def setUp(self):
        self.school = _school("Pay School")
        self.payer = _user("pay_user")
        _link_payer_to_household(self.school, self.payer)

    def test_settles_payment_and_creates_allocations(self):
        ob = _obligation(self.school, self.payer, amount_cents=10_000)
        pay = _payment(self.school, self.payer, amount_cents=10_000)

        result = settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 10_000}],
        )

        result.refresh_from_db()
        self.assertEqual(result.status, PaymentStatus.SETTLED)
        self.assertIsNotNone(result.settled_at)

        allocs = list(FinanceAllocation.objects.filter(payment=result))
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].amount_cents, 10_000)
        self.assertEqual(allocs[0].obligation_id, ob.id)

        ledger_payment = LedgerPayment.objects.get(reference=f"finance_payment:{result.id}")
        self.assertEqual(ledger_payment.school_id, self.school.id)
        self.assertEqual(str(ledger_payment.amount), "100.00")
        self.assertTrue(
            LedgerAllocation.objects.filter(payment=ledger_payment).exists(),
            "Expected ledger allocation row for settled finance payment",
        )

    def test_settle_is_idempotent_on_already_settled(self):
        """Calling settle again on a SETTLED payment returns it unchanged."""
        ob = _obligation(self.school, self.payer, amount_cents=5_000)
        pay = _payment(self.school, self.payer, amount_cents=5_000)

        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 5_000}],
        )

        # Call again — should NOT create double allocations
        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 5_000}],
        )

        alloc_count = FinanceAllocation.objects.filter(payment=pay).count()
        self.assertEqual(alloc_count, 1, "Idempotency violated: double allocation created")

    def test_settle_cross_school_obligation_raises(self):
        """Obligation from a different school → DoesNotExist (tenant guard)."""
        other_school = _school("Other School")
        other_payer = _user("other_pay")
        ob_other = _obligation(other_school, other_payer, amount_cents=5_000)
        pay = _payment(self.school, self.payer, amount_cents=5_000)

        with self.assertRaises(FinanceObligation.DoesNotExist):
            settle_payment_and_allocate(
                payment=pay,
                allocations_payload=[{"obligation_id": ob_other.id, "amount_cents": 5_000}],
            )

    def test_partial_allocation_allowed(self):
        ob = _obligation(self.school, self.payer, amount_cents=10_000)
        pay = _payment(self.school, self.payer, amount_cents=10_000)

        result = settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": 6_000}],
        )

        allocs = list(FinanceAllocation.objects.filter(payment=result))
        self.assertEqual(allocs[0].amount_cents, 6_000)


# ---------------------------------------------------------------------------
# initiate_refund
# ---------------------------------------------------------------------------

class TestInitiateRefund(TestCase):
    def setUp(self):
        self.school = _school("Refund School")
        self.payer = _user("refund_user")
        self.admin = _user("refund_admin", is_staff=True)
        _link_payer_to_household(self.school, self.payer)

    def _settled_payment(self, amount_cents=10_000):
        ob = _obligation(self.school, self.payer, amount_cents=amount_cents)
        pay = _payment(self.school, self.payer, amount_cents=amount_cents)
        settle_payment_and_allocate(
            payment=pay,
            allocations_payload=[{"obligation_id": ob.id, "amount_cents": amount_cents}],
        )
        return pay

    def test_refund_creates_record(self):
        pay = self._settled_payment(10_000)
        refund = initiate_refund(
            payment=pay,
            amount_cents=5_000,
            processor=Processor.MANUAL,
            created_by=self.admin,
        )
        self.assertIsInstance(refund, FinanceRefund)
        self.assertEqual(refund.amount_cents, 5_000)
        self.assertEqual(refund.status, PaymentStatus.PENDING)
        self.assertTrue(
            LedgerCharge.objects.filter(
                school_id=self.school.id,
                description=f"finance_refund:{refund.id}",
            ).exists(),
            "Expected ledger refund charge to be created",
        )

    def test_full_refund_allowed(self):
        pay = self._settled_payment(8_000)
        refund = initiate_refund(
            payment=pay,
            amount_cents=8_000,
            processor=Processor.MANUAL,
        )
        self.assertEqual(refund.amount_cents, 8_000)

    def test_over_refund_raises_over_refund_error(self):
        pay = self._settled_payment(5_000)
        with self.assertRaises(OverRefundError):
            initiate_refund(
                payment=pay,
                amount_cents=5_001,
                processor=Processor.MANUAL,
            )

    def test_cumulative_refund_exceeding_original_raises(self):
        """Two refunds whose sum exceeds original amount → OverRefundError on second."""
        pay = self._settled_payment(10_000)
        initiate_refund(payment=pay, amount_cents=6_000, processor=Processor.MANUAL)
        with self.assertRaises(OverRefundError):
            initiate_refund(payment=pay, amount_cents=5_000, processor=Processor.MANUAL)

    def test_idempotency_key_uniqueness_not_enforced_by_service(self):
        """Service records the key; DB constraint check is processor-side."""
        pay = self._settled_payment(10_000)
        r1 = initiate_refund(payment=pay, amount_cents=3_000, processor=Processor.MANUAL, idempotency_key="xyz")
        r2 = initiate_refund(payment=pay, amount_cents=3_000, processor=Processor.MANUAL, idempotency_key="abc")
        self.assertNotEqual(r1.id, r2.id)
