import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0062_stage2_dunning_chargeback_audit"),
    ]

    operations = [
        migrations.CreateModel(
            name="Credit",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("source", models.CharField(db_index=True, max_length=32)),
                ("reference", models.CharField(db_index=True, max_length=128)),
                ("description", models.CharField(blank=True, default="", max_length=200)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_void", models.BooleanField(db_index=True, default=False)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="credits",
                        to="ledger.ledgeraccount",
                    ),
                ),
            ],
            options={
                "db_table": "student_account_credit",
                "indexes": [
                    models.Index(fields=["school_id", "account"], name="ledger_cred_school__c5bc72_idx"),
                    models.Index(fields=["school_id", "source"], name="ledger_cred_school__8a7f93_idx"),
                    models.Index(fields=["school_id", "created_at"], name="ledger_cred_school__4fbdcc_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("school_id", "source", "reference"),
                        name="uniq_student_account_credit_source_reference",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="student_account_credit_amount_positive",
                    ),
                ],
            },
        ),
    ]
