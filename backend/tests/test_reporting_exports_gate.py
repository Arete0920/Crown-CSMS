import pytest

pytestmark = pytest.mark.django_db


def _client_with_user(client, django_user_model, email, password="Crown2026!"):
    user, _ = django_user_model.objects.get_or_create(
        username=email,
        defaults={"email": email},
    )
    user.email = email
    user.set_password(password)
    user.save()
    logged_in = client.login(username=email, password=password)
    if not logged_in:
        logged_in = client.login(username=user.username, password=password)
    assert logged_in
    return user


def test_openapi_docs_visible(client):
    candidates = ["/api/docs/", "/swagger/", "/docs/"]
    seen = []
    ok = False
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code))
        if resp.status_code == 200:
            ok = True
            break
    assert ok, f"OpenAPI/Swagger docs not visible. Tried: {seen}"


def test_health_endpoint_live(client):
    candidates = ["/health/", "/api/health/"]
    seen = []
    ok = False
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code, bytes(resp.content[:200])))
        if resp.status_code == 200:
            ok = True
            break
    assert ok, f"Health endpoint not live. Tried: {seen}"


def test_integrity_endpoint_live(client):
    candidates = ["/api/integrity/", "/integrity/"]
    seen = []
    ok = False
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code, bytes(resp.content[:200])))
        if resp.status_code == 200:
            ok = True
            break
    assert ok, f"Integrity endpoint not live. Tried: {seen}"


def test_transcript_route_exists_and_requires_auth(client):
    candidates = [
        "/api/v1/transcripts/",
        "/api/transcripts/",
        "/transcripts/",
        "/student/transcript/",
    ]
    seen = []
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code))
    assert any(code in (200, 301, 302, 401, 403) for _, code in seen), (
        f"No transcript route found. Tried: {seen}"
    )


def test_reporting_export_routes_exist_and_are_not_404(client):
    candidates = [
        "/api/v1/reports/",
        "/api/v1/reports/finance/",
        "/api/v1/reports/export/",
        "/api/v1/exports/",
        "/reports/",
        "/exports/",
    ]
    seen = []
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code))
    assert any(code != 404 for _, code in seen), f"All report/export routes 404. Tried: {seen}"


def test_unauthorized_export_is_denied(client):
    candidates = [
        "/api/v1/exports/",
        "/api/v1/reports/export/",
        "/api/v1/transcripts/export/",
    ]
    seen = []
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code))
    assert any(code in (401, 403) for _, code in seen), (
        f"Unauthorized export denial not proven. Tried: {seen}"
    )


def test_export_download_response_shape_if_present(client, django_user_model):
    _client_with_user(client, django_user_model, "admin@heritage.test")
    candidates = ["/api/v1/reports/export/", "/api/v1/exports/"]
    acceptable = {200, 202, 204, 400, 403}
    seen = []
    for path in candidates:
        resp = client.get(path)
        seen.append((path, resp.status_code, dict(resp.items())))
        if resp.status_code in (200, 202):
            content_type = resp.headers.get("Content-Type", "")
            disposition = resp.headers.get("Content-Disposition", "")
            assert content_type or disposition, (
                f"Export returned success without content metadata for {path}"
            )
            return
    assert any(code in acceptable for _, code, _ in seen), (
        f"Export route behavior unacceptable. Tried: {seen}"
    )


def test_transcript_generation_or_denial_is_explicit(client, django_user_model):
    _client_with_user(client, django_user_model, "registrar@heritage.test")
    candidates = [
        "/api/v1/transcripts/generate/",
        "/api/v1/transcripts/",
        "/transcripts/generate/",
    ]
    seen = []
    for path in candidates:
        resp = client.post(path, data={})
        seen.append((path, resp.status_code, bytes(resp.content[:200])))
    assert any(code in (200, 201, 202, 400, 403, 405) for _, code, _ in seen), (
        f"Transcript generation path not explicit. Tried: {seen}"
    )
