"""
Academic services: grade calculation, mastery tracking, transcript generation.
"""
from __future__ import annotations

from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .models import Grade, Submission, MasteryRecord, Assignment


# Standard 10-point grading scale
def percentage_to_letter(pct: Decimal) -> str:
    """Convert percentage to letter grade (10-point scale)."""
    if pct >= 90:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 70:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def compute_percentage(numeric_score: Decimal, points_possible: Decimal) -> Decimal:
    """Calculate percentage score."""
    if points_possible <= 0:
        return Decimal("0.00")
    return (numeric_score / points_possible) * Decimal("100.00")


@transaction.atomic
def upsert_grade_for_submission(
    *,
    submission: Submission,
    numeric_score: Decimal,
    graded_by,
    feedback: str = ""
) -> Grade:
    """
    Create or update grade for a submission.
    Triggers mastery update if assignment is linked to an objective.

    Args:
        submission: Submission instance
        numeric_score: Raw score (e.g., 85 out of 100)
        graded_by: User who graded
        feedback: Teacher feedback text

    Returns:
        Grade instance
    """
    from .models import Enrollment, SubmissionRevision
    import hashlib
    import uuid
    Enrollment.objects.select_for_update().get(id=submission.enrollment_id)
    submission = Submission.objects.select_for_update().get(id=submission.id)
    points_possible = submission.assignment.points_possible
    pct = compute_percentage(numeric_score, points_possible).quantize(Decimal("0.01"))
    letter = percentage_to_letter(pct)

    grade, _created = Grade.objects.update_or_create(
        submission=submission,
        defaults={
            "school_id": submission.school_id,
            "graded_by": graded_by,
            "numeric_score": numeric_score,
            "percentage": pct,
            "letter_grade": letter,
            "teacher_feedback": feedback,
        },
    )

    # Mark submission as graded
    submission.status = Submission.Status.GRADED
    submission.version += 1
    submission.save(update_fields=["status", "version", "updated_at"])
    SubmissionRevision.objects.create(submission=submission, actor=graded_by, sequence=submission.version,
        action="graded", content="", feedback=feedback, request_key=uuid.uuid4(),
        fingerprint=hashlib.sha256(str(numeric_score).encode()).hexdigest())

    # Update mastery if assignment has objective
    if submission.assignment.objective_id:
        update_mastery_from_grade(grade=grade)

    return grade


def mastery_from_percentage(pct: Decimal) -> int:
    """
    Map percentage to mastery level (1-4).

    Levels:
    - 4 (Advanced): 90-100%
    - 3 (Proficient): 80-89%
    - 2 (Developing): 70-79%
    - 1 (Beginning): <70%
    """
    if pct >= 90:
        return 4
    if pct >= 80:
        return 3
    if pct >= 70:
        return 2
    return 1


def update_mastery_from_grade(*, grade: Grade) -> None:
    """
    Update mastery record for objective based on grade.
    Latest evidence replaces previous mastery level.
    """
    assignment: Assignment = grade.submission.assignment
    objective = assignment.objective
    if not objective:
        return

    student = grade.submission.enrollment.student
    level = mastery_from_percentage(grade.percentage)

    MasteryRecord.objects.update_or_create(
        student=student,
        objective=objective,
        defaults={
            "school_id": grade.school_id,
            "mastery_level": level,
            "last_demonstrated_at": timezone.now(),
            "evidence_assignment": assignment,
        },
    )


def mark_submission_submitted(submission: Submission) -> None:
    """
    Mark submission as submitted with timestamp.
    Applies late/on-time status based on due date.
    """
    now = timezone.now()
    submission.submitted_at = now

    # Late rule: submitted after due date
    if submission.assignment.due_date and now.date() > submission.assignment.due_date:
        submission.status = Submission.Status.LATE
    else:
        submission.status = Submission.Status.SUBMITTED

    submission.save(update_fields=["status", "submitted_at", "updated_at"])


def mark_submissions_missing_if_past_due() -> int:
    """
    Batch job: mark all assigned submissions as MISSING if past due date.

    Returns:
        Count of submissions marked missing
    """
    from django.utils import timezone
    now = timezone.now().date()

    missing_submissions = Submission.objects.filter(
        status=Submission.Status.ASSIGNED,
        assignment__due_date__lt=now,
        submitted_at__isnull=True
    )

    count = missing_submissions.update(status=Submission.Status.MISSING)
    return count
