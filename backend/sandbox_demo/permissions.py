from __future__ import annotations

from django.db import transaction

from core.management.commands.seed_permissions import PERMISSIONS, ROLE_PERMISSIONS
from core.models import CrownPermission, RolePermission


_PERMISSION_DESCRIPTIONS = dict(PERMISSIONS)


@transaction.atomic
def ensure_sandbox_role_permissions(role_code: str) -> None:
    """Ensure the canonical permission registry exists for a sandbox persona role.

    Passwordless Heritage sessions can be created in environments where the global
    permission seed has not been run recently. Reuse the authoritative registry
    rather than weakening permission checks or maintaining a sandbox-only mapping.
    """

    for permission_code in ROLE_PERMISSIONS.get(role_code, []):
        permission, _ = CrownPermission.objects.get_or_create(
            code=permission_code,
            defaults={"description": _PERMISSION_DESCRIPTIONS.get(permission_code, "")},
        )
        RolePermission.objects.get_or_create(
            role_code=role_code,
            permission=permission,
        )
