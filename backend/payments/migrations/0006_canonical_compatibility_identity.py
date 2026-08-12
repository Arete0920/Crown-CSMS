from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0005_payment_refund"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(
                fields=("finance_payment_id",),
                condition=models.Q(finance_payment_id__isnull=False),
                name="uq_payments_payment_finance_payment",
            ),
        ),
        migrations.AddConstraint(
            model_name="refund",
            constraint=models.UniqueConstraint(
                fields=("finance_refund_id",),
                condition=models.Q(finance_refund_id__isnull=False),
                name="uq_payments_refund_finance_refund",
            ),
        ),
    ]
