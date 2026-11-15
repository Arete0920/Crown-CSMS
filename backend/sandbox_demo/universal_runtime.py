"""Default-off, exact-revision runtime authority for an owned Arete presenter."""
import os
from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection


def require_hosted_presenter(expected_sha):
    # Reuse the reviewed existing DEV/source/closed-session guard. This is
    # provisioning authority only when a separately authorized owner enables
    # BOTH the feature and this exact immutable revision on existing DEV.
    from .management.commands.provision_hosted_buyer_workspace import _require_existing_dev_runtime
    _require_existing_dev_runtime(expected_sha)
    db = connection.settings_dict
    if (
        getattr(settings, "CROWN_UNIVERSAL_PRESENTER_ENABLED", False) is not True
        or getattr(settings, "CROWN_UNIVERSAL_PRESENTER_APPROVED_SHA", "") != expected_sha
        or not db.get("NAME")
        or not str(db.get("HOST", "")).lower().endswith(".postgres.database.azure.com")
        or not (getattr(settings, "CROWN_SANDBOX_OUTBOUND_DISABLED", False) is True
                or os.environ.get("CROWN_SANDBOX_OUTBOUND_DISABLED", "").strip().lower() in {"1", "true", "yes", "on"})
        or any(str(value or "").strip().lower() not in {"", "dev", "development"}
               for key in ("CROWN_ENV", "DJANGO_ENV", "AZURE_ENVIRONMENT", "ENVIRONMENT", "APP_ENV")
               for value in (os.environ.get(key), getattr(settings, key, None)))
    ):
        raise CommandError("Exact owner-enabled existing DEV presenter revision, Azure PostgreSQL and disabled outbound delivery required.")


def require_presenter_runtime():
    if getattr(settings, "CROWN_ENV", "") == "local":
        from .universal_demo import require_local_presenter
        require_local_presenter()
    else:
        require_hosted_presenter(str(getattr(settings, "BUILD_SHA", "") or ""))
