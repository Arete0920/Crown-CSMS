from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0006_align_canonical_index_names"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="aftercareprogramconfig",
            name="before_start_time",
            field=models.TimeField(default="07:00"),
        ),
        migrations.AddField(
            model_name="aftercareprogramconfig",
            name="before_end_time",
            field=models.TimeField(default="08:30"),
        ),
        migrations.AddField(
            model_name="aftercareenrollment",
            name="care_session",
            field=models.CharField(
                choices=[("AM", "Before Care"), ("PM", "After Care")],
                db_index=True, default="PM", max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="aftercareattendance",
            name="care_session",
            field=models.CharField(
                choices=[("AM", "Before Care"), ("PM", "After Care")],
                db_index=True, default="PM", max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="aftercareattendance",
            name="handoff_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="aftercareattendance",
            name="handoff_recipient",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="extended_care_handoffs_received",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="aftercareattendance",
            name="handoff_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name="aftercareattendance",
            unique_together={("school_id", "student_id", "date", "care_session")},
        ),
        migrations.RemoveConstraint(
            model_name="aftercareattendance",
            name="aftercare_attendance_canonical_unique",
        ),
        migrations.AddConstraint(
            model_name="aftercareattendance",
            constraint=models.UniqueConstraint(
                condition=models.Q(school_fk__isnull=False, student_fk__isnull=False),
                fields=("school_fk", "student_fk", "date", "care_session"),
                name="aftercare_attendance_canonical_session_unique",
            ),
        ),
    ]
