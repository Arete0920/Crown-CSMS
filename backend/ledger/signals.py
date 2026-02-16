from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import School
from journal.models import GLAccount, JournalEntry
from journal.services import post_journal_entry
from ledger.models import Charge, Payment


User = get_user_model()


def _get_system_user():
    user, _ = User.objects.get_or_create(
        username="crown-system",
        defaults={"email": "system@crown.local"},
    )
    return user


def _ensure_canonical_gl_accounts(school):
    cash, _ = GLAccount.objects.get_or_create(
        school=school,
        code="1000",
        defaults={"name": "Cash", "account_type": "ASSET"},
    )
    ar, _ = GLAccount.objects.get_or_create(
        school=school,
        code="1100",
        defaults={"name": "Accounts Receivable", "account_type": "ASSET"},
    )
    revenue, _ = GLAccount.objects.get_or_create(
        school=school,
        code="4000",
        defaults={"name": "Tuition Revenue", "account_type": "REVENUE"},
    )
    return cash, ar, revenue


def _already_posted(reference_type, reference_id):
    return JournalEntry.objects.filter(
        reference_type=reference_type,
        reference_id=reference_id,
    ).exists()


@receiver(post_save, sender=Charge)
def post_charge_to_journal(sender, instance: Charge, created, **kwargs):
    if not created:
        return
    if instance.is_void:
        return
    if _already_posted("charge", instance.id):
        return

    school = School.objects.filter(id=instance.school_id).first()
    if not school:
        raise ValidationError("Charge.school_id does not map to a School.")

    _, ar, revenue = _ensure_canonical_gl_accounts(school)

    amount = instance.amount
    if amount is None or amount <= 0:
        raise ValidationError("Charge amount must be > 0 to post to journal.")

    post_journal_entry(
        school=school,
        created_by=_get_system_user(),
        lines=[
            {"account": ar, "debit": amount},
            {"account": revenue, "credit": amount},
        ],
        memo=f"Charge: {instance.description}",
        reference_type="charge",
        reference_id=instance.id,
    )


@receiver(post_save, sender=Payment)
def post_payment_to_journal(sender, instance: Payment, created, **kwargs):
    if not created:
        return
    if _already_posted("payment", instance.id):
        return

    school = School.objects.filter(id=instance.school_id).first()
    if not school:
        raise ValidationError("Payment.school_id does not map to a School.")

    cash, ar, _ = _ensure_canonical_gl_accounts(school)

    amount = instance.amount
    if amount is None or amount <= 0:
        raise ValidationError("Payment amount must be > 0 to post to journal.")

    post_journal_entry(
        school=school,
        created_by=_get_system_user(),
        lines=[
            {"account": cash, "debit": amount},
            {"account": ar, "credit": amount},
        ],
        memo=f"Payment: {instance.source} {instance.reference}".strip(),
        reference_type="payment",
        reference_id=instance.id,
    )
