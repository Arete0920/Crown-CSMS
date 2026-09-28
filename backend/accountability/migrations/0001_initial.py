# Generated for Crown Student Accountability Core on 2026-09-24.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("households", "0010_student_account"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountabilityState",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("normal_state", models.CharField(choices=[
                    ("EXPECTED_ON_CAMPUS", "Expected on campus"), ("ABSENT", "Absent"),
                    ("IN_CLASS", "In class"), ("IN_TRANSIT", "In transit"),
                    ("OFFICE", "Office"), ("NURSE", "Nurse"), ("ACTIVITY", "Activity"),
                    ("ATHLETICS", "Athletics"), ("AFTERCARE", "Aftercare"),
                    ("DISMISSAL_QUEUED", "Dismissal queued"),
                    ("DISMISSAL_STAGING", "Dismissal staging"),
                    ("BUS_BOARDED", "Bus boarded"), ("RELEASED", "Released"),
                    ("KNOWN_OFF_CAMPUS", "Known off campus"),
                ], default="EXPECTED_ON_CAMPUS", max_length=40)),
                ("emergency_state", models.CharField(blank=True, choices=[
                    ("ACCOUNTED_FOR", "Accounted for"), ("NEEDS_ASSISTANCE", "Needs assistance"),
                    ("MEDICAL", "Medical"), ("LOCATION_UNCONFIRMED", "Location unconfirmed"),
                    ("RELOCATED", "Relocated"),
                    ("READY_FOR_REUNIFICATION", "Ready for reunification"),
                    ("REUNIFICATION_IN_PROGRESS", "Reunification in progress"),
                    ("REUNIFIED", "Reunified"),
                ], max_length=40, null=True)),
                ("location_code", models.CharField(blank=True, default="", max_length=120)),
                ("expected_destination", models.CharField(blank=True, default="", max_length=160)),
                ("source_domain", models.CharField(default="accountability", max_length=64)),
                ("source_record_id", models.UUIDField(blank=True, null=True)),
                ("version", models.PositiveBigIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("responsible_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="accountability_responsibilities", to=settings.AUTH_USER_MODEL)),
                ("student", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="accountability_state", to="households.student")),
            ],
        ),
        migrations.CreateModel(
            name="AccountabilityEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("event_type", models.CharField(max_length=80)),
                ("from_normal_state", models.CharField(blank=True, default="", max_length=40)),
                ("to_normal_state", models.CharField(blank=True, default="", max_length=40)),
                ("from_emergency_state", models.CharField(blank=True, default="", max_length=40)),
                ("to_emergency_state", models.CharField(blank=True, default="", max_length=40)),
                ("location_code", models.CharField(blank=True, default="", max_length=120)),
                ("source_domain", models.CharField(default="accountability", max_length=64)),
                ("source_record_id", models.UUIDField(blank=True, null=True)),
                ("context", models.JSONField(blank=True, default=dict)),
                ("state_version", models.PositiveBigIntegerField()),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("actor_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="accountability_events", to=settings.AUTH_USER_MODEL)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accountability_events", to="households.student")),
            ],
            options={"ordering": ["occurred_at", "id"]},
        ),
        migrations.AddIndex(model_name="accountabilitystate", index=models.Index(fields=["school_id", "normal_state"], name="accountabil_school__4b0a09_idx")),
        migrations.AddIndex(model_name="accountabilitystate", index=models.Index(fields=["school_id", "emergency_state"], name="accountabil_school__6316fb_idx")),
        migrations.AddIndex(model_name="accountabilitystate", index=models.Index(fields=["school_id", "updated_at"], name="accountabil_school__65ec38_idx")),
        migrations.AddIndex(model_name="accountabilityevent", index=models.Index(fields=["school_id", "student", "occurred_at"], name="accountabil_school__55f3fd_idx")),
        migrations.AddIndex(model_name="accountabilityevent", index=models.Index(fields=["school_id", "event_type", "occurred_at"], name="accountabil_school__b39435_idx")),
    ]
