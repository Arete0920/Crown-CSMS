# Generated manually for Microsoft Entra immutable identity binding.
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_seed_summer_camp_permissions"),
        ("integrations", "0002_teamspreviewaudit"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MicrosoftTenantBinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("display_name", models.CharField(blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="microsoft_tenant_bindings",
                        to="core.school",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant_id", "is_active"], name="integration_tenant__ee9b98_idx"),
                    models.Index(fields=["school", "is_active"], name="integration_school__67d95b_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("school", "tenant_id"), name="uniq_microsoft_school_tenant"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MicrosoftIdentityLink",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("object_id", models.UUIDField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "binding",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="identity_links",
                        to="integrations.microsofttenantbinding",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="microsoft_identity_links",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["object_id", "is_active"], name="integration_object__8e587f_idx"),
                    models.Index(fields=["user", "is_active"], name="integration_user_id_635f6e_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("binding", "object_id"), name="uniq_microsoft_binding_object"),
                    models.UniqueConstraint(fields=("binding", "user"), name="uniq_microsoft_binding_user"),
                ],
            },
        ),
    ]
