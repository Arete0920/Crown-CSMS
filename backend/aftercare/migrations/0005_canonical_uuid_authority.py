import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0004_alter_aftercareincident_discipline_record_id"),
        ("core", "0013_student_identity_link"),
        ("households", "0010_student_account"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aftercareprogramconfig",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="aftercareprogramconfig",
            name="school_fk",
            field=models.OneToOneField(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_program_config",
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareenrollment",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareenrollment",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareenrollment",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_enrollments",
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareenrollment",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="student_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_enrollments",
                to="households.student",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareattendance",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareattendance",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareattendance",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_attendance",
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareattendance",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="student_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_attendance",
                to="households.student",
            ),
        ),
        migrations.AddConstraint(
            model_name="aftercareattendance",
            constraint=models.UniqueConstraint(
                condition=models.Q(("school_fk__isnull", False), ("student_fk__isnull", False)),
                fields=("school_fk", "student_fk", "date"),
                name="aftercare_attendance_canonical_unique",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareincident",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareincident",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercareincident",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_incidents",
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="aftercareincident",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="student_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_incidents",
                to="households.student",
            ),
        ),
        migrations.AlterField(
            model_name="aftercarepickupcontact",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="aftercarepickupcontact",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="aftercarepickupcontact",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_pickup_contacts",
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="aftercarepickupcontact",
            name="student_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="student_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_pickup_contacts",
                to="households.student",
            ),
        ),
        migrations.AlterField(
            model_name="aftercaremonthlychargerun",
            name="school_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="aftercaremonthlychargerun",
            name="school_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="school_uuid_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aftercare_monthly_charge_runs",
                to="core.school",
            ),
        ),
        migrations.AddConstraint(
            model_name="aftercaremonthlychargerun",
            constraint=models.UniqueConstraint(
                condition=models.Q(("school_fk__isnull", False)),
                fields=("school_fk", "year", "month"),
                name="aftercare_monthly_charge_canonical_unique",
            ),
        ),
    ]
