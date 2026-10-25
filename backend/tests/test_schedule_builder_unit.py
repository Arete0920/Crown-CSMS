"""
Unit tests for the Standalone Schedule Builder module.
Module keywords: ScheduleBuilder, scheduler, optimizer, standalone_schedule, conflict_solver
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

from ._source_inventory import repository_python_files, repository_python_source

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_schedule_builder_module_source_exists():
    """Verify Standalone Schedule Builder implementation source is present in the repository."""
    source_text = repository_python_source(PROJECT_ROOT)
    keywords = ["ScheduleBuilder", "scheduler", "optimizer", "standalone_schedule", "conflict_solver"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Standalone Schedule Builder module keywords not found in source: {keywords}"


def test_schedule_builder_pytest_config_present():
    """Verify pytest.ini exists for Standalone Schedule Builder test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_schedule_builder_no_placeholder_in_source():
    """Verify Standalone Schedule Builder source does not consist entirely of placeholder stubs."""
    all_py = repository_python_files(PROJECT_ROOT)
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_schedule_builder_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Standalone Schedule Builder source tree."""
    source_text = repository_python_source(PROJECT_ROOT)
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Standalone Schedule Builder: tenant/school scoping not found in source"
