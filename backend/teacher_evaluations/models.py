"""Confidential, unscored staff observation evidence; never a grade or faith score."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class GuardedEvidenceQuerySet(models.QuerySet):
    """Keep model validation and official event history out of bulk-write bypasses."""

    def update(self, **kwargs):
        raise ValidationError("Use the versioned teacher-evaluation workflow.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Bulk changes to teacher-evaluation records are blocked.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Use the audited teacher-evaluation workflow.")

    def delete(self):
        raise ValidationError("Teacher-evaluation evidence cannot be hard-deleted.")


class AppendOnlyEvidence(models.Model):
    """Base for records whose creation is final and attributable."""

    objects = GuardedEvidenceQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Teacher-evaluation history is append-only.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Teacher-evaluation history cannot be deleted.")


class TeacherEvaluationCycle(AppendOnlyEvidence):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    staff = models.ForeignKey("core.Staff", on_delete=models.PROTECT, related_name="evaluation_cycles")
    academic_year = models.ForeignKey("core.AcademicYear", on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=160)
    state = models.CharField(max_length=16, choices=[("active", "Active")], default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [models.Index(fields=["school", "staff", "academic_year"], name="te_cycle_scope_idx")]
        constraints = [
            models.UniqueConstraint(fields=["school", "staff", "academic_year"], name="te_cycle_staff_year_once"),
        ]

    def clean(self):
        if self.school_id and self.staff_id and self.staff.school_id != self.school_id:
            raise ValidationError("Evaluated staff must belong to the cycle school.")
        if self.school_id and self.academic_year_id and self.academic_year.school_id != self.school_id:
            raise ValidationError("Academic year must belong to the cycle school.")
        if self.school_id and self.created_by_id and self.created_by.school_id != self.school_id:
            raise ValidationError("The cycle creator must belong to the school.")
        if self.staff_id and (self.staff.status != "ACTIVE" or self.staff.role_type != "TEACHER"):
            raise ValidationError("New cycles require an active canonical teacher.")
        if self.created_by_id and self.created_by.staff_id == self.staff_id:
            raise ValidationError("Teachers cannot assign their own evaluation.")


class TeacherEvaluationAssignment(AppendOnlyEvidence):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    cycle = models.OneToOneField(TeacherEvaluationCycle, on_delete=models.PROTECT, related_name="assignment")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_teacher_evaluations")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="teacher_evaluation_assignments_made")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.cycle_id and self.school_id and self.cycle.school_id != self.school_id:
            raise ValidationError("Assignment and evaluation cycle must belong to one school.")
        if self.school_id and self.evaluator_id and (
            self.evaluator.school_id != self.school_id or not self.evaluator.is_active
        ):
            raise ValidationError("Evaluator must be an active account in this school.")
        if self.school_id and self.assigned_by_id and self.assigned_by.school_id != self.school_id:
            raise ValidationError("Assignment author must belong to this school.")
        if self.cycle_id and self.evaluator_id and self.evaluator.staff_id == self.cycle.staff_id:
            raise ValidationError("Teachers cannot evaluate themselves.")
        if self.cycle_id and self.assigned_by_id and self.assigned_by.staff_id == self.cycle.staff_id:
            raise ValidationError("Teachers cannot assign their own evaluation.")


class TeacherObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    cycle = models.ForeignKey(TeacherEvaluationCycle, on_delete=models.PROTECT, related_name="observations")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    observed_at = models.DateTimeField()
    narrative = models.TextField(max_length=8000)
    status = models.CharField(
        max_length=16,
        choices=[("draft", "Draft"), ("submitted", "Submitted")],
        default="draft",
    )
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = GuardedEvidenceQuerySet.as_manager()

    class Meta:
        ordering = ["-observed_at", "id"]
        indexes = [models.Index(fields=["school", "cycle", "status"], name="te_observation_scope_idx")]

    def clean(self):
        if self.cycle_id and self.school_id and self.cycle.school_id != self.school_id:
            raise ValidationError("Observation and cycle must belong to one school.")
        if self.cycle_id and self.evaluator_id and (
            not TeacherEvaluationAssignment.objects.filter(
                cycle_id=self.cycle_id, school_id=self.school_id, evaluator_id=self.evaluator_id
            ).exists()
        ):
            raise ValidationError("The observation author is not the assigned evaluator.")
        if not isinstance(self.narrative, str) or not self.narrative.strip():
            raise ValidationError("Observed evidence must be recorded.")
        if self.status == "submitted" and self.submitted_at is None:
            raise ValidationError("Submitted observations require an attributed submission time.")
        if self.status == "draft" and self.submitted_at is not None:
            raise ValidationError("Drafts cannot carry a submission time.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status == "submitted":
                raise ValidationError("Submitted observations are immutable.")
            if (previous.school_id, previous.cycle_id, previous.evaluator_id) != (
                self.school_id, self.cycle_id, self.evaluator_id
            ):
                raise ValidationError("Observation ownership cannot change.")
            if not (
                previous.status == "draft"
                and self.status == "submitted"
                and self.version == previous.version + 1
                and self.submitted_at is not None
                and self.narrative == previous.narrative
                and self.observed_at == previous.observed_at
            ):
                raise ValidationError("Only an audited draft-to-submitted transition is allowed.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Observation evidence cannot be deleted.")


class TeacherObservationResponse(AppendOnlyEvidence):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    observation = models.OneToOneField(TeacherObservation, on_delete=models.PROTECT, related_name="teacher_response")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    choice = models.CharField(
        max_length=24, choices=[("acknowledged_receipt", "Acknowledged receipt"), ("disputed", "Disputed")]
    )
    comment = models.TextField(blank=True, default="", max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.observation_id and self.school_id and self.observation.school_id != self.school_id:
            raise ValidationError("Response and observation must belong to one school.")
        if self.teacher_id and self.school_id and self.teacher.school_id != self.school_id:
            raise ValidationError("Teacher response must originate from the school.")
        if self.observation_id and self.teacher_id and self.teacher.staff_id != self.observation.cycle.staff_id:
            raise ValidationError("Only the evaluated teacher may respond.")
        if self.observation_id and self.observation.status != "submitted":
            raise ValidationError("A draft cannot be acknowledged.")
        if self.choice == "disputed" and not self.comment.strip():
            raise ValidationError("A written statement is required when disputing an observation.")


class TeacherEvaluationEvent(AppendOnlyEvidence):
    """Attributable metadata, deliberately excluding private observation narratives."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    cycle = models.ForeignKey(TeacherEvaluationCycle, on_delete=models.PROTECT, related_name="events")
    observation = models.ForeignKey(
        TeacherObservation, on_delete=models.PROTECT, null=True, blank=True, related_name="events"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=32)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["school", "cycle", "created_at"], name="te_event_scope_idx")]
        constraints = [
            models.UniqueConstraint(fields=["school", "actor", "request_key"], name="te_event_actor_retry"),
        ]

    def clean(self):
        if self.cycle_id and self.school_id and self.cycle.school_id != self.school_id:
            raise ValidationError("Event and cycle must belong to one school.")
        if self.actor_id and self.school_id and self.actor.school_id != self.school_id:
            raise ValidationError("Event actor must belong to this school.")
        if self.observation_id and self.cycle_id and self.observation.cycle_id != self.cycle_id:
            raise ValidationError("Event observation must belong to its cycle.")
