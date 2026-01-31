from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FinancialAidApplication",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("household_id", models.UUIDField(db_index=True)),
                ("academic_year", models.CharField(max_length=9, db_index=True)),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("household_income", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("household_size", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(
                    max_length=20,
                    default="submitted",
                    db_index=True,
                    choices=[
                        ("draft", "Draft"),
                        ("submitted", "Submitted"),
                        ("in_review", "In Review"),
                        ("decided", "Decided"),
                    ],
                )),
            ],
        ),
        migrations.CreateModel(
            name="AidAward",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("bucket", models.CharField(
                    max_length=20,
                    db_index=True,
                    null=True,
                    blank=True,
                    choices=[
                        ("need", "Need-Based"),
                        ("mission", "Mission-Driven"),
                        ("marketing", "Marketing/Enrollment"),
                        ("merit", "Merit-Based"),
                        ("hardship", "Hardship/Crisis"),
                    ],
                )),
                ("amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("rationale", models.TextField(blank=True, default="")),
                ("approved_by_user_id", models.UUIDField(null=True, blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.ForeignKey(
                    to="financial_aid.financialaidapplication",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="awards",
                    null=True,
                    blank=True,
                )),
            ],
        ),
        migrations.CreateModel(
            name="AidAuditEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("event_type", models.CharField(max_length=50, db_index=True)),
                ("entity_type", models.CharField(max_length=50, db_index=True)),
                ("entity_id", models.UUIDField(db_index=True)),
                ("actor_user_id", models.UUIDField(null=True, blank=True)),
                ("message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
