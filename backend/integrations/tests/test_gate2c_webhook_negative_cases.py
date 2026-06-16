import pytest
from django.test import override_settings
from django.urls import reverse

from core.models import School

pytestmark = pytest.mark.django_db


@override_settings(TENANT_HEADER_REQUIRED=True)
def test_legacy_compuwerx_webhook_is_retired(client):
    School.objects.create(name="Legacy Route School")
    url = reverse("compuwerx-webhook")

    response = client.post(url, data="{}", content_type="application/json")

    assert response.status_code == 410
    assert response.json()["error"] == "legacy_compuwerx_webhook_retired"
