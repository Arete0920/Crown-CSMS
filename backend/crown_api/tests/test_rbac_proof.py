import os
import pytest
from django.test import Client


@pytest.mark.django_db
def test_rbac_finance_proof_forbidden_without_role():
    c = Client()
    resp = c.get("/api/system/rbac/finance-proof/")
    assert resp.status_code == 403
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == "Forbidden"
    assert "required_roles" in data


@pytest.mark.django_db
def test_rbac_finance_proof_allows_admin_via_demo_header(monkeypatch):
    """Demo header works when ALLOW_DEMO_ROLE_HEADER=1"""
    monkeypatch.setenv("ALLOW_DEMO_ROLE_HEADER", "1")
    c = Client(HTTP_X_DEMO_ROLE="admin")
    resp = c.get("/api/system/rbac/finance-proof/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "RBAC OK" in data["message"]


@pytest.mark.django_db
def test_rbac_finance_proof_ignores_demo_header_when_flag_disabled(monkeypatch):
    """SECURITY: Demo header is ignored when env flag is not set"""
    monkeypatch.delenv("ALLOW_DEMO_ROLE_HEADER", raising=False)
    c = Client(HTTP_X_DEMO_ROLE="admin")
    resp = c.get("/api/system/rbac/finance-proof/")
    assert resp.status_code == 403
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == "Forbidden"
    assert data["actual_role"] is None  # Header was ignored

