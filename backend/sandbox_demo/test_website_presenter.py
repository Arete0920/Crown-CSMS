"""Disposable-DB proof for disabled-by-default fictional website access."""
from unittest.mock import patch

import pytest
from django.db import transaction
from django.test import RequestFactory
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount
from crown_api.jwt_utils import decode_access
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID, presenter_username
from sandbox_demo.website_presenter import (
    DEMO_ORIGIN, DEMO_SCOPE, WebsitePresenterSessionGuardMiddleware,
    website_demo_rate_limit, website_demo_request_allowed,
    website_demo_school,
)


@pytest.mark.django_db
def test_entry_default_off_and_rejects_other_origins(settings, django_assert_num_queries):
    settings.CROWN_WEBSITE_DEMO_ENABLED = False
    client = APIClient()
    with django_assert_num_queries(0):
        assert website_demo_school() is None
    unavailable = client.get("/api/v1/sandbox/website-presenter/")
    assert unavailable.status_code == 503
    assert unavailable.data["available"] is False
    denied = client.post(
        "/api/v1/sandbox/website-presenter/",
        {"role": "teacher"}, format="json", HTTP_ORIGIN="https://evil.example.invalid",
    )
    assert denied.status_code == 403
    assert denied.data["code"] == "website_presenter_origin_denied"
    assert not School.objects.exists()


@pytest.mark.django_db
def test_owned_fictional_role_issued_without_password_or_refresh(
    local_runtime, settings,
):
    prepare_presenter(apply=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True
    with patch("sandbox_demo.website_presenter.require_hosted_presenter"):
        client = APIClient()
        available = client.get("/api/v1/sandbox/website-presenter/")
        assert available.status_code == 200
        assert len(available.data["roles"]) == 9
        session = client.post(
            "/api/v1/sandbox/website-presenter/", {"role": "teacher"},
            format="json", HTTP_ORIGIN=DEMO_ORIGIN,
        )
        assert session.status_code == 201, session.content
        body = session.data
        assert body["demo_scope"] == DEMO_SCOPE
        assert not body.get("refresh")
        assert body["username"] == presenter_username("teacher")
        token = decode_access(body["access"])
        assert token.ok
        assert token.payload["demo_scope"] == DEMO_SCOPE
        actor = UserAccount.objects.get(username=presenter_username("teacher"))
        request = RequestFactory().get("/api/v1/academics/classroom/workspace/")
        assert website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().get("/api/dashboards/summary/")
        assert website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().post("/api/dashboards/summary/")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().post("/api/v1/academics/submissions/")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().post("/api/v1/presenter/admin/resolve-operational-exception/")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().post("/api/v1/auth/token/")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().get("/api/platform/overview")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().post("/api/v1/payments/checkout/")
        assert not website_demo_request_allowed(request, actor, token.payload)
        request = RequestFactory().get(
            "/api/v1/academics/classroom/workspace/",
            HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000001",
        )
        assert not website_demo_request_allowed(request, actor, token.payload)
        user = UserAccount.objects.get(username=presenter_username("teacher"))
        user.is_active = False
        user.save(update_fields=["is_active"])
        assert website_demo_school() is None



@pytest.mark.django_db
def test_jireh_aid_director_grant_preserves_website_readiness_without_role_drift(
    local_runtime, settings,
):
    from django.core.management import call_command
    from io import StringIO
    from core.models import UserRole
    from sandbox_demo.universal_jireh import prepare_presenter_jireh

    call_command("seed_permissions", stdout=StringIO())
    prepare_presenter(apply=True)
    prepare_presenter_jireh(apply=True, aid_only=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True

    with patch("sandbox_demo.website_presenter.require_hosted_presenter"):
        school = website_demo_school()
        assert school is not None
        client = APIClient()
        available = client.get("/api/v1/sandbox/website-presenter/")
        assert available.status_code == 200
        assert available.data["financial_aid_ready"] is False
        issued = client.post(
            "/api/v1/sandbox/website-presenter/", {"role": "parent"},
            format="json", HTTP_ORIGIN=DEMO_ORIGIN,
        )
        assert issued.status_code == 201, issued.content
        assert issued.data["demo_scope"] == DEMO_SCOPE
        with patch("sandbox_demo.buyer_workspace.hosted_buyer_mode", return_value=True):
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {issued.data['access']}",
                HTTP_X_SCHOOL_ID=str(school.pk),
            )
            family = client.get("/api/v1/presenter/jireh/aid/family/")
            assert family.status_code == 200, family.content
            assert sorted(child["name"] for child in family.json()["students"]) == [
                "Avery Reed", "Jordan Reed",
            ]
            assert family.json()["applications"] == []
            denied = client.post("/api/v1/presenter/jireh/aid/family/", {},
                                 format="json")
            assert denied.status_code == 403, denied.content
            from aid.models import AidApplication
            assert not AidApplication.objects.exists()
            client.credentials()

        # The Jireh officer receives exactly one supplementary Aid role;
        # an unrelated parent's supplementary role still blocks issuance.
        parent = UserAccount.objects.get(username=presenter_username("parent"))
        UserRole.objects.create(user=parent, school=school, role_code="FINANCE_DIRECTOR")
        assert website_demo_school() is None
        assert client.get("/api/v1/sandbox/website-presenter/").status_code == 503




@pytest.mark.django_db
def test_website_role_dashboard_reads_are_exact_scoped_and_read_only(
    local_runtime, settings,
):
    prepare_presenter(apply=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True
    role_paths = {
        "school_admin": ("/api/v1/admin/metrics/",),
        "admissions_director": (),
        "finance_director": (),
        "daycare_director": (),
        "daycare_staff": (),
        "teacher": ("/api/v1/teacher/metrics/",),
        "parent": ("/api/v1/parent/metrics/",),
        "student": ("/api/v1/student/metrics/",),
        "board": (
            "/api/v1/board/metrics/", "/api/v1/board/dashboard/",
            "/api/v1/board/snapshots/", "/api/v1/board/packets/",
        ),
    }
    actors = {
        role: UserAccount.objects.get(username=presenter_username(role))
        for role in role_paths
    }
    claims = {
        role: {
            "demo_scope": DEMO_SCOPE, "role": role,
            "sub": str(actor.pk), "school_id": str(UNIVERSAL_SCHOOL_ID),
        }
        for role, actor in actors.items()
    }
    factory = RequestFactory()
    with patch("sandbox_demo.website_presenter.require_hosted_presenter"):
        for role, paths in role_paths.items():
            assert website_demo_request_allowed(
                factory.get("/api/v1/nav/"), actors[role], claims[role]
            )
            assert not website_demo_request_allowed(
                factory.post("/api/v1/nav/"), actors[role], claims[role]
            )
            assert not website_demo_request_allowed(
                factory.get(
                    "/api/v1/nav/",
                    HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000001",
                ),
                actors[role], claims[role],
            )
            for path in paths:
                get = factory.get(path)
                assert website_demo_request_allowed(get, actors[role], claims[role])
                assert not website_demo_request_allowed(
                    factory.post(path), actors[role], claims[role]
                )
                assert not website_demo_request_allowed(
                    factory.get(path, HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000001"),
                    actors[role], claims[role],
                )
                for other_role in role_paths:
                    if other_role != role:
                        assert not website_demo_request_allowed(
                            get, actors[other_role], claims[other_role]
                        )
        for path in (
            "/api/v1/board/packets/1/",
            "/api/v1/nav/private/",
            "/api/v1/board/packet/download/",
            "/api/v1/board/metrics/private/",
        ):
            assert not website_demo_request_allowed(
                factory.get(path), actors["board"], claims["board"]
            )



@pytest.mark.django_db
def test_signed_website_roles_cannot_read_other_personas_sensitive_dashboards(
    local_runtime, settings,
):
    """Exercise middleware, real signed JWTs, persisted grants and legacy aliases."""
    prepare_presenter(apply=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True
    from sandbox_demo.catalog import SANDBOX_PERSONAS

    # Explicit grants make the positive cases stable in an isolated test DB.
    for role_code, code in (
        ("HEAD_OF_SCHOOL", "finance.view"),
        ("HEAD_OF_SCHOOL", "admissions.view"),
        ("FINANCE_DIRECTOR", "finance.view"),
        ("REGISTRAR", "admissions.view"),
        ("HEAD_OF_SCHOOL", "academics.view"),
        ("REGISTRAR", "academics.view"),
        ("TEACHER", "academics.view"),
    ):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(
            role_code=role_code, permission=permission,
        )

    allowed = {
        "finance/summary/": {"school_admin", "finance_director"},
        "admissions/funnel/": {"school_admin", "admissions_director"},
        "academics/enrollment/": {
            "school_admin", "admissions_director", "teacher",
        },
    }
    with patch("sandbox_demo.website_presenter.require_hosted_presenter"), patch(
        "sandbox_demo.buyer_workspace.hosted_buyer_mode", return_value=True,
    ):
        client = APIClient()
        for role in SANDBOX_PERSONAS:
            # Match website credential-omission on persona switches: a prior
            # demo JWT must not authorize the next session-issuance request.
            client.credentials()
            issued = client.post(
                "/api/v1/sandbox/website-presenter/",
                {"role": role}, format="json", HTTP_ORIGIN=DEMO_ORIGIN,
            )
            assert issued.status_code == 201, (role, issued.content)
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {issued.data['access']}",
            )
            for suffix, authorized_roles in allowed.items():
                for prefix in ("/api/v1/dashboards/", "/api/dashboards/"):
                    path = prefix + suffix
                    result = client.get(
                        path, HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID),
                    )
                    expected = 200 if role in authorized_roles else 403
                    assert result.status_code == expected, (
                        role, path, expected, result.content,
                    )
                    blocked = client.post(
                        path, {}, format="json",
                        HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID),
                    )
                    assert blocked.status_code == 403, (role, path, blocked.content)
                    foreign = client.get(
                        path, HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000001",
                    )
                    assert foreign.status_code == 403, (role, path, foreign.content)

            # Five Stage-2 CFO GETs have no underlying role check. The website
            # scope must enforce the school-bound finance grant for every persona.
            actor = UserAccount.objects.get(username=presenter_username(role))
            claims = decode_access(issued.data["access"]).payload
            for route in (
                "kpis/", "chargebacks/", "monthly-summary/", "payout-audit/",
                "dunning/",
            ):
                path = f"/api/v1/finance/{route}"
                expected = role in {"school_admin", "finance_director"}
                assert website_demo_request_allowed(
                    RequestFactory().get(path), actor, claims,
                ) is expected, (role, path)
                if not expected:
                    denied = client.get(
                        path, HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID),
                    )
                    assert denied.status_code == 403, (role, path, denied.content)

        # A privileged-looking URL without a route-grant must fail closed,
        # including the no-slash legacy dashboard resolver alias.
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {issued.data['access']}")
        for path in (
            "/api/v1/dashboards/finance/summary",
            "/api/dashboards/admissions/funnel",
        ):
            assert client.get(
                path, HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID),
            ).status_code == 403


@pytest.mark.django_db
def test_hosted_presenter_requires_scoped_token_even_for_legacy_login(
    local_runtime, settings,
):
    prepare_presenter(apply=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True
    actor = UserAccount.objects.get(username=presenter_username("teacher"))
    request = RequestFactory().get("/api/v1/academics/classroom/workspace/")
    request.user = actor
    request._crown_authenticated = (actor, {
        "typ": "access", "sub": str(actor.pk), "role": "teacher",
        "school_id": str(actor.school_id),
    })
    from django.http import JsonResponse
    middleware = WebsitePresenterSessionGuardMiddleware(
        lambda req: JsonResponse({"ok": True})
    )
    with patch("sandbox_demo.buyer_workspace.hosted_buyer_mode", return_value=True):
        result = middleware(request)
    assert result.status_code == 403


@pytest.mark.django_db
def test_website_presenter_entry_rate_limit_is_bounded(local_runtime):
    from sandbox_demo.models import SandboxEvent
    from sandbox_demo.website_presenter import website_demo_rate_limit
    prepare_presenter(apply=True)
    school = School.objects.get(pk=UNIVERSAL_SCHOOL_ID)
    with transaction.atomic():
        for _ in range(12):
            assert website_demo_rate_limit(school, "teacher")
        assert not website_demo_rate_limit(school, "teacher")
    assert SandboxEvent.objects.filter(
        event="website_presenter_session_issued_v1", school=str(school.pk),
    ).count() == 12

@pytest.mark.django_db
def test_signed_demo_session_cannot_reach_ops_or_foreign_school_over_http(
    local_runtime, settings,
):
    prepare_presenter(apply=True)
    settings.CROWN_WEBSITE_DEMO_ENABLED = True
    with patch("sandbox_demo.website_presenter.require_hosted_presenter"), patch(
        "sandbox_demo.buyer_workspace.hosted_buyer_mode", return_value=True
    ):
        client = APIClient()
        issued = client.post(
            "/api/v1/sandbox/website-presenter/", {"role": "teacher"},
            format="json", HTTP_ORIGIN=DEMO_ORIGIN,
        )
        assert issued.status_code == 201, issued.content
        token = issued.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        allowed = client.get("/api/dashboards/me/", HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID))
        assert allowed.status_code == 200, allowed.content
        assert allowed.data["school_id"] == str(UNIVERSAL_SCHOOL_ID)
        denied = client.post("/api/v1/academics/submissions/", {}, format="json")
        assert denied.status_code == 403
        denied = client.post("/api/v1/presenter/admin/resolve-operational-exception/", {}, format="json")
        assert denied.status_code == 403
        denied = client.get("/api/platform/overview")
        assert denied.status_code == 403
        denied = client.post("/api/v1/auth/token/", {}, format="json")
        assert denied.status_code == 403
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000001",
        )
        denied = client.get("/api/v1/academics/classroom/workspace/")
        assert denied.status_code == 403



@pytest.mark.parametrize("enabled, debug, env, hostname, allowed", [
    (False, False, "prod", "crown-api-prod.azurewebsites.net", True),
    (True, False, "dev", "crown-api-dev.azurewebsites.net", True),
    (True, True, "dev", "crown-api-dev.azurewebsites.net", False),
    (True, False, "prod", "crown-api-dev.azurewebsites.net", False),
    (True, False, "dev", "crown-api-prod.azurewebsites.net", False),
    (True, False, "dev", "crown-api-dev.azurewebsites.net.evil.invalid", False),
    (True, False, "dev", "", False),
])
def test_website_demo_flag_only_accepts_hardened_dev_runtime(
    enabled, debug, env, hostname, allowed,
):
    from crown_api.settings import _assert_website_demo_dev_only

    if allowed:
        _assert_website_demo_dev_only(
            enabled, debug=debug, crown_env=env, hostname=hostname,
        )
    else:
        with pytest.raises(RuntimeError, match="hardened crown-api-dev only"):
            _assert_website_demo_dev_only(
                enabled, debug=debug, crown_env=env, hostname=hostname,
            )
