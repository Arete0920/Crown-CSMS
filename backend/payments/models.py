import uuid

from django.conf import settings
from django.db import models


class GatewayProvider(models.TextChoices):
    COMPUWERX = "compuwerx", "Compuwerx"


class GatewayIntentStatus(models.TextChoices):
    CREATED = "created", "Created"
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    SETTLING = "settling", "Settling"
    SETTLED = "settled", "Settled"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    CANCELED = "canceled", "Canceled"


class GatewayEventStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"


class PaymentIntentRecord(models.Model):
    school_id = models.UUIDField(db_index=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)
    invoice_id = models.UUIDField(db_index=True, null=True, blank=True)
    household_id = models.UUIDField(db_index=True, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")

    client_reference_id = models.CharField(max_length=128, unique=True, db_index=True)
    provider_intent_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)

    status = models.CharField(
        max_length=32,
        choices=GatewayIntentStatus.choices,
        default=GatewayIntentStatus.CREATED,
        db_index=True,
    )

    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_payment_intents",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]


class GatewayEvent(models.Model):
    school_id = models.UUIDField(db_index=True, null=True, blank=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)

    event_id = models.CharField(max_length=128, db_index=True)
    event_type = models.CharField(max_length=128, db_index=True)

    provider_intent_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)

    signature = models.CharField(max_length=256, blank=True, default="")
    raw_body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=32,
        choices=GatewayEventStatus.choices,
        default=GatewayEventStatus.RECEIVED,
        db_index=True,
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"],
                name="uq_gateway_event_provider_event_id",
            )
        ]


class ProviderDisputeStatus(models.TextChoices):
    OPEN = "open", "Open"
    WON = "won", "Won"
    LOST = "lost", "Lost"
    CLOSED = "closed", "Closed"


class ProviderDispute(models.Model):
    school_id = models.UUIDField(db_index=True, null=True, blank=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)

    dispute_id = models.CharField(max_length=128, unique=True, db_index=True)
    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_intent_id = models.CharField(max_length=128, blank=True, default="", db_index=True)

    invoice_id = models.UUIDField(null=True, blank=True, db_index=True)
    household_id = models.UUIDField(null=True, blank=True, db_index=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    reason = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=ProviderDisputeStatus.choices,
        default=ProviderDisputeStatus.OPEN,
        db_index=True,
    )

    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]


class ProviderPayoutBatch(models.Model):
    school_id = models.UUIDField(db_index=True, null=True, blank=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)

    payout_id = models.CharField(max_length=128, unique=True, db_index=True)
    status = models.CharField(max_length=64, blank=True, default="", db_index=True)

    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")

    expected_payment_count = models.IntegerField(default=0)
    settled_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]


class ProviderPayoutEntry(models.Model):
    batch = models.ForeignKey(
        ProviderPayoutBatch,
        on_delete=models.PROTECT,
        related_name="entries",
    )

    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_intent_id = models.CharField(max_length=128, blank=True, default="", db_index=True)

    invoice_id = models.UUIDField(null=True, blank=True, db_index=True)
    household_id = models.UUIDField(null=True, blank=True, db_index=True)

    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")

    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class SavedPaymentMethod(models.Model):
    school_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(db_index=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)

    provider_customer_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_method_id = models.CharField(max_length=128, unique=True, db_index=True)

    method_type = models.CharField(max_length=32, blank=True, default="card")
    brand = models.CharField(max_length=32, blank=True, default="")
    last4 = models.CharField(max_length=8, blank=True, default="")
    exp_month = models.IntegerField(null=True, blank=True)
    exp_year = models.IntegerField(null=True, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-id"]


class ProviderDisputeAction(models.Model):
    dispute = models.ForeignKey(
        ProviderDispute,
        on_delete=models.CASCADE,
        related_name="actions",
    )

    action_type = models.CharField(max_length=64, db_index=True)
    note = models.TextField(blank=True, default="")
    provider_response_id = models.CharField(max_length=128, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_dispute_actions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class StatementExportStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    GENERATED = "generated", "Generated"
    FAILED = "failed", "Failed"


class StatementExportRequest(models.Model):
    school_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(db_index=True)
    format = models.CharField(max_length=16, default="csv")
    status = models.CharField(
        max_length=32,
        choices=StatementExportStatus.choices,
        default=StatementExportStatus.REQUESTED,
        db_index=True,
    )

    file_name = models.CharField(max_length=255, blank=True, default="")
    filters = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="statement_export_requests",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]


class PaymentExceptionSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class PaymentExceptionStatus(models.TextChoices):
    OPEN = "open", "Open"
    RETRYING = "retrying", "Retrying"
    RESOLVED = "resolved", "Resolved"
    IGNORED = "ignored", "Ignored"


class PaymentSupportException(models.Model):
    school_id = models.UUIDField(db_index=True)
    provider = models.CharField(max_length=32, choices=GatewayProvider.choices)

    category = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(
        max_length=16,
        choices=PaymentExceptionSeverity.choices,
        default=PaymentExceptionSeverity.ERROR,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentExceptionStatus.choices,
        default=PaymentExceptionStatus.OPEN,
        db_index=True,
    )

    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)

    gateway_event_id = models.IntegerField(null=True, blank=True, db_index=True)
    payment_intent_record_id = models.IntegerField(null=True, blank=True, db_index=True)
    dispute_id = models.IntegerField(null=True, blank=True, db_index=True)
    payout_batch_id = models.IntegerField(null=True, blank=True, db_index=True)
    household_id = models.UUIDField(null=True, blank=True, db_index=True)

    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_payment_exceptions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]


class BankStatementImportStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"


class BankStatementImport(models.Model):
    school_id = models.UUIDField(db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bank_statement_imports",
    )

    source_name = models.CharField(max_length=255, blank=True, default="")
    source_sha256 = models.CharField(max_length=64, blank=True, default="", db_index=True)
    status = models.CharField(
        max_length=32,
        choices=BankStatementImportStatus.choices,
        default=BankStatementImportStatus.UPLOADED,
        db_index=True,
    )
    row_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["school_id", "source_sha256"],
                condition=~models.Q(source_sha256=""),
                name="uq_bank_statement_import_school_hash",
            )
        ]


class BankStatementEntry(models.Model):
    school_id = models.UUIDField(db_index=True)
    statement_import = models.ForeignKey(
        BankStatementImport,
        on_delete=models.PROTECT,
        related_name="entries",
    )

    posted_date = models.DateField(db_index=True)
    description = models.CharField(max_length=255, blank=True, default="")
    reference = models.CharField(max_length=128, blank=True, default="", db_index=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")

    is_matched = models.BooleanField(default=False, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-posted_date", "-id"]


class PayoutBankMatchStatus(models.TextChoices):
    AUTO_MATCHED = "auto_matched", "Auto Matched"
    MANUAL_MATCHED = "manual_matched", "Manual Matched"
    REJECTED = "rejected", "Rejected"


class PayoutBankMatch(models.Model):
    school_id = models.UUIDField(db_index=True)
    payout_batch = models.ForeignKey(
        ProviderPayoutBatch,
        on_delete=models.PROTECT,
        related_name="bank_matches",
    )
    bank_entry = models.ForeignKey(
        BankStatementEntry,
        on_delete=models.PROTECT,
        related_name="payout_matches",
    )

    status = models.CharField(
        max_length=32,
        choices=PayoutBankMatchStatus.choices,
        default=PayoutBankMatchStatus.AUTO_MATCHED,
        db_index=True,
    )

    amount_delta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_delta_days = models.IntegerField(default=0)
    note = models.TextField(blank=True, default="")

    matched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payout_bank_matches",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payout_batch", "bank_entry"],
                name="uq_payout_bank_match_pair",
            ),
            models.UniqueConstraint(
                fields=["payout_batch"],
                condition=models.Q(
                    status__in=[
                        PayoutBankMatchStatus.AUTO_MATCHED,
                        PayoutBankMatchStatus.MANUAL_MATCHED,
                    ]
                ),
                name="uq_active_payout_bank_match_payout",
            ),
            models.UniqueConstraint(
                fields=["bank_entry"],
                condition=models.Q(
                    status__in=[
                        PayoutBankMatchStatus.AUTO_MATCHED,
                        PayoutBankMatchStatus.MANUAL_MATCHED,
                    ]
                ),
                name="uq_active_payout_bank_match_bank",
            ),
        ]


# ---------------------------------------------------------------------------
# Option A canonical Payments authority
# ---------------------------------------------------------------------------

from django.core.exceptions import ValidationError


class CanonicalPaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    SETTLING = "settling", "Settling"
    SETTLED = "settled", "Settled"
    FAILED = "failed", "Failed"
    VOID = "void", "Void"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    REFUNDED = "refunded", "Refunded"


class CanonicalRefundStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    PENDING = "pending", "Pending"
    SETTLED = "settled", "Settled"
    FAILED = "failed", "Failed"
    CANCELED = "canceled", "Canceled"


class ImmutableFinancialFactQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Canonical payment facts cannot be bulk-updated.")

    def delete(self):
        raise ValidationError("Canonical payment facts cannot be hard-deleted.")


class ImmutableFinancialFactManager(models.Manager.from_queryset(ImmutableFinancialFactQuerySet)):
    pass


class ImmutableFinancialFact(models.Model):
    objects = ImmutableFinancialFactManager()
    immutable_fields = ()
    write_once_fields = ()

    class Meta:
        abstract = True

    def _assert_immutable(self):
        if not self.pk:
            return
        original = type(self).objects.get(pk=self.pk)
        for field_name in self.immutable_fields:
            if getattr(original, field_name) != getattr(self, field_name):
                raise ValidationError(f"Canonical payment fact {field_name} is immutable.")
        for field_name in self.write_once_fields:
            old_value = getattr(original, field_name)
            new_value = getattr(self, field_name)
            if old_value not in (None, "") and new_value != old_value:
                raise ValidationError(f"Canonical payment fact {field_name} is write-once.")

    def save(self, *args, **kwargs):
        self._assert_immutable()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Canonical payment facts cannot be hard-deleted.")


class Payment(ImmutableFinancialFact):
    school_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(null=True, blank=True, db_index=True)
    finance_payment_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    amount_cents = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(
        max_length=32,
        choices=CanonicalPaymentStatus.choices,
        default=CanonicalPaymentStatus.PENDING,
        db_index=True,
    )

    provider = models.CharField(max_length=64, blank=True, default="", db_index=True)
    provider_intent_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=128, db_index=True)

    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="canonical_payments_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    authorized_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)

    immutable_fields = (
        "school_id",
        "household_id",
        "finance_payment_id",
        "amount_cents",
        "currency",
        "idempotency_key",
        "created_by_id",
    )
    write_once_fields = ("provider", "provider_intent_id", "provider_payment_id")

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["school_id", "status"]),
            models.Index(fields=["school_id", "household_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0),
                name="payments_payment_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["school_id", "idempotency_key"],
                name="uq_payments_payment_school_idempotency",
            ),
            models.UniqueConstraint(
                fields=["finance_payment_id"],
                condition=models.Q(finance_payment_id__isnull=False),
                name="uq_payments_payment_finance_payment",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_intent_id"],
                condition=~models.Q(provider="") & ~models.Q(provider_intent_id=""),
                name="uq_payments_payment_provider_intent",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_payment_id"],
                condition=~models.Q(provider="") & ~models.Q(provider_payment_id=""),
                name="uq_payments_payment_provider_payment",
            ),
        ]

    def clean(self):
        if self.amount_cents <= 0:
            raise ValidationError("Canonical payment amount must be positive.")
        if not self.idempotency_key:
            raise ValidationError("Canonical payment idempotency_key is required.")


class Refund(ImmutableFinancialFact):
    school_id = models.UUIDField(db_index=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    finance_refund_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    amount_cents = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(
        max_length=32,
        choices=CanonicalRefundStatus.choices,
        default=CanonicalRefundStatus.REQUESTED,
        db_index=True,
    )

    provider = models.CharField(max_length=64, blank=True, default="", db_index=True)
    provider_refund_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=128, db_index=True)

    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="canonical_refunds_created",
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    immutable_fields = (
        "school_id",
        "payment_id",
        "amount_cents",
        "currency",
        "idempotency_key",
        "created_by_id",
    )
    write_once_fields = ("finance_refund_id", "provider", "provider_refund_id")

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["school_id", "status"]),
            models.Index(fields=["payment", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0),
                name="payments_refund_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["school_id", "idempotency_key"],
                name="uq_payments_refund_school_idempotency",
            ),
            models.UniqueConstraint(
                fields=["finance_refund_id"],
                condition=models.Q(finance_refund_id__isnull=False),
                name="uq_payments_refund_finance_refund",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_refund_id"],
                condition=~models.Q(provider="") & ~models.Q(provider_refund_id=""),
                name="uq_payments_refund_provider_refund",
            ),
        ]

    def clean(self):
        if self.amount_cents <= 0:
            raise ValidationError("Canonical refund amount must be positive.")
        if not self.idempotency_key:
            raise ValidationError("Canonical refund idempotency_key is required.")
        if self.payment_id:
            if self.school_id != self.payment.school_id:
                raise ValidationError("Canonical refund school must match payment school.")
            if self.currency != self.payment.currency:
                raise ValidationError("Canonical refund currency must match payment currency.")
