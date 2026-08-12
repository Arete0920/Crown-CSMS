import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journal", "0003_accounting_traceability_contract"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="journalentry",
            name="posting_date",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.CreateModel(
            name="AccountingPeriod",
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
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("OPEN", "Open"), ("CLOSED", "Closed")],
                        default="OPEN",
                        max_length=16,
                    ),
                ),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("reopened_at", models.DateTimeField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "closed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accounting_periods_closed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reopened_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accounting_periods_reopened",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accounting_periods",
                        to="core.school",
                    ),
                ),
            ],
            options={
                "db_table": "journal_accounting_period",
                "ordering": ["school_id", "start_date"],
            },
        ),
        migrations.AddConstraint(
            model_name="accountingperiod",
            constraint=models.UniqueConstraint(
                fields=("school", "start_date", "end_date"),
                name="journal_unique_accounting_period_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="accountingperiod",
            constraint=models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="journal_accounting_period_valid_range",
            ),
        ),
        migrations.AddIndex(
            model_name="accountingperiod",
            index=models.Index(
                fields=["school", "start_date", "end_date"],
                name="journal_acc_school__98cc1d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="accountingperiod",
            index=models.Index(
                fields=["school", "status"],
                name="journal_acc_school__805c67_idx",
            ),
        ),
    ]
