"""Module 021 - Competency Tracking evidence.

This proof covers the current Module 021 boundary:
1. Competency rubrics validate required mastery-rule fields.
2. Rubric violations are tenant-scoped and detect duplicate competencies.
3. Evidence collection is tenant-scoped and validates score/source contracts.
4. Mastery status requires sufficient evidence and threshold achievement.
5. Portfolio gaps return active non-mastered competencies only.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from academics.competency_tracking import (
    CompetencyEvidence,
    CompetencyRubric,
    competency_evidence_summary,
    competency_mastery_status,
    competency_portfolio_gaps,
    competency_rubric_violations,
    validate_competency_evidence,
    validate_competency_rubric,
)

MODULE_ID = 21
MODULE_NAME = "Competency Tracking"


def _rubric(school_id, competency_id="comp-1", code="C1", title="Core competency", domain="Academic", threshold="3.00", required=2, active=True):
    return CompetencyRubric(
        school_id=school_id,
        competency_id=competency_id,
        code=code,
        title=title,
        domain=domain,
        mastery_threshold=Decimal(threshold),
        required_evidence_count=required,
        active=active,
    )


def _evidence(school_id, evidence_id="ev-1", competency_id="comp-1", student_id="student-1", score="3.50", source_type="assessment", submitted=True):
    return CompetencyEvidence(
        school_id=school_id,
        evidence_id=evidence_id,
        competency_id=competency_id,
        student_id=student_id,
        score=Decimal(score),
        source_type=source_type,
        submitted=submitted,
    )


def test_module_metadata_is_present():
    assert MODULE_ID == 21
    assert MODULE_NAME == "Competency Tracking"


def test_validate_competency_rubric_rejects_invalid_mastery_contract():
    school_id = uuid4()
    with pytest.raises(ValueError, match="code is required"):
        validate_competency_rubric(_rubric(school_id, code=" "))
    with pytest.raises(ValueError, match="required_evidence_count must be greater than zero"):
        validate_competency_rubric(_rubric(school_id, required=0))
    with pytest.raises(ValueError, match="mastery_threshold must be between 0 and 4"):
        validate_competency_rubric(_rubric(school_id, threshold="4.50"))


def test_competency_rubric_violations_are_tenant_scoped_and_detect_duplicates():
    school_a = uuid4()
    school_b = uuid4()
    rubrics = [
        _rubric(school_a, competency_id="portrait-1", code="P1"),
        _rubric(school_a, competency_id="portrait-1", code="P1-DUP"),
        _rubric(school_a, competency_id="bad-threshold", threshold="5.00"),
        _rubric(school_b, competency_id="bad-other-tenant", threshold="5.00"),
    ]
    violations = competency_rubric_violations(school_a, rubrics)
    assert {row["violation_type"] for row in violations} == {"DUPLICATE_COMPETENCY_ID", "INVALID_RUBRIC"}
    assert {row["competency_id"] for row in violations} == {"portrait-1", "bad-threshold"}


def test_validate_competency_evidence_rejects_invalid_evidence_contract():
    school_id = uuid4()
    with pytest.raises(ValueError, match="score must be between 0 and 4"):
        validate_competency_evidence(_evidence(school_id, score="4.25"))
    with pytest.raises(ValueError, match="source_type is not recognized"):
        validate_competency_evidence(_evidence(school_id, source_type="unknown"))


def test_competency_evidence_summary_collects_only_valid_tenant_scoped_evidence():
    school_a = uuid4()
    school_b = uuid4()
    rubric = _rubric(school_a, required=2)
    evidence = [
        _evidence(school_a, evidence_id="valid-1", student_id="student-a", score="3.00"),
        _evidence(school_a, evidence_id="valid-2", student_id="student-a", score="4.00", source_type="project"),
        _evidence(school_a, evidence_id="draft", student_id="student-a", score="4.00", submitted=False),
        _evidence(school_a, evidence_id="other-student", student_id="student-b", score="4.00"),
        _evidence(school_b, evidence_id="other-tenant", student_id="student-a", score="4.00"),
    ]
    summary = competency_evidence_summary(school_a, rubric, evidence, student_id="student-a")
    assert summary["evidence_count"] == 2
    assert summary["required_evidence_count"] == 2
    assert summary["average_score"] == Decimal("3.50")
    assert summary["rejected_count"] == 1
    assert summary["rejected"] == [{"evidence_id": "draft", "reason": "NOT_SUBMITTED"}]


def test_competency_mastery_status_requires_sufficient_evidence_and_threshold():
    school_id = uuid4()
    rubric = _rubric(school_id, required=2, threshold="3.00")
    insufficient = competency_mastery_status(school_id, rubric, [_evidence(school_id, evidence_id="one", score="4.00")], student_id="student-1")
    developing = competency_mastery_status(
        school_id,
        rubric,
        [_evidence(school_id, evidence_id="low-1", score="2.00"), _evidence(school_id, evidence_id="low-2", score="3.00")],
        student_id="student-1",
    )
    mastered = competency_mastery_status(
        school_id,
        rubric,
        [_evidence(school_id, evidence_id="high-1", score="3.00"), _evidence(school_id, evidence_id="high-2", score="4.00")],
        student_id="student-1",
    )
    assert insufficient["status"] == "INSUFFICIENT_EVIDENCE"
    assert insufficient["mastered"] is False
    assert developing["status"] == "DEVELOPING"
    assert developing["average_score"] == Decimal("2.50")
    assert mastered["status"] == "MASTERED"
    assert mastered["average_score"] == Decimal("3.50")
    assert mastered["mastered"] is True


def test_competency_portfolio_gaps_returns_active_non_mastered_competencies_only():
    school_id = uuid4()
    mastered = _rubric(school_id, competency_id="mastered", code="A")
    developing = _rubric(school_id, competency_id="developing", code="B")
    inactive = _rubric(school_id, competency_id="inactive", code="C", active=False)
    rubrics = [developing, inactive, mastered]
    evidence = [
        _evidence(school_id, evidence_id="m1", competency_id="mastered", score="4.00"),
        _evidence(school_id, evidence_id="m2", competency_id="mastered", score="3.00"),
        _evidence(school_id, evidence_id="d1", competency_id="developing", score="2.00"),
        _evidence(school_id, evidence_id="d2", competency_id="developing", score="2.50"),
        _evidence(school_id, evidence_id="i1", competency_id="inactive", score="1.00"),
    ]
    gaps = competency_portfolio_gaps(school_id, rubrics, evidence, student_id="student-1")
    assert gaps == [
        {
            "competency_id": "developing",
            "code": "B",
            "title": "Core competency",
            "status": "DEVELOPING",
            "evidence_count": 2,
            "required_evidence_count": 2,
            "average_score": Decimal("2.25"),
        }
    ]
