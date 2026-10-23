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


class LegacyRefreshConsumption(models.Model):
    """One-time consumption ledger for signed legacy Crown refresh tokens."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CrownUser, on_delete=models.CASCADE, related_name="consumed_refresh_tokens")
    token_digest = models.CharField(max_length=64, unique=True)
    consumed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-consumed_at"]
