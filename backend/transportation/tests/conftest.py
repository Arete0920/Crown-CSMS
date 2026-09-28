from __future__ import annotations

import pytest

from core.models import CrownPermission, RolePermission, UserRole


@pytest.fixture(autouse=True)
def _legacy_transportation_client_uses_persistent_authority(request, monkeypatch):
    """Keep legacy Transportation functional tests on persistent CROWN authority.

    Historical helpers encoded X-Role/Django-staff authorization. Positive
    operator personas receive the real tenant-scoped view/edit capabilities;
    legacy read-only tests receive only view. Negative spoofing cases remain
    ungranted.
    """
    module = request.module
    # Only the historical functional suite uses the role-based client helper.
    # Security suites must retain their own explicit grants and spoofing inputs.
    if module.__name__.rsplit(".", 1)[-1] != "test_transportation":
        return
    original = getattr(module, "_client", None)
    if original is None:
        return

    positive_legacy_roles = {"transportation_director", "admin", "ops"}
    legacy_read_tests = {"test_readonly_role_can_list", "test_teacher_can_read_routes"}

    def _grant(user, school, code, description):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": description},
        )
        role_code = "transportation_test_operator"
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
        UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)

    def client_with_persistent_authority(user, school, role="transportation_director"):
        if role in positive_legacy_roles:
            _grant(user, school, "transportation.view", "View transportation dashboard")
            _grant(user, school, "transportation.edit", "Create or modify transportation operational records")
        elif role == "teacher" and request.node.name in legacy_read_tests:
            _grant(user, school, "transportation.view", "View transportation dashboard")
        return original(user, school, role=role)

    monkeypatch.setattr(module, "_client", client_with_persistent_authority)
