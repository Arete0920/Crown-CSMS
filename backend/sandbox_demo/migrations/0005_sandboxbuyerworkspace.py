"""Reserved buyer workspace bindings; historical invites are never backfilled."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sandbox_demo", "0004_delete_sandboxaccessrequest"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SandboxBuyerWorkspace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_sha", models.CharField(max_length=40)),
                ("provisioned_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "invite",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="buyer_workspace",
                        to="sandbox_demo.sandboxinvite",
                    ),
                ),
                (
                    "school",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="buyer_sandbox_workspace",
                        to="core.school",
                    ),
                ),
            ],
        ),
    ]
