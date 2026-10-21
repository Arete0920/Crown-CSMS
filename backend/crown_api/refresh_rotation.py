"""Serialize refresh-token rotation to reject concurrent replay on PostgreSQL.

RefreshToken.validate() checks the blacklist before revocation; without a
per-token database lock, two refresh calls may both pass the initial check.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings



class SerializedTokenRefreshSerializer(TokenRefreshSerializer):
    """Recheck revocation under a row lock before rotating the refresh token."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        # Django cannot load blacklist models before the app is installed.
        # This serializer is selected only after schema-first activation.
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        # Decode and verify signature, expiry, token type, and current blacklist.
        current = self.token_class(attrs["refresh"])

        # Existing tokens issued before blacklist activation may lack an
        # OutstandingToken row. Create it in the same transaction as rotation.
        with transaction.atomic():
            current.outstand()
            OutstandingToken.objects.select_for_update().only("id").get(
                jti=current[api_settings.JTI_CLAIM]
            )

            # The first verification ran before acquiring the lock. Recheck
            # after the preceding request commits its blacklist entry.
            current.check_blacklist()

            # Vendor validation revokes the old token and creates the new one.
            # Commit both writes together; any failure rolls back both.
            return super().validate(attrs)
