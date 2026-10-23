"""Persist one-time consumption of legacy signed Crown refresh tokens."""
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crown_api", "0013_attendance_section"),
    ]

    operations = [
        migrations.CreateModel(
            name="LegacyRefreshConsumption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token_digest", models.CharField(max_length=64, unique=True)),
                ("consumed_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="consumed_refresh_tokens",
                    to="crown_api.crownuser",
                )),
            ],
            options={"ordering": ["-consumed_at"]},
        ),
    ]
