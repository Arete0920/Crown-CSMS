from django.db import migrations, models


def assert_no_legacy_integer_identity_rows(apps, schema_editor):
    model_names = [
        "HomeAcademyProgram",
        "HomeAcademyEnrollment",
        "Offering",
        "OfferingEnrollment",
        "FinancialAidRule",
    ]
    legacy_rows = []
    for name in model_names:
        model = apps.get_model("home_academy", name)
        if model.objects.exists():
            legacy_rows.append(name)
    if legacy_rows:
        joined = ", ".join(legacy_rows)
        raise RuntimeError(
            "Home Academy UUID migration blocked because legacy rows exist in: "
            f"{joined}. Reconcile legacy integer identifiers to canonical UUID "
            "School/Student records before retrying the migration."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("home_academy", "0002_rename_home_acade_school__0e7bb3_idx_home_academ_school__269e9e_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(assert_no_legacy_integer_identity_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="homeacademyprogram",
            name="school_id",
            field=models.UUIDField(db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="school_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="student_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="household_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="advisor_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="registrar_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="offering",
            name="school_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name="offering",
            name="staff_owner_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="offeringenrollment",
            name="school_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name="offeringenrollment",
            name="student_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="finance_obligation_id",
            field=models.PositiveBigIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="offering",
            name="academic_course_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="offering",
            name="academic_term_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="transcript_entry_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="final_letter_grade",
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="final_percentage",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="aid_eligible",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="offeringenrollment",
            name="financial_aid_rule_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="financialaidrule",
            name="school_id",
            field=models.UUIDField(db_index=True),
        ),
    ]
