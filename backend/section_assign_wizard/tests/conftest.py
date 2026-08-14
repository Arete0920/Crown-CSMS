import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserRole


BASE_URL = "/api/v1/section-assign-wizard/sessions/"


def _grant_legacy_functional_authority(user, school):
    """Give the legacy functional fixture the explicit authority it now requires."""
    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")
    for code in ("rosters.edit", "academics.view"):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": f"test permission {code}"},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)


@pytest.fixture(autouse=True)
def explicit_legacy_section_assign_authority(request, monkeypatch):
    """
    test_views.py predates roster RBAC and builds authenticated clients without roles.
    Preserve those functional/state-machine assertions by making their intended
    registrar authority explicit at the request fixture boundary. RBAC-specific
    tests are intentionally excluded and continue to prove denial/revocation.
    """
    if request.node.path.name != "test_views.py":
        yield
        return

    original_post = APIClient.post

    def post_with_authority(client, path, *args, **kwargs):
        if path.startswith(BASE_URL):
            user = getattr(client.handler, "_force_user", None)
            school_id = kwargs.get("HTTP_X_SCHOOL_ID")
            if user is not None and school_id:
                school = School.objects.filter(pk=school_id).first()
                if school is not None:
                    _grant_legacy_functional_authority(user, school)
        return original_post(client, path, *args, **kwargs)

    monkeypatch.setattr(APIClient, "post", post_with_authority)
    yield
