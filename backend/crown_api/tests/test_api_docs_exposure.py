import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings


pytestmark = pytest.mark.django_db


@override_settings(CROWN_ENV="production", CROWN_API_DOCS_ENABLED=False)
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/", "/api/redoc/"])
def test_production_api_docs_are_hidden_by_default(path):
    response = Client().get(path)
    assert response.status_code == 404


@override_settings(CROWN_ENV="production", CROWN_API_DOCS_ENABLED=True)
@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/", "/api/redoc/"])
def test_enabled_production_api_docs_remain_hidden_from_unauthenticated_users(path):
    response = Client().get(path)
    assert response.status_code == 404


@override_settings(CROWN_ENV="production", CROWN_API_DOCS_ENABLED=True)
def test_enabled_production_api_docs_remain_hidden_from_nonstaff_users():
    User = get_user_model()
    user = User.objects.create_user(
        username="api-docs-nonstaff",
        email="api-docs-nonstaff@example.test",
        password="StrongPass1!",
    )

    client = Client()
    client.force_login(user)

    for path in ("/api/schema/", "/api/docs/", "/api/redoc/"):
        assert client.get(path).status_code == 404


@override_settings(CROWN_ENV="production", CROWN_API_DOCS_ENABLED=True)
def test_enabled_production_schema_allows_authenticated_staff():
    User = get_user_model()
    staff = User.objects.create_user(
        username="api-docs-staff",
        email="api-docs-staff@example.test",
        password="StrongPass1!",
        is_staff=True,
    )

    client = Client()
    client.force_login(staff)
    response = client.get("/api/schema/")

    assert response.status_code == 200
