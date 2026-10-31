import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from financial_aid.models import AidAward, AidBucket, FinancialAidApplication

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_tenant_middleware(settings):
    settings.TENANT_HEADER_REQUIRED = True


def _school(name="FA Authz School"):
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _user(label="u"):
    return UserAccount.objects.create_user(
        username=f"{label}-{uuid.uuid4()}",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    if user.school_id != school.id:
        user.school = school
        user.save(update_fields=["school"])
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    permission, _ = CrownPermission.objects.get_or_create(
        code=perm_code,
        defaults={"description": ""},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _seed_fa_data(school_id):
    application = FinancialAidApplication.objects.create(
        school_id=school_id,
        household_id=uuid.uuid4(),
        academic_year="2026-2027",
        household_income="55000.00",
        household_size=4,
        status="decided",
    )
    award = AidAward.objects.create(
        school_id=school_id,
        application=application,
        bucket=AidBucket.NEED,
        amount="8000.00",
        rationale="Demonstrable need",
    )
    return application, award


def _client_for(user):
    client = Client()
    client.force_login(user)
    return client


class TestFinancialAidPermissionGate:
    @pytest.mark.parametrize(
        "role_code,perm_code",
        [("PARENT", "parent.view"), ("STUDENT", "student.view"), ("TEACHER", "teacher.view")],
    )
    def test_role_blocked_on_summary(self, role_code, perm_code):
        school = _school("Gate Test")
        user = _user(role_code.lower())
        _assign_role(user, school, role_code)
        _grant(role_code, perm_code)
        response = _client_for(user).get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 403, (
            f"Role {role_code!r} should be blocked from financial-aid/summary/ "
            f"but got {response.status_code}"
        )

    @pytest.mark.parametrize(
        "role_code,perm_code",
        [("PARENT", "parent.view"), ("STUDENT", "student.view"), ("TEACHER", "teacher.view")],
    )
    def test_role_blocked_on_drilldown(self, role_code, perm_code):
        school = _school("Gate Test DD")
        user = _user(f"{role_code.lower()}_dd")
        _assign_role(user, school, role_code)
        _grant(role_code, perm_code)
        response = _client_for(user).get(
            "/api/v1/financial-aid/drilldown/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 403, (
            f"Role {role_code!r} should be blocked from financial-aid/drilldown/ "
            f"but got {response.status_code}"
        )

    def test_unauthenticated_gets_403_not_data(self):
        school = _school("Anon Gate")
        response = Client().get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code in (401, 403)


class TestFinancialAidPermissionAllowed:
    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
    def test_role_reaches_summary(self, role_code):
        school = _school("Allowed Test")
        user = _user(role_code.lower())
        _assign_role(user, school, role_code)
        _grant(role_code, "financial_aid.view")
        response = _client_for(user).get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 200, (
            f"Role {role_code!r} should reach financial-aid/summary/ "
            f"but got {response.status_code}"
        )

    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
    def test_role_reaches_drilldown(self, role_code):
        school = _school("Allowed DD Test")
        user = _user(f"{role_code.lower()}_dd2")
        _assign_role(user, school, role_code)
        _grant(role_code, "financial_aid.view")
        _seed_fa_data(school.id)
        response = _client_for(user).get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 200, (
            f"Role {role_code!r} should reach financial-aid/drilldown/ "
            f"but got {response.status_code}"
        )


class TestFinancialAidTenantIsolation:
    def test_cross_tenant_row_isolation_on_drilldown(self):
        school_a = _school("FA Tenant A")
        school_b = _school("FA Tenant B")
        user = _user("aiddir_isolation")
        _assign_role(user, school_a, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")
        _seed_fa_data(school_b.id)

        response = _client_for(user).get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school_b.id),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "tenant_access_denied"

    def test_same_tenant_drilldown_returns_own_data_only(self):
        school_a = _school("FA Own Data A")
        school_b = _school("FA Own Data B")
        user = _user("aiddir_own")
        _assign_role(user, school_a, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")
        _seed_fa_data(school_a.id)
        _seed_fa_data(school_b.id)

        response = _client_for(user).get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert response.status_code == 200
        data = response.json()
        for row in data.get("rows", []):
            assert row.get("award_id") is not None
        assert data["total"] == 1


class TestRationaleFieldRedaction:
    def _rows_for(self, role_code, *, rationale_permission=False):
        school = _school(f"Rationale {role_code}")
        user = _user(f"rationale-{role_code.lower()}")
        _assign_role(user, school, role_code)
        _grant(role_code, "financial_aid.view")
        if rationale_permission:
            _grant(role_code, "financial_aid.view_rationale")
        _seed_fa_data(school.id)
        response = _client_for(user).get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 200
        rows = response.json().get("rows", [])
        assert rows
        return rows

    def test_aid_director_sees_rationale(self):
        for row in self._rows_for("AID_DIRECTOR", rationale_permission=True):
            assert row["rationale"] == "Demonstrable need"

    def test_finance_director_rationale_is_null(self):
        for row in self._rows_for("FINANCE_DIRECTOR"):
            assert row["rationale"] is None

    def test_head_of_school_rationale_is_null(self):
        for row in self._rows_for("HEAD_OF_SCHOOL"):
            assert row["rationale"] is None


class TestFinancialAidApiRoutePermissions:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/financial-aid/applications/",
            "/api/v1/financial-aid/awards/",
        ],
    )
    def test_non_financial_role_cannot_read_sensitive_financial_aid_rows(self, path):
        school = _school("FA API Read Denied")
        user = _user("teacher-fa-api")
        _assign_role(user, school, "TEACHER")
        _grant("TEACHER", "teacher.view")
        _seed_fa_data(school.id)

        response = _client_for(user).get(path, HTTP_X_SCHOOL_ID=str(school.id))

        assert response.status_code == 403
        assert response.json()["ok"] is False

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/financial-aid/applications/",
            "/api/v1/financial-aid/awards/",
        ],
    )
    def test_financial_aid_view_permission_allows_sensitive_reads(self, path):
        school = _school("FA API Read Allowed")
        user = _user("aid-read-api")
        _assign_role(user, school, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")
        _seed_fa_data(school.id)

        response = _client_for(user).get(path, HTTP_X_SCHOOL_ID=str(school.id))

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert len(payload["data"]) == 1

    def test_view_only_role_cannot_disburse_to_billing_run(self, monkeypatch):
        school = _school("FA Disburse Denied")
        user = _user("finance-view-only")
        _assign_role(user, school, "FINANCE_DIRECTOR")
        _grant("FINANCE_DIRECTOR", "financial_aid.view")
        called = False

        def _unexpected_service_call(**kwargs):
            nonlocal called
            called = True
            return {"unexpected": True}

        monkeypatch.setattr(
            "financial_aid.api.apply_financial_aid_to_billing_run",
            _unexpected_service_call,
        )

        response = _client_for(user).post(
            f"/api/v1/financial-aid/billing-runs/{uuid.uuid4()}/disburse/",
            data={},
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )

        assert response.status_code == 403
        assert called is False

    def test_edit_permission_allows_disbursement_service_call(self, monkeypatch):
        school = _school("FA Disburse Allowed")
        user = _user("aid-edit")
        _assign_role(user, school, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.edit")
        billing_run_id = uuid.uuid4()
        calls = []

        def _service_call(**kwargs):
            calls.append(kwargs)
            return {"billing_run_id": str(kwargs["billing_run_id"]), "applied": 1}

        monkeypatch.setattr(
            "financial_aid.api.apply_financial_aid_to_billing_run",
            _service_call,
        )

        response = _client_for(user).post(
            f"/api/v1/financial-aid/billing-runs/{billing_run_id}/disburse/",
            data={},
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )

        assert response.status_code == 200
        assert calls == [{"school_id": school.id, "billing_run_id": billing_run_id}]

    def test_cross_tenant_financial_aid_api_request_is_denied_before_rows_return(self):
        school_a = _school("FA API Tenant A")
        school_b = _school("FA API Tenant B")
        user = _user("aid-cross-tenant")
        _assign_role(user, school_a, "AID_DIRECTOR")
        _grant("AID_DIRECTOR", "financial_aid.view")
        _seed_fa_data(school_b.id)

        response = _client_for(user).get(
            "/api/v1/financial-aid/applications/",
            HTTP_X_SCHOOL_ID=str(school_b.id),
        )

        assert response.status_code == 404
        assert response.json()["code"] == "tenant_access_denied"


class TestFinancialAidAwardListRationaleRedaction:
    """The legacy award list must not bypass drilldown's sensitive-rationale grant."""

    @pytest.mark.parametrize("path", [
        "/api/v1/financial-aid/awards/",
        "/api/financial-aid/awards/",
    ])
    def test_aid_view_without_rationale_grant_returns_null(self, path):
        school = _school("Award Rationale Read")
        user = _user("award-reader")
        _assign_role(user, school, "AID_AWARD_READ_ONLY_TEST")
        _grant("AID_AWARD_READ_ONLY_TEST", "financial_aid.view")
        _seed_fa_data(school.id)

        response = _client_for(user).get(path, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert len(payload["data"]) == 1
        assert "rationale" in payload["data"][0]
        assert payload["data"][0]["rationale"] is None
        assert b"Demonstrable need" not in response.content

    @pytest.mark.parametrize("path", [
        "/api/v1/financial-aid/awards/",
        "/api/financial-aid/awards/",
    ])
    def test_explicit_same_school_rationale_grant_preserves_value(self, path):
        school = _school("Award Rationale Allowed")
        user = _user("award-rationale-reader")
        _assign_role(user, school, "AID_AWARD_RATIONALE_TEST")
        _grant("AID_AWARD_RATIONALE_TEST", "financial_aid.view")
        _grant("AID_AWARD_RATIONALE_TEST", "financial_aid.view_rationale")
        _seed_fa_data(school.id)

        response = _client_for(user).get(path, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"][0]["rationale"] == "Demonstrable need"

    def test_grant_at_other_school_cannot_disclose_home_school_rationale(self):
        home = _school("Award Rationale Home")
        foreign = _school("Award Rationale Other")
        user = _user("award-role-separation")
        _assign_role(user, home, "AID_AWARD_HOME_VIEW_TEST")
        UserRole.objects.create(
            user=user, school=foreign, role_code="AID_AWARD_OTHER_RATIONALE_TEST"
        )
        _grant("AID_AWARD_HOME_VIEW_TEST", "financial_aid.view")
        _grant("AID_AWARD_OTHER_RATIONALE_TEST", "financial_aid.view_rationale")
        _seed_fa_data(home.id)

        response = _client_for(user).get(
            "/api/v1/financial-aid/awards/",
            HTTP_X_SCHOOL_ID=str(home.id),
        )
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 1
        assert payload["data"][0]["rationale"] is None
        assert b"Demonstrable need" not in response.content


class TestFinancialAidAwardOwnershipConsistency:
    def test_award_reads_exclude_foreign_application_but_preserve_unlinked_awards(self):
        home = _school("Award Home Link")
        foreign = _school("Award Foreign Link")
        user = _user("award-link-scope")
        role = "AID_AWARD_LINK_SCOPE_TEST"
        _assign_role(user, home, role)
        _grant(role, "financial_aid.view")

        _own_application, owned_award = _seed_fa_data(home.id)
        foreign_application, _foreign_award = _seed_fa_data(foreign.id)
        inconsistent = AidAward.objects.create(
            school_id=home.id,
            application=foreign_application,
            bucket=AidBucket.NEED,
            amount="9000.00",
            rationale="Synthetic mismatched association",
        )
        unlinked = AidAward.objects.create(
            school_id=home.id,
            application=None,
            bucket=AidBucket.NEED,
            amount="1000.00",
        )
        client = _client_for(user)
        for path in ("/api/v1/financial-aid/awards/", "/api/financial-aid/awards/"):
            response = client.get(path, HTTP_X_SCHOOL_ID=str(home.id))
            assert response.status_code == 200
            payload = response.json()
            assert payload["ok"] is True
            returned = {row["id"] for row in payload["data"]}
            assert returned == {str(owned_award.id), str(unlinked.id)}
            assert str(inconsistent.id) not in returned

        metrics = client.get("/api/v1/financial-aid/metrics/", HTTP_X_SCHOOL_ID=str(home.id))
        assert metrics.status_code == 200
        assert metrics.json()["budget_awarded"] == "9000.00"
        assert metrics.json()["avg_award"] == 4500
