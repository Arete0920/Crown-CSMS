"""Module 019 - Assessment & Testing Framework evidence.

This proof covers the current Module 019 production boundary:

1. Assessment blueprints validate required design fields and scoring ranges.
2. Assessment design violations are tenant-scoped.
3. Scoring produces deterministic mastery, passing, below-standard, missing, and excused states.
4. Cross-school scoring is rejected.
5. Aggregate score summaries ignore cross-tenant submissions and unrelated assessments.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from academics.assessment_framework import (
    AssessmentBlueprint,
    AssessmentSubmission,
    assessment_design_violations,
    assessment_score_summary,
    score_submission,
    validate_assessment_blueprint,
)


MODULE_ID = 19
MODULE_NAME = "Assessment & Testing Framework"


def _blueprint(
    school_id,
    assessment_id="quiz-1",
    title="Unit 1 Quiz",
    term="2026-FALL",
    max_points="20.00",
    weight="10.00",
    mastery="80.00",
    active=True,
):
    return AssessmentBlueprint(
        school_id=school_id,
        assessment_id=assessment_id,
        title=title,
        term=term,
        max_points=Decimal(max_points),
        weight_percent=Decimal(weight),
        mastery_cutoff_percent=Decimal(mastery),
        active=active,
    )


def _submission(
    school_id,
    assessment_id="quiz-1",
    student_id="student-1",
    points="18.00",
    submitted=True,
    excused=False,
):
    return AssessmentSubmission(
        school_id=school_id,
        assessment_id=assessment_id,
        student_id=student_id,
        points_earned=None if points is None else Decimal(points),
        submitted=submitted,
        excused=excused,
    )


def test_module_metadata_is_present():
    assert MODULE_ID == 19
    assert MODULE_NAME == "Assessment & Testing Framework"


def test_validate_assessment_blueprint_rejects_invalid_design_fields():
    school_id = uuid4()

    with pytest.raises(ValueError, match="title is required"):
        validate_assessment_blueprint(_blueprint(school_id, title=" "))

    with pytest.raises(ValueError, match="max_points must be greater than zero"):
        validate_assessment_blueprint(_blueprint(school_id, max_points="0.00"))

    with pytest.raises(ValueError, match="weight_percent must be between 0 and 100"):
        validate_assessment_blueprint(_blueprint(school_id, weight="-0.01"))

    with pytest.raises(ValueError, match="weight_percent must be between 0 and 100"):
        validate_assessment_blueprint(_blueprint(school_id, weight="100.01"))

    with pytest.raises(ValueError, match="mastery_cutoff_percent must be between 0 and 100"):
        validate_assessment_blueprint(_blueprint(school_id, mastery="101.00"))


def test_assessment_design_violations_are_tenant_scoped_and_detect_duplicates():
    school_a = uuid4()
    school_b = uuid4()
    blueprints = [
        _blueprint(school_a, assessment_id="midterm", title="Midterm A"),
        _blueprint(school_a, assessment_id="midterm", title="Midterm Duplicate"),
        _blueprint(school_a, assessment_id="bad-max", max_points="0.00"),
        _blueprint(school_b, assessment_id="bad-other-tenant", max_points="0.00"),
    ]

    violations = assessment_design_violations(school_a, blueprints, term="2026-FALL")
    by_type = {row["violation_type"] for row in violations}

    assert by_type == {"DUPLICATE_ASSESSMENT_ID", "INVALID_ASSESSMENT_DESIGN"}
    assert {row["assessment_id"] for row in violations} == {"midterm", "bad-max"}


def test_score_submission_produces_mastery_passing_below_missing_and_excused_states():
    school_id = uuid4()
    blueprint = _blueprint(school_id, max_points="20.00", mastery="85.00")

    mastered = score_submission(blueprint, _submission(school_id, student_id="mastered", points="18.00"))
    passing = score_submission(blueprint, _submission(school_id, student_id="passing", points="14.00"))
    below = score_submission(blueprint, _submission(school_id, student_id="below", points="9.00"))
    missing = score_submission(blueprint, _submission(school_id, student_id="missing", points=None, submitted=False))
    excused = score_submission(blueprint, _submission(school_id, student_id="excused", points=None, excused=True))

    assert mastered["status"] == "MASTERED"
    assert mastered["percent"] == Decimal("90.00")
    assert mastered["mastery_met"] is True

    assert passing["status"] == "PASSING"
    assert passing["percent"] == Decimal("70.00")

    assert below["status"] == "BELOW_STANDARD"
    assert below["percent"] == Decimal("45.00")

    assert missing["status"] == "MISSING"
    assert missing["percent"] is None

    assert excused["status"] == "EXCUSED"
    assert excused["percent"] is None


def test_score_submission_rejects_cross_school_and_over_max_scores():
    school_a = uuid4()
    school_b = uuid4()
    blueprint = _blueprint(school_a, max_points="20.00")

    with pytest.raises(ValueError, match="cross-school assessment scoring is not permitted"):
        score_submission(blueprint, _submission(school_b, points="10.00"))

    with pytest.raises(ValueError, match="points_earned cannot exceed max_points"):
        score_submission(blueprint, _submission(school_a, points="21.00"))


def test_assessment_score_summary_is_tenant_scoped_and_ignores_unrelated_assessments():
    school_a = uuid4()
    school_b = uuid4()
    blueprints = [
        _blueprint(school_a, assessment_id="quiz-1", max_points="20.00"),
        _blueprint(school_a, assessment_id="quiz-2", max_points="10.00"),
        _blueprint(school_b, assessment_id="quiz-1", max_points="100.00"),
    ]
    submissions = [
        _submission(school_a, assessment_id="quiz-1", student_id="a", points="18.00"),
        _submission(school_a, assessment_id="quiz-1", student_id="b", points="12.00"),
        _submission(school_a, assessment_id="quiz-2", student_id="c", points=None, submitted=False),
        _submission(school_a, assessment_id="unknown", student_id="ignored", points="10.00"),
        _submission(school_b, assessment_id="quiz-1", student_id="other-tenant", points="100.00"),
    ]

    summary = assessment_score_summary(school_a, blueprints, submissions, term="2026-FALL")

    assert summary["assessment_count"] == 2
    assert summary["submission_count"] == 3
    assert summary["scored_count"] == 2
    assert summary["missing_count"] == 1
    assert summary["excused_count"] == 0
    assert summary["mastery_count"] == 1
    assert summary["average_percent"] == Decimal("75.00")
