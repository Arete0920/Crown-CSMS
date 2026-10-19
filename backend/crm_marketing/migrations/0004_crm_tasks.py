"""Staged additive CRM task schema; not an accepted migration until governed integration."""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("crm_marketing", "0003_prospect_relationships")]

    operations = [
        migrations.CreateModel(
            name="CRMTask",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("title", models.CharField(max_length=160)),
                ("kind", models.CharField(max_length=24, default="other", choices=[("call","Phone call"),("tour","Tour follow-up"),("application","Application assistance"),("other","Other staff follow-up")])),
                ("state", models.CharField(max_length=20, default="open", choices=[("open","Open"),("in_progress","In progress"),("done","Completed"),("cancelled","Cancelled")])),
                ("priority", models.CharField(max_length=12, default="normal", choices=[("normal","Normal"),("high","High")])),
                ("assigned_to_user_id", models.UUIDField(null=True, blank=True)),
                ("due_at", models.DateTimeField(null=True, blank=True)),
                ("completed_at", models.DateTimeField(null=True, blank=True)),
                ("completed_by_user_id", models.UUIDField(null=True, blank=True)),
                ("created_by_user_id", models.UUIDField()),
                ("idempotency_key", models.CharField(max_length=128, null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(to="core.school", on_delete=django.db.models.deletion.CASCADE, related_name="crm_tasks")),
                ("lead", models.ForeignKey(to="crm_marketing.marketinglead", null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, related_name="crm_tasks")),
                ("group", models.ForeignKey(to="crm_marketing.prospectgroup", null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, related_name="crm_tasks")),
            ],
            options={"ordering":["due_at","created_at","id"]},
        ),
        migrations.CreateModel(
            name="CRMTaskEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("kind", models.CharField(max_length=24, choices=[("created","Created"),("assigned","Assigned"),("completed","Completed"),("reopened","Reopened"),("cancelled","Cancelled")])),
                ("actor_user_id", models.UUIDField()),
                ("from_state", models.CharField(max_length=20, blank=True, default="")),
                ("to_state", models.CharField(max_length=20, blank=True, default="")),
                ("from_assignee_id", models.UUIDField(null=True, blank=True)),
                ("to_assignee_id", models.UUIDField(null=True, blank=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("school", models.ForeignKey(to="core.school", on_delete=django.db.models.deletion.CASCADE, related_name="crm_task_events")),
                ("task", models.ForeignKey(to="crm_marketing.crmtask", on_delete=django.db.models.deletion.PROTECT, related_name="events")),
            ],
            options={"ordering":["occurred_at","id"]},
        ),
        migrations.AddIndex(model_name="crmtask", index=models.Index(fields=["school","state","due_at"], name="crm_task_state_due_idx")),
        migrations.AddIndex(model_name="crmtask", index=models.Index(fields=["school","assigned_to_user_id","state"], name="crm_task_owner_state_idx")),
        migrations.AddIndex(model_name="crmtaskevent", index=models.Index(fields=["school","task","occurred_at"], name="crm_te_school_task_time_idx")),
        migrations.AddConstraint(model_name="crmtask", constraint=models.UniqueConstraint(fields=["school","idempotency_key"], condition=models.Q(idempotency_key__isnull=False), name="crm_task_school_retry_uniq")),
        migrations.AddConstraint(model_name="crmtask", constraint=models.CheckConstraint(condition=(models.Q(state="done",completed_at__isnull=False,completed_by_user_id__isnull=False)|(~models.Q(state="done")&models.Q(completed_at__isnull=True,completed_by_user_id__isnull=True))), name="crm_task_completion_consistent")),
    ]
