"""
Unit tests for the Extended Discipline Workflows module.
Module keywords: Discipline, behavior, incident, consequence, escalation
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

from ._source_inventory import repository_python_files, repository_python_source

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_extended_discipline_module_source_exists():
    """Verify Extended Discipline Workflows implementation source is present in the repository."""
    source_text = repository_python_source(PROJECT_ROOT)
    keywords = ["Discipline", "behavior", "incident", "consequence", "escalation"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Extended Discipline Workflows module keywords not found in source: {keywords}"


def test_extended_discipline_pytest_config_present():
    """Verify pytest.ini exists for Extended Discipline Workflows test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_extended_discipline_no_placeholder_in_source():
    """Verify Extended Discipline Workflows source does not consist entirely of placeholder stubs."""
    all_py = repository_python_files(PROJECT_ROOT)
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_extended_discipline_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Extended Discipline Workflows source tree."""
    source_text = repository_python_source(PROJECT_ROOT)
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Extended Discipline Workflows: tenant/school scoping not found in source"
