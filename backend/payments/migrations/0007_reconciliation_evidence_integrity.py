import django.db.models.deletion
from django.db import migrations, models


ACTIVE_MATCH_STATUSES = ["auto_matched", "manual_matched"]


def assert_no_active_match_reuse(apps, schema_editor):
    PayoutBankMatch = apps.get_model("payments", "PayoutBankMatch")

    payout_duplicates = list(
        PayoutBankMatch.objects.filter(status__in=ACTIVE_MATCH_STATUSES)
        .values("payout_batch_id")
        .annotate(match_count=models.Count("id"))
        .filter(match_count__gt=1)
        .order_by("payout_batch_id")[:20]
    )
    bank_duplicates = list(
        PayoutBankMatch.objects.filter(status__in=ACTIVE_MATCH_STATUSES)
        .values("bank_entry_id")
        .annotate(match_count=models.Count("id"))
        .filter(match_count__gt=1)
        .order_by("bank_entry_id")[:20]
    )

    if payout_duplicates or bank_duplicates:
        raise RuntimeError(
            "Cannot enforce reconciliation one-to-one integrity: existing active "
            f"matches reuse payout batches or bank entries. payout_duplicates={payout_duplicates}; "
            f"bank_duplicates={bank_duplicates}. Reconcile these records explicitly before retrying."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0006_canonical_compatibility_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatementimport",
            name="source_sha256",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
        migrations.AlterField(
            model_name="bankstatemententry",
            name="statement_import",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="entries",
                to="payments.bankstatementimport",
            ),
        ),
        migrations.AlterField(
            model_name="payoutbankmatch",
            name="bank_entry",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payout_matches",
                to="payments.bankstatemententry",
            ),
        ),
        migrations.AlterField(
            model_name="payoutbankmatch",
            name="payout_batch",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bank_matches",
                to="payments.providerpayoutbatch",
            ),
        ),
        migrations.AlterField(
            model_name="providerpayoutentry",
            name="batch",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="entries",
                to="payments.providerpayoutbatch",
            ),
        ),
        migrations.AddConstraint(
            model_name="bankstatementimport",
            constraint=models.UniqueConstraint(
                fields=("school_id", "source_sha256"),
                condition=~models.Q(source_sha256=""),
                name="uq_bank_statement_import_school_hash",
            ),
        ),
        migrations.RunPython(
            assert_no_active_match_reuse,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="payoutbankmatch",
            constraint=models.UniqueConstraint(
                fields=("payout_batch",),
                condition=models.Q(status__in=ACTIVE_MATCH_STATUSES),
                name="uq_active_payout_bank_match_payout",
            ),
        ),
        migrations.AddConstraint(
            model_name="payoutbankmatch",
            constraint=models.UniqueConstraint(
                fields=("bank_entry",),
                condition=models.Q(status__in=ACTIVE_MATCH_STATUSES),
                name="uq_active_payout_bank_match_bank",
            ),
        ),
    ]
