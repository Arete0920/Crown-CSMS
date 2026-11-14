"""Cold-start and real JWT proof for configured REST defaults."""
import json
import os
import secrets
import subprocess
import sys

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from core.models import School, UserAccount


def test_cold_start_applies_authentication_permissions_and_schema_extensions():
    code = '''
import django, json
django.setup()
from django.conf import settings
from rest_framework.views import APIView
from crown_api.system_views import whoami
from drf_spectacular.extensions import OpenApiAuthenticationExtension
def paths(classes):
    return [c.__module__ + "." + c.__name__ for c in classes]
print(json.dumps({
    "configured_auth": settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
    "actual_auth": paths(APIView.authentication_classes),
    "identity_auth": paths(whoami.cls.authentication_classes),
    "configured_permissions": settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
    "actual_permissions": paths(APIView.permission_classes),
    "schema_extensions": [c.__name__ for c in OpenApiAuthenticationExtension._registry],
}))
'''
    process = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             env={**os.environ, "DJANGO_SETTINGS_MODULE": "crown_api.settings"}, timeout=30)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout.strip().splitlines()[-1])
    assert result["actual_auth"] == result["identity_auth"] == result["configured_auth"]
    assert result["actual_permissions"] == result["configured_permissions"]
    assert "TenantJWTAuthenticationExtension" in result["schema_extensions"]
    assert "AADBearerAuthenticationExtension" in result["schema_extensions"]


@pytest.mark.django_db
def test_normal_password_login_proves_own_identity_and_denies_foreign_tenant():
    school = School.objects.create(name="Fictional authentication school")
    foreign = School.objects.create(name="Other fictional authentication school")
    password = secrets.token_urlsafe(32)
    user = UserAccount.objects.create_user(username="startup-proof@fictional.crown.invalid",
                                            email="startup-proof@fictional.crown.invalid",
                                            password=password, school=school)
    client = APIClient()
    assert client.get("/api/system/whoami/").status_code == 401
    signed = client.post("/api/v1/auth/token/", {"username": user.username, "password": password}, format="json")
    assert signed.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {signed.json()['access']}")
    own = client.get("/api/system/whoami/")
    assert own.status_code == 200, own.content
    assert own.json()["user"]["id"] == str(user.pk)
    assert own.json()["user"]["school_id"] == str(school.pk)
    assert own.json()["tenant"]["resolved_school_id"] == str(school.pk)
    assert not user.is_staff and not user.is_superuser
    denied = client.get("/api/v1/households/", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert denied.status_code == 404
    assert not denied.json().get("results")
