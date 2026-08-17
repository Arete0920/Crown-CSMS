from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0002_add_uuid_fks"),
        ("core", "0015_seed_curriculum_permissions"),
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
            field=models.OneToOneField(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_program_config", to="core.school"),
        ),
        migrations.AlterField(model_name="aftercareenrollment", name="school_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareenrollment", name="student_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareenrollment", name="school_fk", field=models.ForeignKey(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_enrollments", to="core.school")),
        migrations.AlterField(model_name="aftercareenrollment", name="student_fk", field=models.ForeignKey(blank=True, db_column="student_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_enrollments", to="households.student")),
        migrations.AddIndex(model_name="aftercareenrollment", index=models.Index(fields=["school_fk", "is_active"], name="aftercare_e_school__c97659_idx")),
        migrations.AddIndex(model_name="aftercareenrollment", index=models.Index(fields=["school_fk", "student_fk"], name="aftercare_e_school__874184_idx")),
        migrations.AlterField(model_name="aftercarepickupcontact", name="school_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercarepickupcontact", name="student_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name="aftercarepickupcontact", name="school_fk", field=models.ForeignKey(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_pickup_contacts", to="core.school")),
        migrations.AddField(model_name="aftercarepickupcontact", name="student_fk", field=models.ForeignKey(blank=True, db_column="student_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_pickup_contacts", to="households.student")),
        migrations.AddIndex(model_name="aftercarepickupcontact", index=models.Index(fields=["school_fk", "student_fk", "is_active"], name="aftercare_p_school__458577_idx")),
        migrations.AlterField(model_name="aftercareattendance", name="school_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareattendance", name="student_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareattendance", name="school_fk", field=models.ForeignKey(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_attendance", to="core.school")),
        migrations.AlterField(model_name="aftercareattendance", name="student_fk", field=models.ForeignKey(blank=True, db_column="student_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_attendance", to="households.student")),
        migrations.AddField(model_name="aftercareattendance", name="pickup_contact_fk", field=models.ForeignKey(blank=True, db_column="pickup_contact_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="attendance_pickups", to="aftercare.aftercarepickupcontact")),
        migrations.AlterField(model_name="aftercareattendance", name="late_fee_charge_id", field=models.CharField(blank=True, max_length=64, null=True)),
        migrations.AddConstraint(model_name="aftercareattendance", constraint=models.UniqueConstraint(condition=models.Q(("school_fk__isnull", False), ("student_fk__isnull", False)), fields=("school_fk", "student_fk", "date"), name="aftercare_attendance_canonical_unique")),
        migrations.AddIndex(model_name="aftercareattendance", index=models.Index(fields=["school_fk", "date"], name="aftercare_a_school__8d2340_idx")),
        migrations.AlterField(model_name="aftercareincident", name="school_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareincident", name="student_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AlterField(model_name="aftercareincident", name="school_fk", field=models.ForeignKey(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_incidents", to="core.school")),
        migrations.AlterField(model_name="aftercareincident", name="student_fk", field=models.ForeignKey(blank=True, db_column="student_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_incidents", to="households.student")),
        migrations.AddField(model_name="aftercareincident", name="attendance_fk", field=models.ForeignKey(blank=True, db_column="attendance_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="incidents", to="aftercare.aftercareattendance")),
        migrations.AddIndex(model_name="aftercareincident", index=models.Index(fields=["school_fk", "student_fk", "occurred_at"], name="aftercare_i_school__4cb9ad_idx")),
        migrations.AddIndex(model_name="aftercareincident", index=models.Index(fields=["school_fk", "severity", "occurred_at"], name="aftercare_i_school__d41667_idx")),
        migrations.AlterField(model_name="aftercaremonthlychargerun", name="school_id", field=models.IntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name="aftercaremonthlychargerun", name="school_fk", field=models.ForeignKey(blank=True, db_column="school_uuid_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="aftercare_monthly_charge_runs", to="core.school")),
        migrations.AddConstraint(model_name="aftercaremonthlychargerun", constraint=models.UniqueConstraint(condition=models.Q(("school_fk__isnull", False)), fields=("school_fk", "year", "month"), name="aftercare_charge_run_canonical_unique")),
        migrations.AddIndex(model_name="aftercaremonthlychargerun", index=models.Index(fields=["school_fk", "year", "month"], name="aftercare_m_school__3007e1_idx")),
    ]
