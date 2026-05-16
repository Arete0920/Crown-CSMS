import uuid

from django.db import models


class AccountingAuditLog(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tenant_id = models.UUIDField(db_index=True)

    actor_id = models.UUIDField()

    action = models.CharField(max_length=255)

    object_type = models.CharField(max_length=255)

    object_id = models.CharField(max_length=255)

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
