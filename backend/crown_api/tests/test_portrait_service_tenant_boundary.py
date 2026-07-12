import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@override_settings(
    TENANT_HEADER_REQUIRED=False,
    CROWN_ENV="development",
    CROWN_DEV_OPEN_API=True,
)
@pytest.mark.django_db
def test_portrait_service_summary_requires_explicit_tenant_header_even_in_dev_open():
    user_model = get_user_model()
    user = user_model.objects.create_user(username="portrait-service-no-header")
    user.set_unusable_password()
    user.save(update_fields=["password"])

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "portrait-service"})
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "X-School-Id header is required."
