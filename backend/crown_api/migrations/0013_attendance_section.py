from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crown_api", "0012_dashboard_snapshot"),
        ("academics", "0039_term_uniq_term_year_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendancerecord",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="attendance_records",
                to="academics.section",
            ),
        ),
        migrations.AddConstraint(
            model_name="attendancerecord",
            constraint=models.UniqueConstraint(
                condition=models.Q(("section__isnull", False)),
                fields=("student", "section", "date"),
                name="uniq_attendance_student_section_date",
            ),
        ),
    ]
