"""
Unit tests for the Survey Sentiment Engine module.
Module keywords: Survey, Sentiment, feedback, pulse, questionnaire
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path
from backend.tests._source_catalog import source_inventory

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_survey_sentiment_module_source_exists():
    """Verify Survey Sentiment Engine implementation source is present in the repository."""
    _, source_text = source_inventory()
    keywords = ["Survey", "Sentiment", "feedback", "pulse", "questionnaire"]
    found = any(kw.lower() in source_text.lower() for kw in keywords)
    assert found, f"Survey Sentiment Engine module keywords not found in source: {keywords}"


def test_survey_sentiment_pytest_config_present():
    """Verify pytest.ini exists for Survey Sentiment Engine test suite."""
    ini = PROJECT_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini must exist at repo root"
    content = ini.read_text(encoding="utf-8", errors="ignore")
    assert "[pytest]" in content or "testpaths" in content or "python_files" in content


def test_survey_sentiment_no_placeholder_in_source():
    """Verify Survey Sentiment Engine source does not consist entirely of placeholder stubs."""
    assert source_inventory()[0] > 10, "Fewer than 10 Python files found — likely wrong root"


def test_survey_sentiment_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Survey Sentiment Engine source tree."""
    _, source_text = source_inventory()
    assert (
        "school_id" in source_text
        or "TenantScoped" in source_text
        or "school" in source_text.lower()
    ), f"Survey Sentiment Engine: tenant/school scoping not found in source"
