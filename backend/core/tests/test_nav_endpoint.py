import json
import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from subscriptions.models import SchoolModule

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_tenant_middleware(settings):
    settings.TENANT_HEADER_REQUIRED = True


def _school(name="Nav Test School"):
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _user(label="u", school=None):
    return UserAccount.objects.create_user(
        username=f"{label}-{uuid.uuid4()}",
        password="Passw0rd!",
        school=school,
    )


def _assign_role(user, school, role_code):
    if user.school_id != school.id:
        user.school = school
        user.save(update_fields=["school"])
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(
        code=perm_code,
        defaults={"description": ""},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _nav_flat_labels(payload):
    return [item["label"] for group in payload.get("groups", []) for item in group.get("items", [])]


def _nav_flat_hrefs(payload):
    return [item["href"] for group in payload.get("groups", []) for item in group.get("items", [])]


class TestNavTenantEnforcement:
    def test_missing_school_id_header_returns_400(self):
        response = Client().get("/api/v1/nav/")
        assert response.status_code == 400

    def test_unknown_school_id_returns_404(self):
        response = Client().get(
            "/api/v1/nav/",
            HTTP_X_SCHOOL_ID=str(uuid.uuid4()),
        )
        assert response.status_code == 404


class TestNavPermissionFiltering:
    def test_parent_does_not_see_finance_admissions_billing_integrity(self):
        school = _school("Parent Nav School")
        parent = _user("parent1")
        _assign_role(parent, school, "parent")
        _grant("parent", "parent.view")

        client = Client()
        client.force_login(parent)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200

        payload = json.loads(response.content)
        labels = _nav_flat_labels(payload)
        hrefs = _nav_flat_hrefs(payload)
        assert "Parent" in labels
        assert "/parent" in hrefs
        assert "Finance" not in labels
        assert "Billing" not in labels
        assert "Admissions" not in labels
        assert "System Integrity" not in labels
        assert "/finance" not in hrefs
        assert "/billing" not in hrefs
        assert "/admissions" not in hrefs
        assert "/integrity" not in hrefs

    def test_finance_role_sees_finance_and_billing_not_admissions(self):
        school = _school("Finance Nav School")
        user = _user("fin1")
        _assign_role(user, school, "finance")
        _grant("finance", "finance.view")
        _grant("finance", "billing.view")

        client = Client()
        client.force_login(user)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        hrefs = _nav_flat_hrefs(json.loads(response.content))
        assert "/finance" in hrefs
        assert "/billing" in hrefs
        assert "/admissions" not in hrefs
        assert "/parent" not in hrefs

    def test_head_of_school_sees_admin_board_integrity(self):
        school = _school("HoS Nav School")
        user = _user("hos1")
        _assign_role(user, school, "HEAD_OF_SCHOOL")
        _grant("HEAD_OF_SCHOOL", "admin.view")
        _grant("HEAD_OF_SCHOOL", "board.view")
        _grant("HEAD_OF_SCHOOL", "integrity.view")

        client = Client()
        client.force_login(user)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        hrefs = _nav_flat_hrefs(json.loads(response.content))
        assert "/admin" in hrefs
        assert "/board" in hrefs
        assert "/integrity" in hrefs

    def test_user_with_no_roles_sees_empty_nav(self):
        school = _school("Empty Nav School")
        user = _user("noroles1", school=school)

        client = Client()
        client.force_login(user)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        assert json.loads(response.content)["groups"] == []

    def test_teacher_sees_teacher_and_academics_not_finance(self):
        school = _school("Teacher Nav School")
        user = _user("teacher1")
        _assign_role(user, school, "TEACHER")
        _grant("TEACHER", "teacher.view")
        _grant("TEACHER", "academics.view")

        client = Client()
        client.force_login(user)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        hrefs = _nav_flat_hrefs(json.loads(response.content))
        assert "/teacher" in hrefs
        assert "/academics" in hrefs
        assert "/finance" not in hrefs
        assert "/admin" not in hrefs


class TestNavResponseShape:
    def _response(self, label):
        school = _school(f"Shape School {label}")
        user = _user(f"shape-{label}")
        _assign_role(user, school, "parent")
        _grant("parent", "parent.view")
        client = Client()
        client.force_login(user)
        return client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))

    def test_response_has_groups_key(self):
        payload = json.loads(self._response("one").content)
        assert "groups" in payload
        assert isinstance(payload["groups"], list)

    def test_group_has_title_and_items(self):
        payload = json.loads(self._response("two").content)
        for group in payload["groups"]:
            assert "title" in group
            assert "items" in group
            assert isinstance(group["items"], list)

    def test_item_has_label_and_href(self):
        payload = json.loads(self._response("three").content)
        for group in payload["groups"]:
            for item in group["items"]:
                assert "label" in item
                assert "href" in item

    def test_school_scoping_cross_tenant_isolation(self):
        school_a = _school("School A Nav")
        school_b = _school("School B Nav")
        user = _user("cross")
        _assign_role(user, school_a, "finance")
        _grant("finance", "finance.view")

        client = Client()
        client.force_login(user)
        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school_b.id))
        assert response.status_code == 404
        assert response.json()["code"] == "tenant_access_denied"


class TestHomeAcademyNavEntitlement:
    def test_parent_home_academy_link_hidden_until_module_enabled(self):
        school = _school("Home Academy Parent Nav")
        parent = _user("ha-parent")
        _assign_role(parent, school, "parent")
        _grant("parent", "parent.view")
        client = Client()
        client.force_login(parent)

        before = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert before.status_code == 200
        assert "/parent/home-academy" not in _nav_flat_hrefs(before.json())

        SchoolModule.objects.create(
            school=school,
            module_key="home_academy",
            status="active",
        )
        after = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))
        assert after.status_code == 200
        assert "/parent/home-academy" in _nav_flat_hrefs(after.json())

    def test_registrar_home_academy_link_requires_edit_permission_and_entitlement(self):
        school = _school("Home Academy Registrar Nav")
        registrar = _user("ha-registrar")
        _assign_role(registrar, school, "registrar")
        _grant("registrar", "home_academy.edit")
        SchoolModule.objects.create(
            school=school,
            module_key="home_academy",
            status="active",
        )
        client = Client()
        client.force_login(registrar)

        response = client.get("/api/v1/nav/", HTTP_X_SCHOOL_ID=str(school.id))

        assert response.status_code == 200
        assert "/home-academy" in _nav_flat_hrefs(response.json())
        assert "/parent/home-academy" not in _nav_flat_hrefs(response.json())
