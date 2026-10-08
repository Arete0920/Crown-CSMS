"""
Regression tests for ApiExceptionMiddleware.

Verifies:
 - Http404 raised in a view → 404 JSON response (not 500)
 - Unhandled RuntimeError → 500 JSON response
 - /api/ops/summary/ and /api/ops/alerts/ return 404 in prod environment
"""
import json
import os
import pytest
from django.http import Http404, JsonResponse
from django.test import RequestFactory, override_settings


# ---------------------------------------------------------------------------
# Unit tests for the middleware in isolation
# ---------------------------------------------------------------------------

def _make_middleware():
    from crown_api.middleware.api_exceptions import ApiExceptionMiddleware
    # get_response is unused for process_exception unit tests
    return ApiExceptionMiddleware(get_response=lambda r: r)


def test_http404_returns_404_json():
    """Http404 must produce a 404 JSON response, NOT 500."""
    mw = _make_middleware()
    rf = RequestFactory()
    request = rf.get("/api/ops/summary/")

    response = mw.process_exception(request, Http404("not found"))

    assert response.status_code == 404
    body = json.loads(response.content)
    assert body["ok"] is False
    assert body["error"] == "Not Found"
    assert "request_id" in body


@override_settings(DEBUG=False)
def test_runtime_error_returns_500_json():
    """Unhandled RuntimeError must still produce a 500 JSON response."""
    mw = _make_middleware()
    rf = RequestFactory()
    request = rf.get("/api/something/")

    response = mw.process_exception(request, RuntimeError("boom"))

    assert response.status_code == 500
    body = json.loads(response.content)
    assert body["ok"] is False
    assert body["error"] == "Internal Server Error"
    assert "detail" not in body  # DEBUG=False should hide detail


@override_settings(DEBUG=True)
def test_runtime_error_includes_detail_in_debug():
    """In DEBUG mode, the detail field is included in 500 responses."""
    mw = _make_middleware()
    rf = RequestFactory()
    request = rf.get("/api/something/")

    response = mw.process_exception(request, RuntimeError("debug detail here"))

    assert response.status_code == 500
    body = json.loads(response.content)
    assert "debug detail here" in body.get("detail", "")


# ---------------------------------------------------------------------------
# Integration tests: ops endpoints return 404 in production environment
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ops_summary_returns_404_in_prod(client):
    """
    /api/ops/summary/ must return 404 (not 500) when ENVIRONMENT=production.
    This is the regression for the _dev_only() / ApiExceptionMiddleware bug.
    """
    with override_settings(DEBUG=False):
        with _prod_env():
            resp = client.get("/api/ops/summary/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_ops_alerts_returns_404_in_prod(client):
    """
    /api/ops/alerts/ must return 404 (not 500) when ENVIRONMENT=production.
    """
    with override_settings(DEBUG=False):
        with _prod_env():
            resp = client.get("/api/ops/alerts/")
    assert resp.status_code == 404


class _prod_env:
    """Context manager that sets ENVIRONMENT=production and cleans up."""
    def __enter__(self):
        os.environ["ENVIRONMENT"] = "production"
        return self

    def __exit__(self, *_):
        os.environ.pop("ENVIRONMENT", None)


@pytest.mark.parametrize("exception_class, expected_status", [
    ("MissingSchoolContext", 400),
    ("NotFound", 404),
    ("PermissionDenied", 403),
])
@override_settings(DEBUG=False)
def test_expected_api_denial_preserves_status(exception_class, expected_status):
    from households.scoping import MissingSchoolContext
    from rest_framework.exceptions import NotFound, PermissionDenied

    exceptions = {
        "MissingSchoolContext": MissingSchoolContext,
        "NotFound": NotFound,
        "PermissionDenied": PermissionDenied,
    }
    request = RequestFactory().get("/api/v1/admin/metrics/")
    response = _make_middleware().process_exception(request, exceptions[exception_class]())
    assert response.status_code == expected_status
    assert json.loads(response.content)
    assert response["X-Request-Id"]


@override_settings(DEBUG=False)
def test_server_api_exception_keeps_internal_detail_private():
    from rest_framework.exceptions import APIException

    request = RequestFactory().get("/api/v1/admin/metrics/")
    response = _make_middleware().process_exception(request, APIException("private server detail"))
    assert response.status_code == 500
    assert b"private server detail" not in response.content
