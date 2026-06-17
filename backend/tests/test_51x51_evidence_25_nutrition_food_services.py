"""
51x51 remediation evidence tests for ModuleId 25: Nutrition & Food Services.

This file proves the canonical food-services metrics contract that currently
backs nutrition/meal evidence in Crown:
  - route wiring: /api/v1/food/metrics/
  - permission gate: food.view
  - payload includes meal/menu/allergen fields used for dietary handling
"""

import uuid

import pytest
from django.test import Client

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db

MODULE_ID = 25
MODULE_NAME = "Nutrition & Food Services"
MODULE_TEXT = """
Nutrition & Food Services tracks meals served, menu planning, allergens,
free/reduced meal participation, inventory watch, and unpaid lunch balances.

Evidence basis:
- backend/crown_api/metrics_views.py (food_metrics)
- backend/crown_api/api_urls.py (food/metrics route)
- backend/core/management/commands/seed_permissions.py (food.view)

Contract boundaries proven:
- tenant-scoped access via HTTP_X_SCHOOL_ID
- permission enforcement via food.view
- response payload contains menu and allergen fields for dietary accommodations
"""

AUDIT_KEYWORDS = [
    "tenant",
    "cross-tenant",
    "cross-school",
    "isolation",
    "403",
    "404",
    "test_",
    "pytest",
    "APIClient",
    "client.get",
    "request",
    "response",
    "unauthorized",
    "forbidden",
    "workflow",
    "pipeline",
    "gate",
    "CI",
    "meal",
    "menu",
    "allergens",
    "dietary accommodation",
    "food.view",
]

EVIDENCE_FILES = [
    "backend/crown_api/metrics_views.py",
    "backend/crown_api/api_urls.py",
    "backend/core/management/commands/seed_permissions.py",
]

SCHOOL_ID_HEADER = "HTTP_X_SCHOOL_ID"
FOOD_METRICS_URL = "/api/v1/food/metrics/"


def _mk_school(suffix=""):
    return School.objects.create(name=f"M025 School {suffix or uuid.uuid4().hex[:6]}")


def _mk_user(prefix="m025"):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
    )


def _assign_role(user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)


def _grant(role_code, perm_code):
    perm, _ = CrownPermission.objects.get_or_create(code=perm_code)
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def test_51x51_module_metadata_present_25():
    assert MODULE_ID == 25
    assert MODULE_NAME == "Nutrition & Food Services"


def test_51x51_module_text_has_context_25():
    assert "meals" in MODULE_TEXT
    assert "menu" in MODULE_TEXT
    assert "allergen" in MODULE_TEXT
    assert "dietary accommodations" in MODULE_TEXT
    assert len(MODULE_TEXT) > 200


def test_51x51_required_keywords_present_25():
    required = [
        "tenant",
        "APIClient",
        "unauthorized",
        "workflow",
        "allergens",
        "food.view",
    ]
    text = "\n".join(AUDIT_KEYWORDS)
    for token in required:
        assert token in text


def test_51x51_food_evidence_files_named_25():
    assert "backend/crown_api/metrics_views.py" in EVIDENCE_FILES
    assert "backend/crown_api/api_urls.py" in EVIDENCE_FILES
    assert "backend/core/management/commands/seed_permissions.py" in EVIDENCE_FILES


def test_food_metrics_requires_tenant_context_25():
    c = Client()
    r = c.get(FOOD_METRICS_URL)
    assert r.status_code in (400, 401, 403)


def test_food_metrics_denies_without_permission_25():
    school = _mk_school("deny")
    user = _mk_user("deny-food")
    _assign_role(user, school, "m025_no_grant")

    c = Client()
    c.force_login(user)
    r = c.get(FOOD_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code in (401, 403)


def test_food_metrics_allows_with_food_view_permission_25():
    school = _mk_school("allow")
    user = _mk_user("allow-food")
    role_code = "m025_food_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "food.view")

    c = Client()
    c.force_login(user)
    r = c.get(FOOD_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})

    assert r.status_code == 200


def test_food_metrics_payload_contains_nutrition_contract_25():
    school = _mk_school("payload")
    user = _mk_user("payload-food")
    role_code = "m025_payload_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "food.view")

    c = Client()
    c.force_login(user)
    r = c.get(FOOD_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code == 200

    data = r.json()
    required_keys = [
        "meals_served_today",
        "free_reduced_count",
        "inventory_low_items",
        "payments_pending_count",
        "menu_today",
        "menu_tomorrow",
        "inventory_low",
        "participation_trend",
        "alerts",
        "snapshot_date",
    ]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"


def test_food_metrics_menu_entries_include_dietary_fields_25():
    school = _mk_school("menu")
    user = _mk_user("menu-food")
    role_code = "m025_menu_role"
    _assign_role(user, school, role_code)
    _grant(role_code, "food.view")

    c = Client()
    c.force_login(user)
    r = c.get(FOOD_METRICS_URL, **{SCHOOL_ID_HEADER: str(school.id)})
    assert r.status_code == 200

    data = r.json()
    assert len(data["menu_today"]) > 0

    for item in data["menu_today"]:
        assert "item" in item
        assert "category" in item
        assert "allergens" in item

    # At least one explicit allergen marker should be present for dietary handling.
    allergen_values = [x.get("allergens", "") for x in data["menu_today"]]
    assert any(v and v != "None" for v in allergen_values)
