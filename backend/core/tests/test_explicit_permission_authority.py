"""Negative authorization proof for missing scope and implicit mutation grants."""

import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import CrownPermission, RolePermission, School, UserRole
from core.permissions import CrownModulePermission, RoleRequired, user_has_permission

pytestmark = pytest.mark.django_db


@pytest.fixture
def principal():
    school = School.objects.create(name="Explicit authority school")
    user = get_user_model().objects.create_user(username=f"authority-{uuid.uuid4()}")
    UserRole.objects.create(user=user, school=school, role_code="TEACHER")
    for code in ("advancement.view", "advancement.edit"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.filter(role_code="TEACHER", permission=permission).delete()
    permission = CrownPermission.objects.get(code="advancement.view")
    RolePermission.objects.create(role_code="TEACHER", permission=permission)
    return user, school


def request_for(user, school, method="get", data=None):
    request = getattr(APIRequestFactory(), method)("/authority/", data=data or {}, format="json")
    request.user = user
    request.school = school
    force_authenticate(request, user=user)
    return request


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_read_permission_does_not_authorize_mutation(principal, method):
    user, school = principal
    permission = CrownModulePermission("advancement.view")()
    assert not permission.has_permission(request_for(user, school, method), object())


def test_read_only_permission_still_allows_read(principal):
    user, school = principal
    assert CrownModulePermission("advancement.view")().has_permission(request_for(user, school), object())


def test_explicit_action_permission_allows_mutation(principal):
    user, school = principal
    permission = CrownPermission.objects.get(code="advancement.edit")
    RolePermission.objects.create(role_code="TEACHER", permission=permission)
    assert CrownModulePermission("advancement.view", write_code="advancement.edit")().has_permission(
        request_for(user, school, "post"), object()
    )


def test_inactive_principal_cannot_use_existing_grant(principal):
    user, school = principal
    user.is_active = False
    assert not user_has_permission(user, "advancement.view", school=school)
    assert not CrownModulePermission("advancement.view")().has_permission(request_for(user, school), object())


def test_missing_school_does_not_borrow_any_school_role(principal):
    user, school = principal
    assert not user_has_permission(user, "advancement.view")
    other_school = School.objects.create(name="Other authority school")
    assert not user_has_permission(user, "advancement.view", school=other_school)



def test_principal_school_resolves_without_redundant_header(principal):
    user, school = principal
    user.school = school
    user.save(update_fields=["school"])
    permission = CrownModulePermission("advancement.view")()
    request = APIRequestFactory().get("/api/v1/advancement/example/")
    request.user = user
    force_authenticate(request, user=user)
    assert permission.has_permission(request, object())
    assert request.school.id == school.id


def test_explicit_wizard_header_requirement_is_preserved(principal):
    user, school = principal
    user.school = school
    user.save(update_fields=["school"])
    permission = CrownModulePermission("advancement.view")()
    request = APIRequestFactory().get("/api/v1/scheduling-wizard/session/")
    request.user = user
    force_authenticate(request, user=user)
    from households.scoping import MissingSchoolContext

    with pytest.raises(MissingSchoolContext):
        permission.has_permission(request, object())

def test_role_required_without_configuration_denies(principal):
    user, school = principal
    assert not RoleRequired().has_permission(request_for(user, school), object())


def test_viewer_cannot_hold_seats_or_call_mutation_service(principal):
    from advancement.api import seating_hold_strict

    user, school = principal
    with patch("advancement.services_stage3_1.hold_seats_strict") as hold:
        response = seating_hold_strict(request_for(user, school, "post", {
            "event_id": str(uuid.uuid4()), "seat_ids": [str(uuid.uuid4())], "email": "viewer@example.test",
        }))
    assert response.status_code == 403
    hold.assert_not_called()


def test_section_price_viewer_denied_and_editor_can_update(principal):
    from advancement.api import event_section_prices
    from advancement.models_stage3_3 import EventSectionPrice

    user, school = principal
    event_id = uuid.uuid4()
    data = {"section": "Main", "price_cents": 2500}
    response = event_section_prices(request_for(user, school, "post", data), event_id=event_id)
    assert response.status_code == 403
    assert not EventSectionPrice.objects.filter(school_id=school.id, event_id=event_id).exists()
    RolePermission.objects.create(role_code="TEACHER", permission=CrownPermission.objects.get(code="advancement.edit"))
    response = event_section_prices(request_for(user, school, "post", data), event_id=event_id)
    assert response.status_code == 201
    assert EventSectionPrice.objects.get(school_id=school.id, event_id=event_id).price_cents == 2500


def test_runtime_permission_consumers_declare_scope_and_mutation_intent():
    """New routes cannot accidentally reintroduce permissive shared defaults."""
    import ast
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2]
    violations = []
    for path in backend.rglob("*.py"):
        if any(part in {"tests", "migrations", "quarantine_old_tests"} for part in path.parts):
            continue
        if path.name.startswith("test_") or path.name in {"tests.py", "conftest.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "user_has_permission":
                if len(node.args) < 3 and not any(keyword.arg == "school" for keyword in node.keywords):
                    violations.append(f"{path.relative_to(backend)}:{node.lineno}: permission lookup without school")
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            mutates = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "api_view":
                    mutates = any(isinstance(value, ast.Constant) and value.value in {"POST", "PUT", "PATCH", "DELETE"}
                                  for arg in decorator.args for value in ast.walk(arg))
            if mutates:
                for decorator in node.decorator_list:
                    for call in ast.walk(decorator):
                        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "CrownModulePermission":
                            if len(call.args) < 2 and not any(keyword.arg == "write_code" for keyword in call.keywords):
                                violations.append(f"{path.relative_to(backend)}:{node.lineno}: mutation without write code")
    assert not violations, "\n".join(violations)


def test_privileged_advancement_mutations_require_explicit_edit_authority():
    """Privileged advancement mutations may not fall back to authentication-only access."""
    import ast
    from pathlib import Path

    source_path = Path(__file__).resolve().parents[2] / "advancement" / "api.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8-sig"))
    privileged = {
        "gift_mark_paid",
        "pledge_cancel",
        "sponsorship_mark_paid",
        "qr_checkin",
        "moves_transition",
        "seating_set_layout",
        "seating_assign",
        "sponsorship_log_impressions",
    }
    found = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in privileged:
            continue
        found.add(node.name)
        permission_calls = [
            call
            for decorator in node.decorator_list
            for call in ast.walk(decorator)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "CrownModulePermission"
        ]
        assert permission_calls, f"{node.name} lacks CrownModulePermission"
        call = permission_calls[0]
        write_code = next(
            (kw.value.value for kw in call.keywords if kw.arg == "write_code" and isinstance(kw.value, ast.Constant)),
            None,
        )
        assert write_code == "advancement.edit", f"{node.name} lacks advancement.edit mutation authority"

    assert found == privileged


def test_advancement_order_status_resolves_tenant_before_query():
    """Order status must bind tenant context before referencing school-scoped data."""
    import ast
    from pathlib import Path

    source_path = Path(__file__).resolve().parents[2] / "advancement" / "api.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8-sig"))
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "order_status")
    assignments = [
        item for item in node.body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "school" for target in item.targets)
    ]
    assert assignments, "order_status must resolve request school before querying"


def test_view_only_principal_cannot_call_privileged_advancement_mutations(principal):
    from advancement import api as advancement_api

    user, school = principal
    cases = (
        (advancement_api.gift_mark_paid, (uuid.uuid4(),)),
        (advancement_api.pledge_cancel, (uuid.uuid4(),)),
        (advancement_api.sponsorship_mark_paid, (uuid.uuid4(),)),
        (advancement_api.qr_checkin, ()),
        (advancement_api.moves_transition, ()),
        (advancement_api.seating_set_layout, ()),
        (advancement_api.seating_assign, ()),
        (advancement_api.sponsorship_log_impressions, ()),
    )
    for view, args in cases:
        response = view(request_for(user, school, "post"), *args)
        assert response.status_code == 403, view.__name__
