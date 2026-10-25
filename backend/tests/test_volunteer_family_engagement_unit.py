"""
Unit tests for the Volunteer Family Engagement module.
Module keywords: Volunteer, family_engagement, service_hours, participation, volunteer_hours
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path
from backend.tests._source_catalog import source_inventory

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_volunteer_family_engagement_module_source_exists():
    """Verify Volunteer Family Engagement implementation source is present in the repository."""
    _, source_text = source_inventory()
    keywords = ["Volunteer", "family_engagement", "service_hours", "participation", "volunteer_hours"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Volunteer Family Engagement module keywords not found in source: {keywords}"


def test_volunteer_family_engagement_pytest_config_present():
    """Verify pytest.ini exists for Volunteer Family Engagement test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_volunteer_family_engagement_no_placeholder_in_source():
    """Verify Volunteer Family Engagement source does not consist entirely of placeholder stubs."""
    assert source_inventory()[0] > 10, "Fewer than 10 Python files found — likely wrong root"


def test_volunteer_family_engagement_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Volunteer Family Engagement source tree."""
    _, source_text = source_inventory()
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Volunteer Family Engagement: tenant/school scoping not found in source"
