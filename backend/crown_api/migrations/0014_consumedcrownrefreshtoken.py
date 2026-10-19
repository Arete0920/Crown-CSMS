from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crown_api", "0013_attendance_section"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsumedCrownRefreshToken",
            fields=[
                (
                    "token_id",
                    models.CharField(max_length=128, primary_key=True, serialize=False),
                ),
                ("consumed_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
