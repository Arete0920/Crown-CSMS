"""Keep older application images writable after the support schema is staged."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("support", "0002_ticket_attribution"),
    ]

    operations = [
        migrations.AlterField(
            model_name="supportticket",
            name="resolution_summary",
            field=models.TextField(blank=True, default="", db_default=""),
        ),
    ]
