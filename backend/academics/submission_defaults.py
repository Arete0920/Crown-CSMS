from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Assignment, Enrollment, Submission


@receiver(
    pre_save,
    sender=Submission,
    dispatch_uid="academics.submission.infer_school_before_validation",
)
def infer_submission_school_from_parents(
    sender, instance, raw=False, using=None, **kwargs
):
    """Preserve API creates that stamp school from the assignment after serializer input."""
    if raw or instance.school_id:
        return
    if not instance.assignment_id or not instance.enrollment_id:
        return

    assignments = Assignment._base_manager.using(using) if using else Assignment._base_manager
    enrollments = Enrollment._base_manager.using(using) if using else Enrollment._base_manager

    try:
        assignment = assignments.only("school_id", "section_id").get(
            pk=instance.assignment_id
        )
    except Assignment.DoesNotExist as exc:
        raise ValidationError({"assignment": "Assignment does not exist."}) from exc

    try:
        enrollment = enrollments.only("school_id", "section_id").get(
            pk=instance.enrollment_id
        )
    except Enrollment.DoesNotExist as exc:
        raise ValidationError({"enrollment": "Enrollment does not exist."}) from exc

    if assignment.school_id != enrollment.school_id:
        raise ValidationError(
            {"enrollment": "Submission parents must belong to the same school."}
        )
    if assignment.section_id != enrollment.section_id:
        raise ValidationError(
            {"enrollment": "Submission enrollment must belong to the assignment section."}
        )

    instance.school_id = assignment.school_id
