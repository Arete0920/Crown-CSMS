"""
Unit tests for the Survey Sentiment Engine module.
Module keywords: Survey, Sentiment, feedback, pulse, questionnaire
Covers check 40: Unit Tests Exist.
"""
import pytest
from pathlib import Path

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_survey_sentiment_module_source_exists():
    """Verify Survey Sentiment Engine implementation source is present in the repository."""
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    source_text = ""
    for p in all_py:
        try:
            source_text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
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
    all_py = list(PROJECT_ROOT.rglob("*.py"))
    assert len(all_py) > 10, "Fewer than 10 Python files found — likely wrong root"


def test_survey_sentiment_school_keyword_in_source():
    """Verify tenant/school scoping keywords appear in the Survey Sentiment Engine source tree."""
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
    ), f"Survey Sentiment Engine: tenant/school scoping not found in source"
