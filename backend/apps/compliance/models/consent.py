from django.conf import settings
from django.db import models


class ConsentAudit(models.Model):
    CONSENT_TYPES = [
        ("privacy_policy", "Privacy Policy"),
        ("school_authorization", "School Authorization"),
        ("parental_consent", "Parental Consent"),
        ("faith_data_acknowledgement", "Faith Data Acknowledgement"),
    ]

    tenant_id = models.CharField(max_length=64)
    consent_type = models.CharField(max_length=64, choices=CONSENT_TYPES)

    version = models.CharField(max_length=32)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]

    def __str__(self):
        return f"{self.consent_type} - {self.tenant_id}"
