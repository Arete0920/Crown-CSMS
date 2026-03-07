"""
0002_rebuild_uuid_fks

Full rebuild: drop the original IntegerField-based signals tables and
recreate them with UUID primary keys and proper ForeignKey references
to core.School (UUID PK) and households.Student (UUID PK).

This is a destructive migration.  In production these tables should be
empty (the signals engine populates them via a nightly cron or on-demand
compute call) so no data migration is required.  In development / CI just
apply; demo data is seeded by the seed_demo management command.
"""

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("signals", "0001_initial"),
        ("core", "0005_crown_permission_engine"),
        ("households", "0008_households_guardians_students"),
    ]

    operations = [
        # ------------------------------------------------------------------ #
        # Drop the six original IntegerField-based models                     #
        # ------------------------------------------------------------------ #
        migrations.DeleteModel(name="BoardExecutiveMetric"),
        migrations.DeleteModel(name="InterventionAction"),
        migrations.DeleteModel(name="InterventionCase"),
        migrations.DeleteModel(name="SignalDefinition"),
        migrations.DeleteModel(name="SignalEvent"),
        migrations.DeleteModel(name="StudentRiskSnapshot"),

        # ------------------------------------------------------------------ #
        # Recreate with UUID PK + proper FK references                        #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name="SignalDefinition",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="signal_definitions",
                    to="core.school",
                )),
                ("key", models.SlugField(max_length=64)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("severity_weight", models.IntegerField(default=10)),
                ("is_active", models.BooleanField(default=True)),
                ("rule", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "unique_together": {("school", "key")},
                "indexes": [models.Index(fields=["school", "is_active"], name="signals_sig2_school_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="StudentRiskSnapshot",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="risk_snapshots",
                    to="core.school",
                )),
                ("student", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="risk_snapshots",
                    to="households.student",
                )),
                ("as_of_date", models.DateField(db_index=True)),
                ("risk_score", models.IntegerField(default=0)),
                ("risk_level", models.CharField(max_length=12, default="LOW")),
                ("drivers", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "unique_together": {("school", "student", "as_of_date")},
                "indexes": [
                    models.Index(fields=["school", "as_of_date", "risk_level"], name="signals_rsk2_date_lvl_idx"),
                    models.Index(fields=["school", "student"], name="signals_rsk2_school_stu_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SignalEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="signal_events",
                    to="core.school",
                )),
                ("student", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="signal_events",
                    to="households.student",
                )),
                ("signal_key", models.SlugField(max_length=64, db_index=True)),
                ("weight", models.IntegerField(default=10)),
                ("summary", models.CharField(max_length=200)),
                ("details", models.JSONField(default=dict)),
                ("fired_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["school", "student", "fired_at"], name="signals_evt2_stu_date_idx"),
                    models.Index(fields=["school", "signal_key", "fired_at"], name="signals_evt2_key_date_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="InterventionCase",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="intervention_cases",
                    to="core.school",
                )),
                ("student", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="intervention_cases",
                    to="households.student",
                )),
                ("opened_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(max_length=16, default="OPEN")),
                ("priority", models.CharField(max_length=12, default="MED")),
                ("reason", models.CharField(max_length=200)),
                ("linked_signals", models.JSONField(default=list)),
                ("owner_user_id", models.IntegerField(blank=True, null=True)),
                ("last_action_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["school", "status", "priority"], name="signals_ic2_status_pri_idx"),
                    models.Index(fields=["school", "student", "status"], name="signals_ic2_stu_status_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="InterventionAction",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="intervention_actions",
                    to="core.school",
                )),
                ("case", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="actions",
                    to="signals.interventioncase",
                )),
                ("action_type", models.CharField(max_length=24, default="NOTE")),
                ("note", models.TextField()),
                ("created_by_user_id", models.IntegerField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["school", "case", "created_at"], name="signals_ia2_case_date_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="BoardExecutiveMetric",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("school", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="board_metrics",
                    to="core.school",
                )),
                ("as_of_date", models.DateField(db_index=True)),
                ("enrollment_health", models.IntegerField(default=0)),
                ("financial_health", models.IntegerField(default=0)),
                ("culture_health", models.IntegerField(default=0)),
                ("mission_health", models.IntegerField(default=0)),
                ("retention_risk", models.IntegerField(default=0)),
                ("highlights", models.JSONField(default=list)),
                ("watchlist", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "unique_together": {("school", "as_of_date")},
                "indexes": [
                    models.Index(fields=["school", "as_of_date"], name="signals_bem2_date_idx"),
                ],
            },
        ),
    ]
