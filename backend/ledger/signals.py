from decimal import Decimal
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import School
from journal.models import GLAccount, JournalEntry
from journal.services import post_journal_entry, create_reversal_entry
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


def _is_finance_refund_charge(instance: Charge) -> bool:
    return (instance.description or "").startswith("finance_refund:")


@receiver(post_save, sender=Charge)
def post_charge_to_journal(sender, instance: Charge, created, **kwargs):
    if not created:
        return
    if instance.is_void:
        return

    is_finance_refund = _is_finance_refund_charge(instance)
    reference_type = "finance_refund" if is_finance_refund else "charge"
    if _already_posted(reference_type, instance.id):
        return

    school = School.objects.filter(pk=instance.school_id).first()
    if not school:
        raise ValidationError("Charge.school_id does not map to a School.")

    cash, ar, revenue = _ensure_canonical_gl_accounts(school)

    amount = instance.amount
    if amount is None or amount <= 0:
        raise ValidationError("Charge amount must be > 0 to post to journal.")

    if is_finance_refund:
        lines = [
            {"account": ar, "debit": amount},
            {"account": cash, "credit": amount},
        ]
        memo = f"Refund: {instance.description}"
    else:
        lines = [
            {"account": ar, "debit": amount},
            {"account": revenue, "credit": amount},
        ]
        memo = f"Charge: {instance.description}"

    post_journal_entry(
        school=school,
        created_by=_get_system_user(),
        lines=lines,
        memo=memo,
        reference_type=reference_type,
        reference_id=instance.id,
    )


@receiver(post_save, sender=Payment)
def post_payment_to_journal(sender, instance: Payment, created, **kwargs):
    if not created:
        return
    if instance.is_void:
        return
    if _already_posted("payment", instance.id):
        return

    school = School.objects.filter(pk=instance.school_id).first()
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


@receiver(pre_save, sender=Charge)
def _charge_capture_void_flip(sender, instance: Charge, **kwargs):
    """
    Store a flag on the instance when is_void flips False -> True.
    This avoids guessing in post_save and avoids re-querying after save.
    """
    instance._void_flip_to_true = False

    if not instance.pk:
        return

    prior = sender.objects.filter(pk=instance.pk).values_list("is_void", flat=True).first()
    if prior is None:
        return

    if (bool(prior) is False) and (bool(instance.is_void) is True):
        instance._void_flip_to_true = True


@receiver(post_save, sender=Charge)
def _charge_create_void_reversal(sender, instance: Charge, created: bool, **kwargs):
    if created:
        return
    if not getattr(instance, "_void_flip_to_true", False):
        return

    original = (
        JournalEntry.objects
        .select_related("school", "created_by")
        .filter(
            school_id=instance.school_id,
            reference_type="charge",
            reference_id=instance.id,
        )
        .order_by("-id")
        .first()
    )
    if not original:
        return

    create_reversal_entry(
        original_entry=original,
        reason=f"Charge voided ({instance.id})",
        reference_type="charge_void_reversal",
    )


@receiver(pre_save, sender=Payment)
def _payment_capture_void_flip(sender, instance: Payment, **kwargs):
    """
    Store a flag on the instance when is_void flips False -> True.
    This avoids guessing in post_save and avoids re-querying after save.
    """
    instance._void_flip_to_true = False

    if not instance.pk:
        return

    prior = sender.objects.filter(pk=instance.pk).values_list("is_void", flat=True).first()
    if prior is None:
        return

    if (bool(prior) is False) and (bool(instance.is_void) is True):
        instance._void_flip_to_true = True


@receiver(post_save, sender=Payment)
def _payment_create_void_reversal(sender, instance: Payment, created: bool, **kwargs):
    if created:
        return
    if not getattr(instance, "_void_flip_to_true", False):
        return

    original = (
        JournalEntry.objects
        .select_related("school", "created_by")
        .filter(
            school_id=instance.school_id,
            reference_type="payment",
            reference_id=instance.id,
        )
        .order_by("-id")
        .first()
    )
    if not original:
        return

    create_reversal_entry(
        original_entry=original,
        reason=f"Payment voided ({instance.id})",
        reference_type="payment_void_reversal",
    )
