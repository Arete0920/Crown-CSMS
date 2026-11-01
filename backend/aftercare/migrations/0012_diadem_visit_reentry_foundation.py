"""Versioned Diadem custody visits; no new check-in or release routes enabled.

All existing attendance rows retain visit_number=1. The former single-day
constraint is replaced by a visit-scoped key; services continue rejecting
repeat same-day admissions until a separately reviewed authorization flow.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0011_aftercare_pickup_verified_by"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="daycareattendance", name="visit_number",
            field=models.PositiveIntegerField(default=1, editable=False),
        ),
        migrations.CreateModel(
            name="DaycareReentryAuthorization",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("care_date", models.DateField()),
                ("reason_code", models.CharField(max_length=24, choices=[
                    ("SCHEDULED_RETURN", "Scheduled same-day return"),
                    ("DIRECTOR_REVIEWED", "Director-reviewed same-day exception"),
                ])),
                ("approved_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                ("request_key", models.UUIDField(default=uuid.uuid4)),
                ("school", models.ForeignKey(to="core.school", on_delete=django.db.models.deletion.PROTECT)),
                ("site", models.ForeignKey(to="aftercare.daycaresite", on_delete=django.db.models.deletion.PROTECT, related_name="reentry_authorizations")),
                ("child", models.ForeignKey(to="aftercare.daycarechild", on_delete=django.db.models.deletion.PROTECT, related_name="reentry_authorizations")),
                ("previous_attendance", models.ForeignKey(to="aftercare.daycareattendance", on_delete=django.db.models.deletion.PROTECT, related_name="subsequent_reentry_authorizations")),
                ("director", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT, related_name="diadem_reentry_authorizations")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=["school", "request_key"], name="dia_reentry_request_uq"),
                    models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("approved_at")), name="dia_reentry_window_ck"),
                ],
                "indexes": [models.Index(fields=["school", "child", "care_date"], name="dia_reentry_child_day_idx")],
            },
        ),
        migrations.AddField(
            model_name="daycareattendance", name="reentry_approval",
            field=models.OneToOneField(to="aftercare.daycarereentryauthorization",
                on_delete=django.db.models.deletion.PROTECT, null=True, blank=True,
                related_name="admitted_visit"),
        ),
        migrations.RemoveConstraint(model_name="daycareattendance", name="dia_attendance_child_day_uq"),
        migrations.AddConstraint(
            model_name="daycareattendance",
            constraint=models.UniqueConstraint(
                fields=["school", "child", "care_date", "visit_number"],
                name="dia_attendance_visit_uq",
            ),
        ),
    ]
