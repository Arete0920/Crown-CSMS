import pytest
from core.models import School
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
def test_master_control_rejects_unbound_non_staff_user_even_with_valid_school_header():
    school = School.objects.create(name="Master Control Bound Tenant")
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="master-control-unbound-non-staff",
        school_id=None,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."
