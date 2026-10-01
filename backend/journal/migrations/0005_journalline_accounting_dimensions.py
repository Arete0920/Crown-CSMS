from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0004_accounting_period_controls"),
    ]

    operations = [
        migrations.AddField(model_name="journalline", name="fund_code", field=models.CharField(blank=True, default="", max_length=32)),
        migrations.AddField(model_name="journalline", name="department_code", field=models.CharField(blank=True, default="", max_length=32)),
        migrations.AddField(model_name="journalline", name="program_code", field=models.CharField(blank=True, default="", max_length=32)),
        migrations.AddField(model_name="journalline", name="campus_code", field=models.CharField(blank=True, default="", max_length=32)),
        migrations.AddField(model_name="journalline", name="project_code", field=models.CharField(blank=True, default="", max_length=32)),
        migrations.AddIndex(
            model_name="journalline",
            index=models.Index(fields=["account", "fund_code"], name="journal_line_account_fund_idx"),
        ),
    ]
