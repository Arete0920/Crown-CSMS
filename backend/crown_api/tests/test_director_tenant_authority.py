"""HTTP regression: legacy director routes require active school-specific authority."""
from datetime import date
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from core.models import AcademicYear, School, UserRole


@pytest.mark.django_db
def test_legacy_director_reads_require_active_matching_school_role():
    own = School.objects.create(name="Synthetic Director Own School")
    other = School.objects.create(name="Synthetic Director Other School")
    pending = School.objects.create(name="Synthetic Director Pending", is_active=False)
    year = AcademicYear.objects.create(
        school=own, name="2026-2027", start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30), is_current=True,
    )
    User = get_user_model()
    director = User.objects.create_user(
        username=f"synthetic-director-{uuid4().hex}", school=own, is_staff=True,
    )
    UserRole.objects.create(user=director, school=own, role_code="AID_DIRECTOR")
    client = APIClient()
    client.force_authenticate(user=director)
    url = "/api/director/registrar/summary/"

    def fetch(target, selected_header=None):
        return client.get(
            f"{url}?school_id={target}&academic_year_id={year.pk}",
            HTTP_X_SCHOOL_ID=str(selected_header if selected_header is not None else target),
        )

    assert fetch(own.pk).status_code == 200
    assert fetch(other.pk).status_code == 403
    assert fetch(pending.pk).status_code == 403
    assert fetch(own.pk, other.pk).status_code == 403

    with override_settings(CROWN_DEV_OPEN_API=True):
        no_role = User.objects.create_user(
            username=f"synthetic-director-norole-{uuid4().hex}",
            school=own, is_staff=True,
        )
        client.force_authenticate(user=no_role)
        assert fetch(own.pk).status_code == 403


@pytest.mark.django_db
def test_legacy_director_writes_require_matching_school_role():
    own = School.objects.create(name="Synthetic Director Write Own")
    other = School.objects.create(name="Synthetic Director Write Other")
    User = get_user_model()
    director = User.objects.create_user(
        username=f"synthetic-writer-{uuid4().hex}", school=own, is_staff=True,
    )
    UserRole.objects.create(user=director, school=own, role_code="AID_DIRECTOR")
    client = APIClient()
    client.force_authenticate(user=director)
    payload = {"action": "POST_ACCEPTED_AWARDS", "ids": [str(uuid4())]}
    url = "/api/director/actions/"

    denied = client.post(url, {**payload, "school_id": str(other.pk)},
                         format="json", HTTP_X_SCHOOL_ID=str(other.pk))
    assert denied.status_code == 403

    allowed = client.post(url, {**payload, "school_id": str(own.pk)},
                          format="json", HTTP_X_SCHOOL_ID=str(own.pk))
    assert allowed.status_code == 200
    assert allowed.data["posted_count"] == 0

    # A valid role attached to a different school cannot authorize this write.
    impostor = User.objects.create_user(
        username=f"synthetic-no-target-role-{uuid4().hex}",
        school=other, is_staff=True,
    )
    UserRole.objects.create(user=impostor, school=other, role_code="AID_DIRECTOR")
    client.force_authenticate(user=impostor)
    wrong = client.post(url, {**payload, "school_id": str(own.pk)},
                        format="json", HTTP_X_SCHOOL_ID=str(own.pk))
    assert wrong.status_code == 403


@pytest.mark.django_db
def test_platform_owner_can_read_only_active_director_school():
    active = School.objects.create(name="Synthetic Director Owner Active")
    pending = School.objects.create(name="Synthetic Director Owner Pending", is_active=False)
    year = AcademicYear.objects.create(
        school=active, name="2026-2027", start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30), is_current=True,
    )
    owner = get_user_model().objects.create_superuser(
        username=f"synthetic-owner-{uuid4().hex}",
        email="synthetic-owner@example.invalid",
        password="synthetic-test-only-password",
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    endpoint = "/api/director/registrar/summary/"
    active_response = client.get(
        f"{endpoint}?school_id={active.pk}&academic_year_id={year.pk}"
    )
    pending_response = client.get(
        f"{endpoint}?school_id={pending.pk}&academic_year_id={year.pk}"
    )
    assert active_response.status_code == 200
    assert pending_response.status_code == 403
