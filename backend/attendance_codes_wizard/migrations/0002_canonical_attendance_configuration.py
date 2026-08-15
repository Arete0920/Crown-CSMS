import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("attendance_codes_wizard", "0001_initial"),
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceConfiguration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_year", models.CharField(max_length=24)),
                ("label", models.CharField(default="Attendance Policy", max_length=128)),
                ("policy_config", models.JSONField(default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_configurations", to="core.school")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_configurations_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["school_id", "school_year"]},
        ),
        migrations.CreateModel(
            name="AttendanceCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=8)),
                ("label", models.CharField(max_length=128)),
                ("excused", models.BooleanField(default=False)),
                ("counts_as_tardy", models.BooleanField(default=False)),
                ("counts_as_absent", models.BooleanField(default=False)),
                ("notify_guardian", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("configuration", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="codes", to="attendance_codes_wizard.attendanceconfiguration")),
            ],
            options={"ordering": ["configuration_id", "code"]},
        ),
        migrations.AddConstraint(
            model_name="attendanceconfiguration",
            constraint=models.UniqueConstraint(fields=("school", "school_year"), name="uniq_attendance_config_school_year"),
        ),
        migrations.AddConstraint(
            model_name="attendancecode",
            constraint=models.UniqueConstraint(fields=("configuration", "code"), name="uniq_attendance_code_per_configuration"),
        ),
    ]
