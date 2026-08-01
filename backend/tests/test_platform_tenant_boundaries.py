from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from rest_framework.exceptions import PermissionDenied

from hr import api as hr_api
from pdhub import api as pd_api
from safety import api as safety_api


MODULE_CASES = [
    (hr_api, hr_api.EmployeeViewSet, hr_api.Employee, "school-hr"),
    (pd_api, pd_api.PDResourceViewSet, pd_api.PDResource, "school-pd"),
    (pd_api, pd_api.PDSessionViewSet, pd_api.PDSession, "school-pd"),
    (safety_api, safety_api.IncidentViewSet, safety_api.IncidentReport, "school-safety"),
]


@pytest.mark.parametrize("module", [hr_api, pd_api, safety_api])
def test_require_school_fails_closed_without_tenant_context(module):
    with pytest.raises(PermissionDenied, match="Tenant context required"):
        module._require_school(SimpleNamespace())


@pytest.mark.parametrize("module", [hr_api, pd_api, safety_api])
def test_require_school_returns_request_school(module):
    school = SimpleNamespace(id="school-a")

    assert module._require_school(SimpleNamespace(school=school)) is school


@pytest.mark.parametrize("module,viewset_class,model,school_id", MODULE_CASES)
def test_viewset_queryset_is_scoped_to_request_school(
    monkeypatch,
    module,
    viewset_class,
    model,
    school_id,
):
    expected = object()
    manager = MagicMock()
    manager.filter.return_value = expected
    monkeypatch.setattr(model, "objects", manager)

    view = viewset_class()
    view.request = SimpleNamespace(school=SimpleNamespace(id=school_id))

    assert view.get_queryset() is expected
    manager.filter.assert_called_once_with(school_id=school_id)


@pytest.mark.parametrize(
    "module,viewset_class,model,event_name,extra_key",
    [
        (hr_api, hr_api.EmployeeViewSet, hr_api.Employee, "hr.employee.created", "employee_id"),
        (pd_api, pd_api.PDResourceViewSet, pd_api.PDResource, "pd.resource.created", "resource_id"),
        (pd_api, pd_api.PDSessionViewSet, pd_api.PDSession, "pd.session.created", "session_id"),
        (
            safety_api,
            safety_api.IncidentViewSet,
            safety_api.IncidentReport,
            "safety.incident.created",
            "incident_id",
        ),
    ],
)
def test_perform_create_preserves_school_scope_and_audit_event(
    monkeypatch,
    module,
    viewset_class,
    model,
    event_name,
    extra_key,
):
    school = SimpleNamespace(id="school-a")
    user = SimpleNamespace(id="user-a")
    instance = SimpleNamespace(id="record-a")
    serializer = MagicMock()
    serializer.save.return_value = instance
    audit = MagicMock()
    monkeypatch.setattr(module, "audit_event", audit)

    view = viewset_class()
    view.request = SimpleNamespace(school=school, user=user)
    view.perform_create(serializer)

    serializer.save.assert_called_once_with(school_id="school-a")
    audit.assert_called_once_with(
        event_name,
        user=user,
        school=school,
        extra={extra_key: "record-a"},
    )


@pytest.mark.parametrize(
    "module,viewset_class,event_name,extra_key",
    [
        (hr_api, hr_api.EmployeeViewSet, "hr.employee.updated", "employee_id"),
        (pd_api, pd_api.PDResourceViewSet, "pd.resource.updated", "resource_id"),
        (pd_api, pd_api.PDSessionViewSet, "pd.session.updated", "session_id"),
        (safety_api, safety_api.IncidentViewSet, "safety.incident.updated", "incident_id"),
    ],
)
def test_perform_update_audits_against_request_school(
    monkeypatch,
    module,
    viewset_class,
    event_name,
    extra_key,
):
    school = SimpleNamespace(id="school-a")
    user = SimpleNamespace(id="user-a")
    instance = SimpleNamespace(id="record-a")
    serializer = MagicMock()
    serializer.save.return_value = instance
    audit = MagicMock()
    monkeypatch.setattr(module, "audit_event", audit)

    view = viewset_class()
    view.request = SimpleNamespace(school=school, user=user)
    view.perform_update(serializer)

    serializer.save.assert_called_once_with()
    audit.assert_called_once_with(
        event_name,
        user=user,
        school=school,
        extra={extra_key: "record-a"},
    )


@pytest.mark.parametrize(
    "module,viewset_class,event_name,extra_key",
    [
        (hr_api, hr_api.EmployeeViewSet, "hr.employee.deleted", "employee_id"),
        (pd_api, pd_api.PDResourceViewSet, "pd.resource.deleted", "resource_id"),
        (pd_api, pd_api.PDSessionViewSet, "pd.session.deleted", "session_id"),
        (safety_api, safety_api.IncidentViewSet, "safety.incident.deleted", "incident_id"),
    ],
)
def test_perform_destroy_audits_then_deletes(
    monkeypatch,
    module,
    viewset_class,
    event_name,
    extra_key,
):
    school = SimpleNamespace(id="school-a")
    user = SimpleNamespace(id="user-a")
    instance = MagicMock()
    instance.id = "record-a"
    audit = MagicMock()
    sequence = MagicMock()
    sequence.attach_mock(audit, "audit")
    sequence.attach_mock(instance.delete, "delete")
    monkeypatch.setattr(module, "audit_event", audit)

    view = viewset_class()
    view.request = SimpleNamespace(school=school, user=user)
    view.perform_destroy(instance)

    sequence.assert_has_calls(
        [
            call.audit(
                event_name,
                user=user,
                school=school,
                extra={extra_key: "record-a"},
            ),
            call.delete(),
        ]
    )
    assert sequence.mock_calls == [
        call.audit(
            event_name,
            user=user,
            school=school,
            extra={extra_key: "record-a"},
        ),
        call.delete(),
    ]
