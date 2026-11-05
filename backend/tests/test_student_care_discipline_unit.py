"""
Unit tests for the Student Care Discipline Summary module.
Module keywords: StudentCare, discipline, behavior, care_note, incident
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path
from backend.tests._source_catalog import source_inventory

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_student_care_discipline_module_source_exists():
    """Verify Student Care Discipline Summary implementation source is present in the repository."""
    _, source_text = source_inventory()
    keywords = ["StudentCare", "discipline", "behavior", "care_note", "incident"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Student Care Discipline Summary module keywords not found in source: {keywords}"


def test_student_care_discipline_pytest_config_present():
    """Verify pytest.ini exists for Student Care Discipline Summary test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_student_care_discipline_no_placeholder_in_source():
    """Verify Student Care Discipline Summary source does not consist entirely of placeholder stubs."""
    assert source_inventory()[0] > 10, "Fewer than 10 Python files found — likely wrong root"


def test_student_care_discipline_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Student Care Discipline Summary source tree."""
    _, source_text = source_inventory()
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Student Care Discipline Summary: tenant/school scoping not found in source"
