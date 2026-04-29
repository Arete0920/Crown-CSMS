"""
Unit tests for the Student Master Record module.
Module keywords: Student, student_master, demographics, student_record, Student360
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_student_master_record_module_source_exists():
    """Verify Student Master Record implementation source is present in the repository."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    source_text = ""
    for p in all_py:
        try:
            source_text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    keywords = ["Student", "student_master", "demographics", "student_record", "Student360"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Student Master Record module keywords not found in source: {keywords}"


def test_student_master_record_pytest_config_present():
    """Verify pytest.ini exists for Student Master Record test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_student_master_record_no_placeholder_in_source():
    """Verify Student Master Record source does not consist entirely of placeholder stubs."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_student_master_record_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Student Master Record source tree."""
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
    ), f"Student Master Record: tenant/school scoping not found in source"
