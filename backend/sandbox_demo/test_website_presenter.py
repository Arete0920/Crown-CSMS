"""Disposable-DB proof for disabled-by-default fictional website access."""
from unittest.mock import patch

import pytest
from django.db import transaction
from django.test import RequestFactory
from rest_framework.test import APIClient

from core.models import School, UserAccount
from crown_api.jwt_utils import decode_access
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_identity import presenter_username
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
        request = RequestFactory().post("/api/v1/academics/submissions/")
        assert website_demo_request_allowed(request, actor, token.payload)
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
    school_id = prepare_presenter(apply=True)["school_id"]
    school = School.objects.get(pk=school_id)
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
    cache.clear()
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
