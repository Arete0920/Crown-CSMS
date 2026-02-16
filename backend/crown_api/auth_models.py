# backend/crown_api/auth_models.py
import uuid
from django.db import models


class CrownUser(models.Model):
    """
    Minimal auth user model for Crown JWT auth.
    We are NOT replacing django.contrib.auth.User yet (fastest path).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=256)

    # Tenant + role
    school_id = models.UUIDField(null=True, blank=True, db_index=True)
    role = models.CharField(max_length=50, db_index=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"
