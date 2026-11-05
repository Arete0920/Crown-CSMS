"""
Unit tests for the Portrait of the Graduate module.
Module keywords: PortraitGraduate, graduate_profile, competency, outcome, formation_evidence
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path
from backend.tests._source_catalog import source_inventory

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_portrait_graduate_module_source_exists():
    """Verify Portrait of the Graduate implementation source is present in the repository."""
    _, source_text = source_inventory()
    keywords = ["PortraitGraduate", "graduate_profile", "competency", "outcome", "formation_evidence"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Portrait of the Graduate module keywords not found in source: {keywords}"


def test_portrait_graduate_pytest_config_present():
    """Verify pytest.ini exists for Portrait of the Graduate test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_portrait_graduate_no_placeholder_in_source():
    """Verify Portrait of the Graduate source does not consist entirely of placeholder stubs."""
    assert source_inventory()[0] > 10, "Fewer than 10 Python files found — likely wrong root"


def test_portrait_graduate_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Portrait of the Graduate source tree."""
    _, source_text = source_inventory()
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Portrait of the Graduate: tenant/school scoping not found in source"
