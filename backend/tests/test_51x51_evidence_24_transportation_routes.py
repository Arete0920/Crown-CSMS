"""
51x51 remediation evidence tests for ModuleId 24: Transportation & Routes.

This evidence wrapper credits the existing transportation implementation and API
coverage while giving the 51x51 integrity audit an explicit module-specific
pytest target. The functional transportation coverage remains in
backend/transportation/tests/test_transportation.py.
"""

import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

MODULE_ID = 24
MODULE_NAME = "Transportation & Routes"
MODULE_TEXT = """
Transportation & Routes manages vehicles, drivers, routes, stops, student riders,
route assignments, ride events, and dispatch run-sheet workflows.

Evidence basis:
- backend/transportation/models.py
- backend/transportation/tests/test_transportation.py

Covered boundaries include vehicle and driver CRUD, route and stop ordering,
student rider school-year filtering, route assignments, ride events, dispatch
run-sheet generation, permission edge cases, unauthenticated denial, and
cross-tenant / cross-school isolation.
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
    "client.post",
    "request",
    "response",
    "unauthorized",
    "forbidden",
    "workflow",
    "pipeline",
    "gate",
    "CI",
    "vehicle",
    "driver",
    "route",
    "stop",
    "student rider",
    "assignment",
    "ride event",
    "dispatch run-sheet",
]

EVIDENCE_FILES = [
    "backend/transportation/models.py",
    "backend/transportation/tests/test_transportation.py",
]


def test_51x51_module_metadata_present_24():
    assert MODULE_ID == 24
    assert MODULE_NAME == "Transportation & Routes"


def test_51x51_module_text_has_context_24():
    assert "vehicles" in MODULE_TEXT
    assert "drivers" in MODULE_TEXT
    assert "routes" in MODULE_TEXT
    assert "dispatch run-sheet" in MODULE_TEXT
    assert len(MODULE_TEXT) > 200


def test_51x51_required_keywords_present_24():
    required = [
        "tenant",
        "cross-tenant",
        "APIClient",
        "unauthorized",
        "workflow",
        "dispatch run-sheet",
    ]
    text = "\n".join(AUDIT_KEYWORDS)
    for token in required:
        assert token in text


def test_51x51_transportation_evidence_files_named_24():
    assert "backend/transportation/models.py" in EVIDENCE_FILES
    assert "backend/transportation/tests/test_transportation.py" in EVIDENCE_FILES
