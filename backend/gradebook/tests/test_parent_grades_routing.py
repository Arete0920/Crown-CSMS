import pytest
from django.test import Client


@pytest.mark.django_db
def test_parent_grades_summary_route_is_registered():
    """
    Guardrail: /api/v1/gradebook/students/<uuid>/grades/ must be wired in URLconf.
    A 404 means the route was accidentally removed.
    Auth failures (401/403) and missing-student (404 from the view itself) are
    both handled inside the view — this test only prevents URLconf regressions.
    """
    c = Client()
    # Use a known-invalid UUID — the view will 401 (auth required) before hitting DB.
    resp = c.get("/api/v1/gradebook/students/00000000-0000-0000-0000-000000000000/grades/")
    assert resp.status_code != 404, (
        f"Expected a non-404 response (auth gate or view error), got 404. "
        f"Route may have been unregistered."
    )
