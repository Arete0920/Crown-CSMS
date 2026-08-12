from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import FinanceAllocation, FinanceInvoiceLine, FinanceRefund


@receiver(pre_save, sender=FinanceInvoiceLine)
def validate_invoice_line_money_boundary(sender, instance, **kwargs):
    invoice = instance.invoice
    obligation = instance.obligation
    if invoice.school_id != obligation.school_id:
        raise ValidationError("Invoice and obligation must belong to the same school.")
    if invoice.payer_user_id != obligation.payer_user_id:
        raise ValidationError("Invoice and obligation must belong to the same payer.")
    if int(instance.amount_cents) != int(obligation.amount_cents):
        raise ValidationError("Invoice line amount must match the obligation amount snapshot.")


@receiver(pre_save, sender=FinanceAllocation)
def validate_allocation_money_boundary(sender, instance, **kwargs):
    payment = instance.payment
    obligation = instance.obligation
    if instance.school_id != payment.school_id or instance.school_id != obligation.school_id:
        raise ValidationError("Allocation, payment, and obligation must belong to the same school.")
    if payment.payer_user_id != obligation.payer_user_id:
        raise ValidationError("Payment and obligation must belong to the same payer.")
    if int(instance.amount_cents) <= 0:
        raise ValidationError("Allocation amount must be positive.")


@receiver(pre_save, sender=FinanceRefund)
def validate_refund_money_boundary(sender, instance, **kwargs):
    payment = instance.payment
    if instance.school_id != payment.school_id:
        raise ValidationError("Refund and payment must belong to the same school.")
    if instance.currency.upper() != payment.currency.upper():
        raise ValidationError("Refund currency must match payment currency.")
