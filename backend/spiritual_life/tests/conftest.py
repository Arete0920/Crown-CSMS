from __future__ import annotations

import pytest

from core.models import CrownPermission, RolePermission, UserRole


@pytest.fixture(autouse=True)
def _legacy_spiritual_life_helpers_use_persistent_authority(request, monkeypatch):
    """Reconcile the legacy Spiritual Life suite to persistent module authority."""
    module = request.module
    original = getattr(module, "_mk_user", None)
    if original is None:
        return

    def user_with_spiritual_authority(*, school, email, is_staff=False, is_superuser=False):
        user = original(
            school=school,
            email=email,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        permission, _ = CrownPermission.objects.get_or_create(
            code="spiritual_life.view",
            defaults={"description": "View spiritual-life dashboard"},
        )
        role_code = "spiritual_life_test_operator"
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
        UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)

        # Legacy tests used Django staff to represent pastoral staff. Preserve their
        # functional intent with an explicit same-school pastoral role instead.
        if is_staff or is_superuser:
            UserRole.objects.get_or_create(user=user, school=school, role_code="chaplain")
        return user

    monkeypatch.setattr(module, "_mk_user", user_with_spiritual_authority)
