from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_backfill_household_family_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="RetentionPurgeAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("run_id", models.UUIDField(db_index=True)),
                ("model_name", models.CharField(db_index=True, max_length=100)),
                ("retention_days", models.IntegerField(default=0)),
                ("legal_hold", models.BooleanField(default=False)),
                ("deleted_count", models.IntegerField(default=0)),
                ("skipped_reason", models.CharField(blank=True, default="", max_length=255)),
                ("policy_snapshot", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Retention Purge Audit",
                "verbose_name_plural": "Retention Purge Audits",
                "ordering": ["-created_at", "model_name"],
            },
        ),
    ]
