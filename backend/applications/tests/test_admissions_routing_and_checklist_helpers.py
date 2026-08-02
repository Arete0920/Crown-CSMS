from types import SimpleNamespace
from uuid import UUID, uuid4

from applications import views_admissions as admissions


class _Query:
    def __init__(self, results):
        self.results = list(results)
        self.only_args = None
        self.ordering = None

    def only(self, *args):
        self.only_args = args
        return self

    def order_by(self, *args):
        self.ordering = args
        return self

    def first(self):
        return self.results[0] if self.results else None


class _Manager:
    def __init__(self, result_sets):
        self.result_sets = list(result_sets)
        self.calls = []

    def filter(self, **kwargs):
        self.calls.append(kwargs)
        results = self.result_sets.pop(0) if self.result_sets else []
        return _Query(results)


def test_request_payload_or_empty_handles_dict_non_dict_and_exception():
    assert admissions._request_payload_or_empty(SimpleNamespace(data={"ok": True})) == {"ok": True}
    assert admissions._request_payload_or_empty(SimpleNamespace(data=["not", "a", "dict"])) == {}

    class _BrokenRequest:
        @property
        def data(self):
            raise RuntimeError("unavailable")

    assert admissions._request_payload_or_empty(_BrokenRequest()) == {}


def test_normalize_checklist_token_accepts_uuid_and_rejects_empty_sentinels():
    token = uuid4()

    assert admissions._normalize_checklist_token(f"  {token}  ") == str(token)
    assert UUID(admissions._normalize_checklist_token(str(token))) == token

    for value in (None, "", "  ", "none", "NULL", "undefined", "not-a-uuid"):
        assert admissions._normalize_checklist_token(value) == ""


def test_checklist_application_error_requires_identifier_or_tenant():
    missing = admissions._checklist_application_error("", "", None)
    assert missing.status_code == 400
    assert missing.data == {"detail": "application_id or checklist_key is required."}

    missing_tenant = admissions._checklist_application_error(str(uuid4()), "", None)
    assert missing_tenant.status_code == 400
    assert missing_tenant.data == {
        "detail": "application_id without checklist_key requires X-School-Id.",
        "code": "missing_tenant",
    }

    assert admissions._checklist_application_error("", str(uuid4()), None) is None
    assert admissions._checklist_application_error(str(uuid4()), "", str(uuid4())) is None


def test_lookup_checklist_application_builds_expected_filter_sets(monkeypatch):
    expected = [SimpleNamespace(id="both"), SimpleNamespace(id="application"), SimpleNamespace(id="key")]
    manager = _Manager([[expected[0]], [expected[1]], [expected[2]]])
    monkeypatch.setattr(admissions.Application, "objects", manager)

    school_id = str(uuid4())
    application_id = str(uuid4())
    checklist_key = str(uuid4())

    assert admissions._lookup_checklist_application(school_id, application_id, checklist_key) is expected[0]
    assert admissions._lookup_checklist_application(school_id, application_id, "") is expected[1]
    assert admissions._lookup_checklist_application(None, "", checklist_key) is expected[2]
    assert admissions._lookup_checklist_application(None, "", "") is None

    assert manager.calls == [
        {
            "checklist_access_key": checklist_key,
            "school_id": school_id,
            "id": application_id,
        },
        {"school_id": school_id, "id": application_id},
        {"checklist_access_key": checklist_key},
    ]


def test_auto_complete_demo_checklists_respects_enabled_flag(monkeypatch):
    promoted = []
    monkeypatch.setattr(admissions, "_promote_checklist_for_demo", promoted.append)
    applications = [SimpleNamespace(id="one"), SimpleNamespace(id="two")]

    admissions._auto_complete_demo_checklists(applications, False)
    assert promoted == []

    admissions._auto_complete_demo_checklists(applications, True)
    assert promoted == applications


def test_resolve_school_returns_existing_request_school_without_lookup():
    school = SimpleNamespace(id=uuid4(), name="Existing School")
    request = SimpleNamespace(school=school)

    resolved, error = admissions._resolve_school(request)

    assert resolved is school
    assert error is None


def test_resolve_school_rejects_invalid_and_missing_tenant(monkeypatch):
    request = SimpleNamespace()

    monkeypatch.setattr(
        admissions,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(school_id=None, source="header_invalid"),
    )
    school, error = admissions._resolve_school(request)
    assert school is None
    assert error.status_code == 400
    assert error.data["code"] == "invalid_tenant_header"

    monkeypatch.setattr(
        admissions,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(school_id=None, source="missing"),
    )
    school, error = admissions._resolve_school(request)
    assert school is None
    assert error.status_code == 400
    assert error.data["code"] == "missing_tenant"


def test_resolve_school_handles_unknown_and_successful_lookup(monkeypatch):
    school_id = uuid4()
    request = SimpleNamespace()

    monkeypatch.setattr(
        admissions,
        "resolve_tenant_school_id",
        lambda _request: SimpleNamespace(school_id=str(school_id), source="header"),
    )

    unknown_manager = _Manager([[]])
    monkeypatch.setattr(admissions.School, "objects", unknown_manager)
    school, error = admissions._resolve_school(request)
    assert school is None
    assert error.status_code == 404
    assert error.data["code"] == "invalid_tenant"
    assert unknown_manager.calls == [{"pk": str(school_id)}]

    resolved_school = SimpleNamespace(id=school_id, name="Heritage Christian Academy")
    manager = _Manager([[resolved_school]])
    monkeypatch.setattr(admissions.School, "objects", manager)
    school, error = admissions._resolve_school(request)

    assert school is resolved_school
    assert error is None
    assert request.school is resolved_school
    assert request.school_id == str(school_id)
    assert manager.calls == [{"pk": str(school_id)}]


def test_resolve_school_for_submit_preserves_invalid_header(monkeypatch):
    tenant_error = admissions.Response(
        {"detail": "Invalid X-School-Id (must be UUID).", "code": "invalid_tenant_header"},
        status=400,
    )
    monkeypatch.setattr(admissions, "_resolve_school", lambda _request: (None, tenant_error))

    school, error = admissions._resolve_school_for_submit(SimpleNamespace(), {"inquiry": {"campus": "Heritage"}})

    assert school is None
    assert error is tenant_error


def test_resolve_school_for_submit_requires_campus_when_tenant_missing(monkeypatch):
    tenant_error = admissions.Response(
        {"detail": "Missing required header: X-School-Id.", "code": "missing_tenant"},
        status=400,
    )
    monkeypatch.setattr(admissions, "_resolve_school", lambda _request: (None, tenant_error))

    school, error = admissions._resolve_school_for_submit(SimpleNamespace(), {})

    assert school is None
    assert error.status_code == 400
    assert error.data["code"] == "missing_tenant"
    assert "inquiry.campus" in error.data["detail"]


def test_resolve_school_for_submit_uses_exact_then_contains_lookup(monkeypatch):
    tenant_error = admissions.Response(
        {"detail": "Missing required header: X-School-Id.", "code": "missing_tenant"},
        status=400,
    )
    monkeypatch.setattr(admissions, "_resolve_school", lambda _request: (None, tenant_error))

    exact_school = SimpleNamespace(id=uuid4(), name="Heritage Christian Academy")
    exact_manager = _Manager([[exact_school]])
    monkeypatch.setattr(admissions.School, "objects", exact_manager)
    request = SimpleNamespace()

    school, error = admissions._resolve_school_for_submit(
        request,
        {"inquiry": {"campus": " Heritage Christian Academy "}},
    )

    assert school is exact_school
    assert error is None
    assert request.school is exact_school
    assert request.school_id == str(exact_school.id)
    assert exact_manager.calls == [{"name__iexact": "Heritage Christian Academy"}]

    contains_school = SimpleNamespace(id=uuid4(), name="Heritage Christian Academy")
    contains_manager = _Manager([[], [contains_school]])
    monkeypatch.setattr(admissions.School, "objects", contains_manager)
    request = SimpleNamespace()

    school, error = admissions._resolve_school_for_submit(
        request,
        {"inquiry": {"campus": "Heritage"}},
    )

    assert school is contains_school
    assert error is None
    assert request.school is contains_school
    assert request.school_id == str(contains_school.id)
    assert contains_manager.calls == [
        {"name__iexact": "Heritage"},
        {"name__icontains": "Heritage"},
    ]


def test_resolve_school_for_submit_rejects_unknown_campus(monkeypatch):
    tenant_error = admissions.Response(
        {"detail": "Missing required header: X-School-Id.", "code": "missing_tenant"},
        status=400,
    )
    monkeypatch.setattr(admissions, "_resolve_school", lambda _request: (None, tenant_error))
    manager = _Manager([[], []])
    monkeypatch.setattr(admissions.School, "objects", manager)

    school, error = admissions._resolve_school_for_submit(
        SimpleNamespace(),
        {"inquiry": {"campus": "Unknown Campus"}},
    )

    assert school is None
    assert error.status_code == 404
    assert error.data == {
        "detail": "Unable to resolve school for campus 'Unknown Campus'.",
        "code": "invalid_tenant",
    }
