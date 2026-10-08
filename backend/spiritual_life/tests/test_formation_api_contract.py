from __future__ import annotations

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db

SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"
FORMATION_URLS = [
    "/api/v1/spiritual-life/formation/summary/",
    "/api/v1/spiritual-life/formation/portrait-domains/",
    "/api/v1/spiritual-life/formation/worldview-priorities/",
    "/api/v1/spiritual-life/formation/campaigns/",
    "/api/v1/spiritual-life/formation/artifacts/",
    "/api/v1/spiritual-life/formation/devotions/",
    "/api/v1/spiritual-life/formation/biblical-integration/",
    "/api/v1/spiritual-life/formation/domain-ratings/",
    "/api/v1/spiritual-life/formation/care-cases/",
    "/api/v1/spiritual-life/formation/church-partners/",
    "/api/v1/spiritual-life/formation/pastor-contacts/",
    "/api/v1/spiritual-life/formation/church-engagements/",
    "/api/v1/spiritual-life/formation/christian-education-sundays/",
    "/api/v1/spiritual-life/formation/community-partners/",
    "/api/v1/spiritual-life/formation/student-leaders/",
    "/api/v1/spiritual-life/formation/student-leadership-events/",
    "/api/v1/spiritual-life/formation/calling-pathways/",
    "/api/v1/spiritual-life/formation/family-formation-events/",
    "/api/v1/spiritual-life/formation/staff-formation-events/",
    "/api/v1/spiritual-life/formation/speaker-vetting/",
]


def mk_school():
    return School.objects.create(name="Formation Test School")


def mk_user(school, username="formation_user"):
    return UserAccount.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="pass12345",
        school=school,
    )


def assign_role(user, school, role_code="spiritual_life_contract_tester"):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def grant(role_code, perm_code="spiritual_life.view"):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


@pytest.mark.parametrize("url", FORMATION_URLS)
def test_formation_urls_require_auth_or_tenant(url):
    client = Client()
    response = client.get(url)
    assert response.status_code in (400, 401, 403), (
        f"{url}: unauthenticated/no-tenant request must not return 200; got {response.status_code}"
    )


@pytest.mark.parametrize("url", FORMATION_URLS)
def test_formation_urls_available_to_spiritual_life_viewer(url):
    school = mk_school()
    user = mk_user(school, url.strip("/").replace("/", "_")[:80])
    role_code = "spiritual_life_contract_tester"
    assign_role(user, school, role_code)
    grant(role_code)

    client = Client()
    client.force_login(user)
    response = client.get(url, **{SCHOOL_ID_HEADER: str(school.id)})
    assert response.status_code == 200, f"{url}: expected 200, got {response.status_code}"


def test_can_create_portrait_domain_for_school():
    school = mk_school()
    user = mk_user(school, "portrait_domain_create")
    role_code = "spiritual_life_contract_tester"
    assign_role(user, school, role_code)
    grant(role_code)
    grant(role_code, "spiritual_life.edit")

    client = Client()
    client.force_login(user)
    response = client.post(
        "/api/v1/spiritual-life/formation/portrait-domains/",
        data={
            "name": "Christ-centered identity",
            "description": "Students understand identity in Christ and live with wisdom and humility.",
            "scripture_anchor": "Colossians 3:1-17",
            "is_active": True,
            "sort_order": 1,
        },
        content_type="application/json",
        **{SCHOOL_ID_HEADER: str(school.id)},
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["name"] == "Christ-centered identity"
    assert body["school_id"] == str(school.id)


def test_view_only_user_cannot_create_school_wide_formation_record():
    school = mk_school()
    user = mk_user(school, "portrait_domain_view_only")
    role_code = "spiritual_life_view_only_tester"
    assign_role(user, school, role_code)
    grant(role_code, "spiritual_life.view")

    client = Client()
    client.force_login(user)
    response = client.post(
        "/api/v1/spiritual-life/formation/portrait-domains/",
        data={
            "name": "Unauthorized mutation",
            "description": "This write must be denied.",
            "scripture_anchor": "Colossians 3:1-17",
            "is_active": True,
            "sort_order": 99,
        },
        content_type="application/json",
        **{SCHOOL_ID_HEADER: str(school.id)},
    )

    assert response.status_code == 403
