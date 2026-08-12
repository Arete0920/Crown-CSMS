from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journal", "0002_journalentry_reversal_of"),
    ]

    operations = [
        migrations.AddField(
            model_name="journalentry",
            name="correlation_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="currency",
            field=models.CharField(default="USD", max_length=8),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="source_system",
            field=models.CharField(default="journal", max_length=100),
        ),
    ]
