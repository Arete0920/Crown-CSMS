from django.db import models, transaction
from django.utils import timezone
from core.models import School, AcademicYear, Family, Student, UserAccount, LedgerEntry

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AdmissionsApplication(TimeStampedModel):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_NEEDS_INFO = 'NEEDS_INFO'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_WAITLISTED = 'WAITLISTED'
    STATUS_DENIED = 'DENIED'
    STATUS_WITHDRAWN = 'WITHDRAWN'
    STATUS_ENROLLED = 'ENROLLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_NEEDS_INFO, 'Needs Info'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_WAITLISTED, 'Waitlisted'),
        (STATUS_DENIED, 'Denied'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_ENROLLED, 'Enrolled'),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='admissions_applications')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='admissions_applications')
    family = models.ForeignKey(Family, on_delete=models.PROTECT, related_name='admissions_applications')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, null=True, blank=True, related_name='admissions_applications')

    # Linkage to the read-only spine models (Households/Students modules)
    household = models.ForeignKey(
        'crown_api.Household',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='applications',
    )
    sis_student = models.ForeignKey(
        'crown_api.Student',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='applications',
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # Application data
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    test_score = models.PositiveSmallIntegerField(null=True, blank=True)
    essay_received = models.BooleanField(default=False)
    recommendations_received = models.PositiveSmallIntegerField(default=0)
    transcript_received = models.BooleanField(default=False)

    notes_internal = models.TextField(blank=True, default='')

    # Audit trail
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    last_contacted_by = models.ForeignKey(
        UserAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='admissions_contacts_initiated',
    )
    last_contacted_reason = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['school', 'academic_year', 'status']),
            models.Index(fields=['school', 'family']),
        ]

    def __str__(self) -> str:
        return f'{self.academic_year.name}  {self.family.family_name}  {self.status}'

    def set_status(self, new_status: str, actor_user: UserAccount | None = None, details: dict | None = None):
        self.status = new_status
        if new_status == self.STATUS_SUBMITTED and not self.submitted_at:
            self.submitted_at = timezone.now()
        self.save()

        AdmissionsAuditEvent.log(
            school=self.school,
            entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
            entity_id=self.id,
            action=f'STATUS_{new_status}',
            actor_user=actor_user,
            details=details or {},
        )


class AdmissionsReview(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='admissions_reviews')
    application = models.ForeignKey(AdmissionsApplication, on_delete=models.PROTECT, related_name='reviews')
    reviewer_user = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name='admissions_reviews')

    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    academic_score = models.PositiveSmallIntegerField(default=0)  # 0-100
    character_score = models.PositiveSmallIntegerField(default=0)  # 0-100
    mission_fit_score = models.PositiveSmallIntegerField(default=0)  # 0-100

    recommendation = models.CharField(
        max_length=24,
        choices=[
            ('ACCEPT', 'Accept'),
            ('WAITLIST', 'Waitlist'),
            ('DENY', 'Deny'),
        ],
        blank=True,
        default='',
    )
    recommendation_notes = models.TextField(blank=True, default='')

    def __str__(self) -> str:
        return f'Review  {self.application.family.family_name}  {self.recommendation}'


class AdmissionsDecision(TimeStampedModel):
    DECISION_ACCEPTED = 'ACCEPTED'
    DECISION_WAITLISTED = 'WAITLISTED'
    DECISION_DENIED = 'DENIED'

    DECISION_CHOICES = [
        (DECISION_ACCEPTED, 'Accepted'),
        (DECISION_WAITLISTED, 'Waitlisted'),
        (DECISION_DENIED, 'Denied'),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='admissions_decisions')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='admissions_decisions')
    application = models.OneToOneField(AdmissionsApplication, on_delete=models.PROTECT, related_name='decision')

    decision_status = models.CharField(max_length=16, choices=DECISION_CHOICES)
    decided_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name='admissions_decisions_made')
    decided_at = models.DateTimeField(default=timezone.now)

    decision_letter_sent = models.BooleanField(default=False)
    decision_letter_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['school', 'academic_year', 'decision_status']),
        ]

    def __str__(self) -> str:
        return f'{self.application.family.family_name}  {self.decision_status}'

    @transaction.atomic
    def mark_decision_made(self, actor_user: UserAccount | None = None):
        self.decided_by = actor_user
        self.decided_at = timezone.now()
        self.save()

        # Update application status
        if self.decision_status == self.DECISION_ACCEPTED:
            self.application.set_status(AdmissionsApplication.STATUS_ACCEPTED, actor_user)
        elif self.decision_status == self.DECISION_WAITLISTED:
            self.application.set_status(AdmissionsApplication.STATUS_WAITLISTED, actor_user)
        elif self.decision_status == self.DECISION_DENIED:
            self.application.set_status(AdmissionsApplication.STATUS_DENIED, actor_user)

        AdmissionsAuditEvent.log(
            school=self.school,
            entity_type=AdmissionsAuditEvent.ENTITY_DECISION,
            entity_id=self.id,
            action='DECISION_MADE',
            actor_user=actor_user,
            details={'decision_status': self.decision_status},
        )


class AdmissionsAuditEvent(TimeStampedModel):
    ENTITY_APPLICATION = 'APPLICATION'
    ENTITY_REVIEW = 'REVIEW'
    ENTITY_DECISION = 'DECISION'

    ENTITY_CHOICES = [
        (ENTITY_APPLICATION, 'Application'),
        (ENTITY_REVIEW, 'Review'),
        (ENTITY_DECISION, 'Decision'),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='admissions_audit_events')
    entity_type = models.CharField(max_length=24, choices=ENTITY_CHOICES)
    entity_id = models.UUIDField()

    action = models.CharField(max_length=64)
    actor_user = models.ForeignKey(UserAccount, on_delete=models.PROTECT, null=True, blank=True, related_name='admissions_audit_events')

    timestamp = models.DateTimeField(default=timezone.now)
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['school', 'entity_type', 'entity_id']),
            models.Index(fields=['school', 'timestamp']),
            models.Index(fields=['school', 'action']),
        ]

    def __str__(self) -> str:
        return f'{self.timestamp}  {self.entity_type}:{self.entity_id}  {self.action}'

    @staticmethod
    def log(
        school: School,
        entity_type: str,
        entity_id,
        action: str,
        actor_user: UserAccount | None = None,
        details: dict | None = None,
    ):
        return AdmissionsAuditEvent.objects.create(
            school=school,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user=actor_user,
            timestamp=timezone.now(),
            details_json=details or {},
        )
