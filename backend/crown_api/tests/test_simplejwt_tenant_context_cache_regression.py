"""Defensive tenant regressions using fictional local records and normal JWT auth.

The AAD cases isolate its post-validation boundary; no identity-provider request
is made. These tests never persist or print generated bearer credentials.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import path
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken

from athletics.api.permissions import _request_school
from core.auth.authentication import AADBearerAuthentication
from core.middleware import TenantQuerySetMixin
from core.models import CrownPermission, RolePermission, School, UserRole
from core.tenant_header_middleware import TenantContextError
from core.tenant_models import clear_current_school, get_current_school, set_current_school
from crown_api.audit_models import AuditEvent
from crown_api.dashboards.tenant import get_dashboard_school_id
from crown_api.tenant import bind_tenant_context, build_tenant_context, get_tenant_school_id
from crown_api.tenant_authentication import TenantJWTAuthentication
from households.models import Guardian, Household
from onboarding.models import ImportSession


@pytest.fixture(autouse=True)
def isolated_tenant_runtime(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_DEV_OPEN_API = False
    settings.CROWN_ENV = "development"
    settings.HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = True
    clear_current_school()
    yield
    clear_current_school()


@pytest.fixture
def records(db):
    school_a = School.objects.create(name="Fictional Local School A")
    school_b = School.objects.create(name="Fictional Local School B")
    user = get_user_model().objects.create_user(
        username="fictional-tenant-reader",
        email="fictional-tenant-reader@example.invalid",
        password=None,
        school=school_a,
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    assert user.staff_id is None
    assert not UserRole.objects.filter(user=user).exists()
    assert not user.has_perm("core.override_tenant_context")
    return SimpleNamespace(
        user=user,
        school_a=school_a,
        school_b=school_b,
        household_a=Household.objects.create(school_id=school_a.id, name="Fictional Household A"),
        household_b=Household.objects.create(school_id=school_b.id, name="Fictional Household B"),
        import_a=ImportSession.objects.create(school=school_a, status=ImportSession.STATUS_VERIFIED),
        import_b=ImportSession.objects.create(school=school_b, status=ImportSession.STATUS_VERIFIED),
    )


def _jwt_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def _assert_bound(request, school, principal_school):
    context = request.crown_tenant
    assert context.actor_type == "user"
    assert context.principal_school_id == principal_school.id
    assert context.school_id == school.id
    assert context.school.pk == school.id
    assert request.school.pk == school.id
    assert request.tenant_school.pk == school.id
    assert request.school_id == str(school.id)
    assert request.tenant_school_id == school.id


def _assert_denied_without_school(response, records):
    request = response.renderer_context["request"]
    for target in (request, response.wsgi_request):
        assert target.crown_tenant.actor_type == "user"
        assert target.crown_tenant.principal_school_id == records.school_a.id
        assert target.crown_tenant.school_id == records.school_b.id
        assert target.crown_tenant.school is None
        for attr in ("school", "school_id", "tenant_school", "_crown_school_override_id"):
            assert getattr(target, attr, None) is None
    assert get_current_school() is None


@pytest.mark.parametrize("consumer", ["household", "onboarding"])
def test_real_simplejwt_principal_controls_own_and_foreign_records(records, consumer):
    """Exercise default auth and an existing explicitly JWT-configured consumer."""
    if consumer == "household":
        # Tenant authentication alone is not household read authority.
        UserRole.objects.create(user=records.user, school=records.school_a, role_code="PARENT")
        Guardian.objects.create(
            school_id=records.school_a.pk, household=records.household_a,
            account=records.user, first_name="Synthetic", last_name="Guardian",
        )
        own_record, foreign_record = records.household_a, records.household_b
        own_url = f"/api/v1/households/{own_record.pk}/"
        foreign_url = f"/api/v1/households/{foreign_record.pk}/"
        id_field = "id"
    else:
        own_record, foreign_record = records.import_a, records.import_b
        own_url = f"/api/v1/onboarding/imports/{own_record.pk}/verify/"
        foreign_url = f"/api/v1/onboarding/imports/{foreign_record.pk}/verify/"
        id_field = "session_id"

    client = _jwt_client(records.user)
    own = client.get(own_url, HTTP_X_SCHOOL_ID=str(records.school_a.id))
    assert own.status_code == 200
    assert str(own.json()[id_field]) == str(own_record.pk)
    request = own.renderer_context["request"]
    _assert_bound(request, records.school_a, records.school_a)
    _assert_bound(own.wsgi_request, records.school_a, records.school_a)
    assert request.crown_tenant == own.wsgi_request.crown_tenant
    assert request.user.pk == records.user.pk
    assert get_current_school() is None

    wrong_object = client.get(foreign_url, HTTP_X_SCHOOL_ID=str(records.school_a.id))
    assert wrong_object.status_code == 404
    foreign = client.get(foreign_url, HTTP_X_SCHOOL_ID=str(records.school_b.id))
    assert foreign.status_code == 404
    assert foreign.json() == {"detail": "Not found.", "code": "tenant_access_denied"}
    _assert_denied_without_school(foreign, records)

    event = AuditEvent.objects.get(action="tenant.context.decision")
    assert event.actor_id == records.user.pk
    assert event.meta["principal_school_id"] == str(records.school_a.id)
    assert event.meta["selected_school_id"] == str(records.school_b.id)
    assert event.meta["reason"] == "override_not_authorized"


class CachedTenantPermission(BasePermission):
    def has_permission(self, request, view):
        # These production helpers consume cached authority before view logic.
        view.cached_scope = {
            "canonical": str(get_tenant_school_id(request)),
            "dashboard": str(get_dashboard_school_id(request)),
            "athletics": str(_request_school(request).pk),
            "current": str(get_current_school().pk),
            "actor_type": request.crown_tenant.actor_type,
            "principal_school": str(request.crown_tenant.principal_school_id),
        }
        return True


class CachedTenantView(TenantQuerySetMixin, GenericAPIView):
    queryset = ImportSession.objects.all()
    permission_classes = [IsAuthenticated, CachedTenantPermission]

    def get(self, request):
        return Response({
            "scope": self.cached_scope,
            "visible_imports": list(self.get_queryset().values_list("pk", flat=True)),
        })


urlpatterns = [path("api/v1/tenant-cache-regression/", CachedTenantView.as_view())]


def test_direct_cached_readers_see_authenticated_scope_before_data_access(records, settings):
    settings.ROOT_URLCONF = __name__
    response = _jwt_client(records.user).get(
        "/api/v1/tenant-cache-regression/", HTTP_X_SCHOOL_ID=str(records.school_a.id)
    )
    assert response.status_code == 200
    scope = response.json()["scope"]
    assert scope["actor_type"] == "user"
    for field in ("canonical", "dashboard", "athletics", "current", "principal_school"):
        assert scope[field] == str(records.school_a.id)
    assert response.json()["visible_imports"] == [records.import_a.pk]
    assert get_current_school() is None


def test_foreign_scope_is_denied_before_cached_consumers_query_data(records, settings):
    settings.ROOT_URLCONF = __name__
    with CaptureQueriesContext(connection) as queries:
        response = _jwt_client(records.user).get(
            "/api/v1/tenant-cache-regression/", HTTP_X_SCHOOL_ID=str(records.school_b.id)
        )
    assert response.status_code == 404
    assert response.json()["code"] == "tenant_access_denied"
    assert not any("onboarding_importsession" in item["sql"].lower() for item in queries)
    _assert_denied_without_school(response, records)


def test_real_simplejwt_support_override_does_not_change_assigned_school(records):
    UserRole.objects.create(user=records.user, school=records.school_a, role_code="SUPPORT")
    # Cross-school selection and private record access are distinct grants.
    records.user.is_staff = True
    records.user.save(update_fields=["is_staff"])
    UserRole.objects.create(user=records.user, school=records.school_b, role_code="REGISTRAR")
    permission, _ = CrownPermission.objects.get_or_create(code="households.view")
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    response = _jwt_client(records.user).get(
        f"/api/v1/households/{records.household_b.pk}/",
        HTTP_X_SCHOOL_ID=str(records.school_b.id),
    )
    # Audited tenant selection does not change the account's assigned school.
    # Even a target-school role cannot widen this protected read boundary.
    assert response.status_code == 404
    assert str(records.household_b.pk) not in str(response.content)
    assert records.household_b.name not in str(response.content)
    _assert_bound(response.renderer_context["request"], records.school_b, records.school_a)
    assert response.wsgi_request._crown_school_override_id == records.school_b.id
    event = AuditEvent.objects.get(action="tenant.context.decision")
    assert event.actor_id == records.user.pk
    assert event.school_id == records.school_b.id
    assert event.meta["actor_type"] == "user"
    assert event.meta["principal_school_id"] == str(records.school_a.id)
    assert event.meta["selected_school_id"] == str(records.school_b.id)
    assert event.meta["override_requested"] is True
    assert event.meta["override_authorized"] is True
    assert event.meta["outcome"] == "authorized"
    assert event.meta["reason"] == "explicit_cross_school_override"
    assert get_current_school() is None


def test_real_simplejwt_support_override_fails_closed_without_audit(records, monkeypatch):
    UserRole.objects.create(user=records.user, school=records.school_a, role_code="SUPPORT")
    monkeypatch.setattr(
        "core.tenant_header_middleware.audit_tenant_decision",
        Mock(side_effect=RuntimeError("synthetic audit unavailable")),
    )
    with CaptureQueriesContext(connection) as queries:
        response = _jwt_client(records.user).get(
            f"/api/v1/households/{records.household_b.pk}/",
            HTTP_X_SCHOOL_ID=str(records.school_b.id),
        )
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Tenant authorization evidence could not be persisted.",
        "code": "tenant_audit_unavailable",
    }
    assert not any("households_household" in item["sql"].lower() for item in queries)
    _assert_denied_without_school(response, records)


def _request_with_stale_bindings(
    records, *, selected_school, route="/api/v1/tenant-cache-regression/", method="get", aad=False
):
    # Recreate a pre-authentication snapshot, including stale DRF shadow aliases.
    credential = "fictional-aad-boundary-" * 8 if aad else str(AccessToken.for_user(records.user))
    raw = getattr(APIRequestFactory(), method)(
        route,
        HTTP_AUTHORIZATION=f"Bearer {credential}",
        HTTP_X_SCHOOL_ID=str(selected_school.id),
    )
    raw.user = AnonymousUser()
    context = build_tenant_context(raw, school=records.school_b)
    bind_tenant_context(raw, context)
    authenticator = AADBearerAuthentication() if aad else TenantJWTAuthentication()
    request = Request(raw, authenticators=[authenticator])
    bind_tenant_context(request, context)
    for target in (raw, request):
        target._crown_school_override_id = records.school_b.id
    set_current_school(records.school_b)
    return request


def test_successful_reauthentication_replaces_all_stale_bindings(records):
    request = _request_with_stale_bindings(records, selected_school=records.school_a)
    assert request.user.pk == records.user.pk
    for target in (request, request._request):
        _assert_bound(target, records.school_a, records.school_a)
        assert getattr(target, "_crown_school_override_id", None) is None
    assert get_current_school().pk == records.school_a.id


def test_denied_reauthentication_clears_stale_school_and_override_bindings(records):
    request = _request_with_stale_bindings(records, selected_school=records.school_b)
    with pytest.raises(TenantContextError) as exc:
        request.user
    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "tenant_access_denied"
    for target in (request, request._request):
        assert target.crown_tenant.principal_school_id == records.school_a.id
        assert target.crown_tenant.school is None
        for attr in ("school", "school_id", "tenant_school", "_crown_school_override_id"):
            assert getattr(target, attr, None) is None
    assert get_current_school() is None


@pytest.mark.parametrize("route,method,required,dev_open", [
    ("/api/auth/tenant-metadata/", "get", True, False),
    ("/api/v1/tenant-cache-regression/", "options", True, False),
    ("/api/v1/tenant-cache-regression/", "get", False, False),
    ("/internal/tenant-metadata/", "get", True, False),
    ("/api/v1/dashboards/tenant-metadata/", "get", True, True),
])
def test_bypassed_guard_still_refreshes_authenticated_metadata(
    records, settings, route, method, required, dev_open
):
    settings.TENANT_HEADER_REQUIRED = required
    settings.CROWN_DEV_OPEN_API = dev_open
    request = _request_with_stale_bindings(
        records, selected_school=records.school_a, route=route, method=method
    )
    assert request.user.pk == records.user.pk
    for target in (request, request._request):
        assert target.crown_tenant.actor_type == "user"
        assert target.crown_tenant.principal_school_id == records.school_a.id
        assert target.crown_tenant.school_id == records.school_a.id
        assert target.crown_tenant.school is None
        assert get_tenant_school_id(target) == records.school_a.id
        for attr in ("school", "school_id", "tenant_school", "_crown_school_override_id"):
            assert getattr(target, attr, None) is None
    assert get_current_school() is None


@pytest.mark.parametrize("case,expected_status", [
    ("own", None), ("foreign", 404), ("support_audit_failure", 503),
])
def test_aad_post_validation_boundary_reconciles_and_preserves_tenant_denials(
    records, monkeypatch, case, expected_status
):
    # Provider validation/user provisioning are isolated boundaries in this test.
    decode = Mock(return_value={"sub": str(records.user.pk)})
    resolve_user = Mock(return_value=records.user)
    monkeypatch.setattr("core.auth.authentication.decode_and_validate_bearer", decode)
    monkeypatch.setattr("core.auth.authentication.get_or_create_user_from_claims", resolve_user)
    if case == "support_audit_failure":
        UserRole.objects.create(user=records.user, school=records.school_a, role_code="SUPPORT")
        monkeypatch.setattr(
            "core.tenant_header_middleware.audit_tenant_decision",
            Mock(side_effect=RuntimeError("synthetic audit unavailable")),
        )
    selected = records.school_a if case == "own" else records.school_b
    request = _request_with_stale_bindings(records, selected_school=selected, aad=True)
    if expected_status is None:
        assert request.user.pk == records.user.pk
        _assert_bound(request, records.school_a, records.school_a)
    else:
        with pytest.raises(TenantContextError) as exc:
            request.user
        assert exc.value.status_code == expected_status
        for target in (request, request._request):
            assert target.crown_tenant.school is None
            for attr in ("school", "school_id", "tenant_school", "_crown_school_override_id"):
                assert getattr(target, attr, None) is None
        assert get_current_school() is None
    decode.assert_called_once()
    resolve_user.assert_called_once()


def test_aad_rejected_validation_never_reconciles_tenant(records, monkeypatch):
    monkeypatch.setattr(
        "core.auth.authentication.decode_and_validate_bearer",
        Mock(side_effect=ValueError("synthetic validation rejection")),
    )
    reconcile = Mock()
    monkeypatch.setattr("core.auth.authentication.reconcile_authenticated_tenant", reconcile)
    request = _request_with_stale_bindings(records, selected_school=records.school_a, aad=True)
    assert AADBearerAuthentication().authenticate(request) is None
    reconcile.assert_not_called()


def test_tenant_jwt_schema_keeps_existing_bearer_security_contract():
    extension = OpenApiAuthenticationExtension.get_match(TenantJWTAuthentication())
    assert extension is not None
    assert extension.get_security_requirement(None) == {"jwtAuth": []}
    assert extension.get_security_definition(None) == {
        "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
    }


def test_real_simplejwt_support_override_alone_cannot_read_household(records):
    UserRole.objects.create(user=records.user, school=records.school_a, role_code="SUPPORT")
    response = _jwt_client(records.user).get(
        f"/api/v1/households/{records.household_b.pk}/",
        HTTP_X_SCHOOL_ID=str(records.school_b.pk),
    )
    assert response.status_code == 404
    assert "Fictional Household" not in str(response.content)
    # Tenant selection is still authorized/audited even though row scope denies
    # the private directory record. Do not conflate the two decisions.
    _assert_bound(response.renderer_context["request"], records.school_b, records.school_a)
    event = AuditEvent.objects.get(action="tenant.context.decision")
    assert event.meta["override_authorized"] is True
    assert event.meta["outcome"] == "authorized"
