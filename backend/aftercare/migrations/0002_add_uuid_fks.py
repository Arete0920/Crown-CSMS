"""
0002_add_uuid_fks

Add nullable ForeignKey fields (school_fk, student_fk) to AftercareEnrollment,
AftercareAttendance, and AftercareIncident.

Named with _fk suffix to avoid column clash: Django auto-creates <name>_id for
ForeignKey, and these models already have explicit school_id / student_id
IntegerFields.  The explicit db_column directs the DB column to school_uuid_id /
student_uuid_id so there is no collision at the database level either.

The signals engine and seed_demo command write to both integer columns (legacy)
and the new FK columns (UUID joins).
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aftercare", "0001_initial"),
        ("core", "0005_crown_permission_engine"),
        ("households", "0008_households_guardians_students"),
    ]

    operations = [
        # ---- AftercareEnrollment ----------------------------------------- #
        migrations.AddField(
            model_name="aftercareenrollment",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_enrollments",
                to="core.school",
                db_column="school_uuid_id",
            ),
        ),
        migrations.AddField(
            model_name="aftercareenrollment",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_enrollments",
                to="households.student",
                db_column="student_uuid_id",
            ),
        ),
        # ---- AftercareAttendance ----------------------------------------- #
        migrations.AddField(
            model_name="aftercareattendance",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_attendance",
                to="core.school",
                db_column="school_uuid_id",
            ),
        ),
        migrations.AddField(
            model_name="aftercareattendance",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_attendance",
                to="households.student",
                db_column="student_uuid_id",
            ),
        ),
        # ---- AftercareIncident ------------------------------------------- #
        migrations.AddField(
            model_name="aftercareincident",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_incidents",
                to="core.school",
                db_column="school_uuid_id",
            ),
        ),
        migrations.AddField(
            model_name="aftercareincident",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aftercare_incidents",
                to="households.student",
                db_column="student_uuid_id",
            ),
        ),
    ]
