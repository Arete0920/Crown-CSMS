# Durable admissions request replay; tenant + key is unique across workers.
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0011_application_checklist_access_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdmissionsSubmissionReceipt",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("idempotency_key", models.CharField(max_length=256)),
                ("request_hash", models.CharField(max_length=64)),
                ("response_payload", models.JSONField(default=dict)),
            ],
            options={"db_table": "admissions_submission_receipt"},
        ),
        migrations.AddConstraint(
            model_name="admissionssubmissionreceipt",
            constraint=models.UniqueConstraint(
                fields=["school_id", "idempotency_key"],
                name="uniq_admissions_receipt_school_key",
            ),
        ),
    ]
