# Generated for Option A canonical Payments authority.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0004_bankstatementimport_bankstatemententry_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("school_id", models.UUIDField(db_index=True)),
                ("household_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("finance_payment_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("amount_cents", models.PositiveBigIntegerField()),
                ("currency", models.CharField(default="USD", max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("authorized", "Authorized"),
                            ("settling", "Settling"),
                            ("settled", "Settled"),
                            ("failed", "Failed"),
                            ("void", "Void"),
                            ("partially_refunded", "Partially Refunded"),
                            ("refunded", "Refunded"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("provider", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                (
                    "provider_intent_id",
                    models.CharField(blank=True, db_index=True, default="", max_length=128),
                ),
                (
                    "provider_payment_id",
                    models.CharField(blank=True, db_index=True, default="", max_length=128),
                ),
                ("idempotency_key", models.CharField(db_index=True, max_length=128)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("authorized_at", models.DateTimeField(blank=True, null=True)),
                ("settled_at", models.DateTimeField(blank=True, null=True)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="canonical_payments_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
                "indexes": [
                    models.Index(fields=["school_id", "status"], name="payments_pa_school__deeb91_idx"),
                    models.Index(fields=["school_id", "household_id"], name="payments_pa_school__ae3f8d_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_cents__gt", 0)),
                        name="payments_payment_amount_positive",
                    ),
                    models.UniqueConstraint(
                        fields=("school_id", "idempotency_key"),
                        name="uq_payments_payment_school_idempotency",
                    ),
                    models.UniqueConstraint(
                        condition=~models.Q(("provider", ""))
                        & ~models.Q(("provider_intent_id", "")),
                        fields=("provider", "provider_intent_id"),
                        name="uq_payments_payment_provider_intent",
                    ),
                    models.UniqueConstraint(
                        condition=~models.Q(("provider", ""))
                        & ~models.Q(("provider_payment_id", "")),
                        fields=("provider", "provider_payment_id"),
                        name="uq_payments_payment_provider_payment",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Refund",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("school_id", models.UUIDField(db_index=True)),
                ("finance_refund_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("amount_cents", models.PositiveBigIntegerField()),
                ("currency", models.CharField(default="USD", max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("requested", "Requested"),
                            ("pending", "Pending"),
                            ("settled", "Settled"),
                            ("failed", "Failed"),
                            ("canceled", "Canceled"),
                        ],
                        db_index=True,
                        default="requested",
                        max_length=32,
                    ),
                ),
                ("provider", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                (
                    "provider_refund_id",
                    models.CharField(blank=True, db_index=True, default="", max_length=128),
                ),
                ("idempotency_key", models.CharField(db_index=True, max_length=128)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("settled_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="canonical_refunds_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="refunds",
                        to="payments.payment",
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
                "indexes": [
                    models.Index(fields=["school_id", "status"], name="payments_re_school__2b527e_idx"),
                    models.Index(fields=["payment", "status"], name="payments_re_payment_4444a0_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_cents__gt", 0)),
                        name="payments_refund_amount_positive",
                    ),
                    models.UniqueConstraint(
                        fields=("school_id", "idempotency_key"),
                        name="uq_payments_refund_school_idempotency",
                    ),
                    models.UniqueConstraint(
                        condition=~models.Q(("provider", ""))
                        & ~models.Q(("provider_refund_id", "")),
                        fields=("provider", "provider_refund_id"),
                        name="uq_payments_refund_provider_refund",
                    ),
                ],
            },
        ),
    ]
