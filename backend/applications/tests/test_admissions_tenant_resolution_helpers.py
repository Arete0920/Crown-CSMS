from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from applications import views_admissions as views


def _request(**overrides):
    values = {
        "query_params": {},
        "headers": {},
        "method": "GET",
        "data": {},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_resolve_school_uses_middleware_resolved_school(monkeypatch):
    school = SimpleNamespace(id=uuid4(), name="Heritage Christian Academy")
    request = _request(school=school)
    resolver = MagicMock()
    monkeypatch.setattr(views, "resolve_tenant_school_id", resolver)

    resolved, error = views._resolve_school(request)

    assert resolved is school
    assert error is None
    resolver.assert_not_called()


def test_resolve_school_rejects_malformed_tenant_header(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        views,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(source="header_invalid", school_id=None),
    )

    school, error = views._resolve_school(request)

    assert school is None
    assert error.status_code == 400
    assert error.data == {
        "detail": "Invalid X-School-Id (must be UUID).",
        "code": "invalid_tenant_header",
    }


def test_resolve_school_requires_tenant_when_no_school_is_resolved(monkeypatch):
    request = _request()
    monkeypatch.setattr(
        views,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(source="none", school_id=None),
    )

    school, error = views._resolve_school(request)

    assert school is None
    assert error.status_code == 400
    assert error.data["code"] == "missing_tenant"


def test_resolve_school_rejects_unknown_tenant(monkeypatch):
    school_id = uuid4()
    request = _request()
    query = MagicMock()
    query.filter.return_value.only.return_value.first.return_value = None
    monkeypatch.setattr(views, "School", SimpleNamespace(objects=query))
    monkeypatch.setattr(
        views,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(source="header", school_id=school_id),
    )

    school, error = views._resolve_school(request)

    assert school is None
    assert error.status_code == 404
    assert error.data["code"] == "invalid_tenant"
    query.filter.assert_called_once_with(pk=school_id)


def test_resolve_school_sets_request_tenant_context(monkeypatch):
    school_id = uuid4()
    school = SimpleNamespace(id=school_id, name="Heritage Christian Academy")
    request = _request()
    query = MagicMock()
    query.filter.return_value.only.return_value.first.return_value = school
    monkeypatch.setattr(views, "School", SimpleNamespace(objects=query))
    monkeypatch.setattr(
        views,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(source="header", school_id=school_id),
    )

    resolved, error = views._resolve_school(request)

    assert resolved is school
    assert error is None
    assert request.school is school
    assert request.school_id == str(school_id)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("", ""),
        (" none ", ""),
        ("undefined", ""),
        ("not-a-uuid", ""),
    ],
)
def test_normalize_checklist_token_rejects_non_uuid_values(value, expected):
    assert views._normalize_checklist_token(value) == expected


def test_normalize_checklist_token_canonicalizes_uuid():
    token = uuid4()

    assert views._normalize_checklist_token(f" {token} ") == str(token)


def test_checklist_access_requires_an_identifier():
    error = views._checklist_application_error("", "", None)

    assert error.status_code == 400
    assert error.data["detail"] == "application_id or checklist_key is required."


def test_application_id_without_checklist_key_requires_tenant():
    error = views._checklist_application_error(str(uuid4()), "", None)

    assert error.status_code == 400
    assert error.data["code"] == "missing_tenant"


@pytest.mark.parametrize(
    "query_params",
    [
        {"limit": "not-an-int"},
        {"offset": "not-an-int"},
        {"limit": "0"},
        {"limit": "201"},
        {"offset": "-1"},
    ],
)
def test_parse_pagination_rejects_invalid_values(query_params):
    limit, offset, error = views._parse_pagination(_request(query_params=query_params))

    assert limit is None
    assert offset is None
    assert error.status_code == 400


def test_parse_pagination_returns_bounded_values():
    limit, offset, error = views._parse_pagination(
        _request(query_params={"limit": "50", "offset": "25"})
    )

    assert (limit, offset) == (50, 25)
    assert error is None
