from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0011_application_checklist_access_key_and_more"),
        ("electronic_forms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="enrollmentcontract",
            name="electronic_envelope",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="enrollment_contracts",
                to="electronic_forms.electronicenvelope",
            ),
        ),
    ]
