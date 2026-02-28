import pytest

SCHOOL_ID = "00000000-0000-0000-0000-000000000000"

BOARD_URLS = [
    "/api/board/metrics/",
    "/api/board/dashboard/",
    "/api/board/snapshots/",
    "/api/board/packets/",
]


@pytest.mark.django_db
@pytest.mark.parametrize("url", BOARD_URLS)
def test_post_not_allowed_unauthenticated(client, url):
    resp = client.post(url, {}, content_type="application/json", HTTP_X_SCHOOL_ID=SCHOOL_ID)
    # Must be 401 (unauthenticated) or 405 (method not allowed checked before auth)
    assert resp.status_code in (401, 403, 405)


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_write_methods_not_allowed_on_metrics(client, django_user_model, method):
    user = django_user_model.objects.create_user(username=f"getonly_{method}", password="x")
    client.force_login(user)
    call = getattr(client, method)
    resp = call(
        "/api/board/metrics/",
        {},
        content_type="application/json",
        HTTP_X_SCHOOL_ID=SCHOOL_ID,
    )
    assert resp.status_code in (403, 405)
