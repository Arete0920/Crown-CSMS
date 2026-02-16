from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment
from journal.models import JournalEntry, GLAccount


User = get_user_model()


class ARPostsToJournalTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Heritage Test School")

        # System user should be created by posting, but we create a normal user too (future use)
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="pass1234",
        )

        self.household = Household.objects.create(
            school_id=self.school.id,
            name="Test Household",
        )

        self.ledger_account = LedgerAccount.objects.create(
            school_id=self.school.id,
            household=self.household,
        )

    def _sum_entry(self, entry: JournalEntry):
        debit = Decimal("0.00")
        credit = Decimal("0.00")
        for line in entry.lines.all():
            debit += line.debit
            credit += line.credit
        return debit, credit

    def test_charge_creation_posts_one_balanced_journal_entry(self):
        c = Charge.objects.create(
            school_id=self.school.id,
            account=self.ledger_account,
            description="Tuition charge",
            amount=Decimal("250.00"),
            is_void=False,
        )

        qs = JournalEntry.objects.filter(reference_type="charge", reference_id=c.id)
        self.assertEqual(qs.count(), 1)

        entry = qs.first()
        self.assertTrue(entry.locked)

        debit, credit = self._sum_entry(entry)
        self.assertEqual(debit, Decimal("250.00"))
        self.assertEqual(credit, Decimal("250.00"))

    def test_payment_creation_posts_one_balanced_journal_entry(self):
        p = Payment.objects.create(
            school_id=self.school.id,
            account=self.ledger_account,
            source="EXTERNAL",
            reference="txn_123",
            amount=Decimal("125.00"),
        )

        qs = JournalEntry.objects.filter(reference_type="payment", reference_id=p.id)
        self.assertEqual(qs.count(), 1)

        entry = qs.first()
        self.assertTrue(entry.locked)

        debit, credit = self._sum_entry(entry)
        self.assertEqual(debit, Decimal("125.00"))
        self.assertEqual(credit, Decimal("125.00"))

    def test_idempotent_posting_no_duplicate_on_resave(self):
        c = Charge.objects.create(
            school_id=self.school.id,
            account=self.ledger_account,
            description="Tuition charge",
            amount=Decimal("100.00"),
            is_void=False,
        )

        self.assertEqual(
            JournalEntry.objects.filter(reference_type="charge", reference_id=c.id).count(),
            1,
        )

        # resave should not create another journal entry
        c.description = "Tuition charge updated"
        c.save()

        self.assertEqual(
            JournalEntry.objects.filter(reference_type="charge", reference_id=c.id).count(),
            1,
        )

    def test_void_charge_does_not_post(self):
        c = Charge.objects.create(
            school_id=self.school.id,
            account=self.ledger_account,
            description="Voided charge",
            amount=Decimal("100.00"),
            is_void=True,
        )
        self.assertEqual(
            JournalEntry.objects.filter(reference_type="charge", reference_id=c.id).count(),
            0,
        )

    def test_canonical_gl_accounts_are_created(self):
        # Trigger via charge
        Charge.objects.create(
            school_id=self.school.id,
            account=self.ledger_account,
            description="Tuition charge",
            amount=Decimal("10.00"),
            is_void=False,
        )

        codes = set(
            GLAccount.objects.filter(school=self.school).values_list("code", flat=True)
        )
        self.assertTrue({"1000", "1100", "4000"}.issubset(codes))
