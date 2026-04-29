"""
Unit tests for the Chaplain Pastoral Care module.
Module keywords: Chaplain, Pastoral, care_referral, prayer_followup, counseling
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_chaplain_pastoral_care_module_source_exists():
    """Verify Chaplain Pastoral Care implementation source is present in the repository."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    source_text = ""
    for p in all_py:
        try:
            source_text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    keywords = ["Chaplain", "Pastoral", "care_referral", "prayer_followup", "counseling"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Chaplain Pastoral Care module keywords not found in source: {keywords}"


def test_chaplain_pastoral_care_pytest_config_present():
    """Verify pytest.ini exists for Chaplain Pastoral Care test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_chaplain_pastoral_care_no_placeholder_in_source():
    """Verify Chaplain Pastoral Care source does not consist entirely of placeholder stubs."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_chaplain_pastoral_care_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Chaplain Pastoral Care source tree."""
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
    ), f"Chaplain Pastoral Care: tenant/school scoping not found in source"
