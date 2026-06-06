from django.test import RequestFactory

from crown_api.request_parsing import parse_bounded_int, parse_json_object


def test_parse_json_object_accepts_json_object():
    request = RequestFactory().post(
        "/api/auth/login/",
        data='{"email":"admin@example.com"}',
        content_type="application/json",
    )

    assert parse_json_object(request) == {"email": "admin@example.com"}


def test_parse_json_object_rejects_non_object_payloads():
    request = RequestFactory().post(
        "/api/auth/login/",
        data='["admin@example.com"]',
        content_type="application/json",
    )

    assert parse_json_object(request) is None


def test_parse_json_object_rejects_invalid_utf8():
    request = RequestFactory().post(
        "/api/auth/login/",
        data=b"\xff",
        content_type="application/json",
    )

    assert parse_json_object(request) is None


def test_parse_bounded_int_clamps_and_defaults():
    assert parse_bounded_int("90", default=25, min_value=1, max_value=100) == 90
    assert parse_bounded_int("500", default=25, min_value=1, max_value=100) == 100
    assert parse_bounded_int("bad", default=25, min_value=1, max_value=100) == 25
