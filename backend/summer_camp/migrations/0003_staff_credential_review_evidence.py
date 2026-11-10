"""Require an attributable, evidence-referenced camp staff clearance for readiness."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summer_camp", "0002_pickup_verification_actor"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="summercampstaffassignment",
            name="credential_status",
            field=models.CharField(
                max_length=64,
                default="PENDING",
                choices=[
                    ("PENDING", "Pending review"),
                    ("VERIFIED", "Verified"),
                    ("REVOKED", "Revoked"),
                ],
            ),
        ),
        migrations.AddField(
            model_name="summercampstaffassignment",
            name="credential_verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="summer_camp_staff_credentials_verified",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="summercampstaffassignment",
            name="credential_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="summercampstaffassignment",
            name="credential_evidence_ref",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
    ]
