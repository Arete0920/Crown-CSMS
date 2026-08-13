from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling_wizard", "0001_initial"),
        ("academics", "0039_term_uniq_term_year_code"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedulingwizardsession",
            name="academic_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="scheduling_wizard_sessions",
                to="core.academicyear",
            ),
        ),
        migrations.AddField(
            model_name="schedulingwizardsession",
            name="term_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="scheduling_wizard_sessions",
                to="academics.term",
            ),
        ),
    ]
