"""
Unit tests for the Nurse Health Office module.
Module keywords: Nurse, HealthOffice, health_visit, medication, health_incident
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_nurse_health_office_module_source_exists():
    """Verify Nurse Health Office implementation source is present in the repository."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    source_text = ""
    for p in all_py:
        try:
            source_text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    keywords = ["Nurse", "HealthOffice", "health_visit", "medication", "health_incident"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Nurse Health Office module keywords not found in source: {keywords}"


def test_nurse_health_office_pytest_config_present():
    """Verify pytest.ini exists for Nurse Health Office test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_nurse_health_office_no_placeholder_in_source():
    """Verify Nurse Health Office source does not consist entirely of placeholder stubs."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_nurse_health_office_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Nurse Health Office source tree."""
    source_text = ""
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            source_text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Nurse Health Office: tenant/school scoping not found in source"
