"""Explicit local fictional SGO family grants and revisioned case intake."""
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


GRADES = [(str(i), str(i)) for i in range(1, 13)] + [("K", "Kindergarten")]
REASONS = [
    ("GRADE_UNVERIFIED", "Grade not verified"),
    ("PROGRAM_DETAIL_MISMATCH", "Program details need verification"),
    ("OTHER_NON_SENSITIVE", "Other non-sensitive correction"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("jireh_sgo", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="sgoauditevent",
            name="action",
            field=models.CharField(
                max_length=70,
                choices=[
                    ("PROGRAM_CREATED", "PROGRAM_CREATED"),
                    ("APPLICATION_CREATED", "APPLICATION_CREATED"),
                    ("ELIGIBILITY_ATTESTED", "ELIGIBILITY_ATTESTED"),
                    ("AWARD_COMMITTED_NONCASH", "AWARD_COMMITTED_NONCASH"),
                    ("AWARD_CANCELLED_NONCASH", "AWARD_CANCELLED_NONCASH"),
                    ("INTAKE_SUBMITTED", "INTAKE_SUBMITTED"),
                    ("INTAKE_CORRECTION_REQUESTED", "INTAKE_CORRECTION_REQUESTED"),
                    ("INTAKE_RESUBMITTED", "INTAKE_RESUBMITTED"),
                ],
            ),
        ),
        migrations.CreateModel(
            name="SGOFamilyGrant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("student_key", models.UUIDField()),
                ("school_key", models.UUIDField()),
                ("consent_version", models.CharField(max_length=80)),
                ("active", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("program", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="family_grants", to="jireh_sgo.sgoprogram",
                )),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="+", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=["program", "student_key"], name="unique_sgo_family_grant"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SGOProcessorAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("active", models.BooleanField(default=False)),
                ("program", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="processors", to="jireh_sgo.sgoprogram",
                )),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="+", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=["program", "user"], name="unique_sgo_processor_assignment",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="SGOFamilyIntake",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("grade_level", models.CharField(max_length=2, choices=GRADES)),
                ("initial_grade_level", models.CharField(max_length=2, choices=GRADES)),
                ("status", models.CharField(
                    max_length=24, default="SUBMITTED",
                    choices=[("SUBMITTED", "Submitted"),
                             ("CORRECTION_REQUESTED", "Correction requested"),
                             ("RESUBMITTED", "Resubmitted")],
                )),
                ("consent_version", models.CharField(max_length=80)),
                ("consented_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("revision", models.PositiveIntegerField(default=1)),
                ("submission_key", models.UUIDField(unique=True)),
                ("requested_reason", models.CharField(max_length=32, blank=True, choices=REASONS)),
                ("last_processor_key", models.UUIDField(blank=True, null=True, unique=True)),
                ("last_correction_key", models.UUIDField(blank=True, null=True, unique=True)),
                ("application", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="family_intake", to="jireh_sgo.sgoapplication",
                )),
                ("grant", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="intake", to="jireh_sgo.sgofamilygrant",
                )),
            ],
        ),
    ]
