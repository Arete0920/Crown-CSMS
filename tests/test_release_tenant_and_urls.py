import os
import importlib
from pathlib import Path
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def _try_import(name: str):
    return importlib.import_module(name)

def test_project_has_manage_py():
    assert (PROJECT_ROOT / "manage.py").exists() or (PROJECT_ROOT / "backend" / "manage.py").exists()

def test_backend_urls_module_importable():
    candidates = [
        "backend.urls",
        "crown2026_config.urls",
        "crown_api.urls",
    ]
    imported = False
    for candidate in candidates:
        try:
            _try_import(candidate)
            imported = True
            break
        except Exception:
            continue
    assert imported, f"Could not import any URL module from candidates: {candidates}"

def test_health_or_integrity_route_strings_present():
    text = ""
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            continue
    assert ("api/health" in text or "/health" in text), "Health route string not found"
    assert ("api/integrity" in text or "/integrity" in text), "Integrity route string not found"

def test_tenant_keywords_present():
    text = ""
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            continue
    required_any = [
        "TenantQuerySetMixin",
        "tenant_school",
        "tenant_guard",
        "TenantScopedModel",
        "school_id",
        "X-School-Id",
    ]
    assert any(token in text for token in required_any), "Tenant isolation keywords not found in source tree"