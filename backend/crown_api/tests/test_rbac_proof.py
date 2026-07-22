import pytest
from django.test import Client

from crown_api.auth_models import CrownUser
from crown_api.jwt_utils import build_access_token


def _authenticated_client(*, role):
    user = CrownUser.objects.create(
        email=f"{role}@example.test",
        password_hash="unused",
        role=role,
        is_active=True,
    )
    token = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=role,
        school_id=None,
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.mark.django_db
def test_rbac_finance_proof_forbidden_without_role():
    response = Client().get("/api/system/rbac/finance-proof/")
    assert response.status_code == 403
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "Forbidden"
    assert "required_roles" in data


@pytest.mark.django_db
def test_rbac_finance_proof_rejects_anonymous_demo_header_even_when_flag_enabled(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    response = Client(HTTP_X_DEMO_ROLE="admin").get("/api/system/rbac/finance-proof/")
    assert response.status_code == 403
    assert response.json()["actual_role"] is None


@pytest.mark.django_db
def test_rbac_finance_proof_allows_authenticated_admin():
    response = _authenticated_client(role="AdMiN").get("/api/system/rbac/finance-proof/")
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_rbac_finance_proof_allows_authenticated_finance():
    response = _authenticated_client(role="finance").get("/api/system/rbac/finance-proof/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_rbac_finance_proof_rejects_authenticated_wrong_role():
    response = _authenticated_client(role="teacher").get("/api/system/rbac/finance-proof/")
    assert response.status_code == 403
    assert response.json()["actual_role"] == "teacher"


@pytest.mark.django_db
def test_demo_header_cannot_override_authenticated_wrong_role(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    client = _authenticated_client(role="teacher")
    response = client.get(
        "/api/system/rbac/finance-proof/",
        HTTP_X_DEMO_ROLE="admin",
    )
    assert response.status_code == 403
    assert response.json()["actual_role"] == "teacher"
