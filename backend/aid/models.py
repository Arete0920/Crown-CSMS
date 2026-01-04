from django.db import models, transaction
from django.utils import timezone

from core.models import School, AcademicYear, Family, Student, UserAccount, LedgerEntry
from finance.models import ChartAccount, JournalBatch


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AidApplication(TimeStampedModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_NEEDS_INFO = "NEEDS_INFO"
    STATUS_APPROVED = "APPROVED"
    STATUS_DENIED = "DENIED"
    STATUS_WITHDRAWN = "WITHDRAWN"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_NEEDS_INFO, "Needs Info"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
        (STATUS_WITHDRAWN, "Withdrawn"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_applications")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="aid_applications")
    family = models.ForeignKey(Family, on_delete=models.PROTECT, related_name="aid_applications")

    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    household_size = models.PositiveSmallIntegerField(default=1)
    income_annual_cents = models.IntegerField(default=0)
    notes_internal = models.TextField(blank=True, default="")

    # Audit trail: when director last contacted family (e.g., needs-info email sent)
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    last_contacted_by = models.ForeignKey(
        UserAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="aid_contacts_initiated",
    )
    last_contacted_reason = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "academic_year", "status"]),
            models.Index(fields=["school", "family"]),
        ]

    def __str__(self) -> str:
        return f"{self.academic_year.name} — {self.family.family_name} — {self.status}"

    def set_status(self, new_status: str, actor_user: UserAccount | None = None, details: dict | None = None):
        self.status = new_status
        if new_status == self.STATUS_SUBMITTED and not self.submitted_at:
            self.submitted_at = timezone.now()
        self.save()

        AidAuditEvent.log(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_APPLICATION,
            entity_id=self.id,
            action=f"STATUS_{new_status}",
            actor_user=actor_user,
            details=details or {},
        )


class AidDocument(TimeStampedModel):
    DOC_W2 = "W2"
    DOC_TAX_RETURN = "TAX_RETURN"
    DOC_PAY_STUB = "PAY_STUB"
    DOC_OTHER = "OTHER"
    DOC_CHOICES = [
        (DOC_W2, "W-2"),
        (DOC_TAX_RETURN, "Tax Return"),
        (DOC_PAY_STUB, "Pay Stub"),
        (DOC_OTHER, "Other"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_documents")
    aid_application = models.ForeignKey(AidApplication, on_delete=models.PROTECT, related_name="documents")

    doc_type = models.CharField(max_length=24, choices=DOC_CHOICES)
    received = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.aid_application} — {self.doc_type}"


class AidReview(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_reviews")
    aid_application = models.ForeignKey(AidApplication, on_delete=models.PROTECT, related_name="reviews")

    reviewer_user = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="aid_reviews")
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    recommendation_cents = models.IntegerField(default=0)
    recommendation_notes = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Review — {self.aid_application.family.family_name} — ${self.recommendation_cents/100:.2f}"


class AidAward(TimeStampedModel):
    TYPE_NEED = "NEED"
    TYPE_MISSION = "MISSION"
    TYPE_MERIT = "MERIT"
    TYPE_HARDSHIP = "HARDSHIP"
    TYPE_CHOICES = [
        (TYPE_NEED, "Need"),
        (TYPE_MISSION, "Mission"),
        (TYPE_MERIT, "Merit"),
        (TYPE_HARDSHIP, "Hardship"),
    ]

    DECISION_OFFERED = "OFFERED"
    DECISION_ACCEPTED = "ACCEPTED"
    DECISION_DECLINED = "DECLINED"
    DECISION_CHOICES = [
        (DECISION_OFFERED, "Offered"),
        (DECISION_ACCEPTED, "Accepted"),
        (DECISION_DECLINED, "Declined"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_awards")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="aid_awards")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="aid_awards")

    award_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_NEED)
    awarded_cents = models.IntegerField(default=0)

    decision_status = models.CharField(max_length=16, choices=DECISION_CHOICES, default=DECISION_OFFERED)
    decided_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name="aid_awards_decided", null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    # Posting control (prevents double-posting to ledger)
    ledger_entry = models.OneToOneField(LedgerEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="aid_award")

    class Meta:
        indexes = [
            models.Index(fields=["school", "academic_year", "award_type"]),
            models.Index(fields=["school", "student"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.award_type} — ${self.awarded_cents/100:.2f} ({self.decision_status})"

    @transaction.atomic
    def mark_offered(self, actor_user: UserAccount | None = None):
        self.decision_status = self.DECISION_OFFERED
        self.decided_by = actor_user
        self.decided_at = timezone.now()
        self.save()

        AidAuditEvent.log(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=self.id,
            action="AWARD_OFFERED",
            actor_user=actor_user,
            details={"awarded_cents": self.awarded_cents, "award_type": self.award_type},
        )

    @transaction.atomic
    def mark_accepted_and_post(self, actor_user: UserAccount | None = None, batch: JournalBatch | None = None):
        """
        Accept the award and create a negative ledger entry (credit) under ChartAccount code 'AID'.
        Safe to call once; prevents duplicate ledger posting via self.ledger_entry.
        """
        self.decision_status = self.DECISION_ACCEPTED
        self.decided_by = actor_user
        self.decided_at = timezone.now()
        self.save()

        AidAuditEvent.log(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=self.id,
            action="AWARD_ACCEPTED",
            actor_user=actor_user,
            details={"awarded_cents": self.awarded_cents, "award_type": self.award_type},
        )

        if self.ledger_entry_id:
            # Already posted. Do not duplicate.
            return self.ledger_entry

        # Ensure ChartAccount exists
        aid_account = ChartAccount.objects.get(school=self.school, code="AID")

        # Ledger credit: negative amount
        entry = LedgerEntry.objects.create(
            school=self.school,
            academic_year=self.academic_year,
            family=self.student.family,
            student=self.student,
            entry_date=timezone.now().date(),
            account=aid_account,
            amount_cents=-abs(int(self.awarded_cents)),
            memo=f"Financial Aid Award ({self.award_type})",
            source=LedgerEntry.SOURCE_AID_AWARD,
            batch=batch,
            created_by_user=actor_user,
        )

        self.ledger_entry = entry
        self.save(update_fields=["ledger_entry"])

        AidAuditEvent.log(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=self.id,
            action="LEDGER_POSTED",
            actor_user=actor_user,
            details={"ledger_entry_id": str(entry.id), "amount_cents": entry.amount_cents, "account_code": "AID"},
        )

        return entry

    @transaction.atomic
    def mark_declined_and_reverse(self, actor_user: UserAccount | None = None):
        """
        If declined after posting, reverse the ledger entry by creating a reversal entry.
        """
        self.decision_status = self.DECISION_DECLINED
        self.decided_by = actor_user
        self.decided_at = timezone.now()
        self.save()

        AidAuditEvent.log(
            school=self.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=self.id,
            action="AWARD_DECLINED",
            actor_user=actor_user,
            details={"awarded_cents": self.awarded_cents, "award_type": self.award_type},
        )

        if self.ledger_entry_id:
            reversal = LedgerEntry.create_reversal(self.ledger_entry, created_by=actor_user)
            AidAuditEvent.log(
                school=self.school,
                entity_type=AidAuditEvent.ENTITY_AWARD,
                entity_id=self.id,
                action="LEDGER_REVERSED",
                actor_user=actor_user,
                details={"original_ledger_entry_id": str(self.ledger_entry_id), "reversal_ledger_entry_id": str(reversal.id)},
            )


class AidAuditEvent(TimeStampedModel):
    ENTITY_APPLICATION = "APPLICATION"
    ENTITY_REVIEW = "REVIEW"
    ENTITY_AWARD = "AWARD"

    ENTITY_CHOICES = [
        (ENTITY_APPLICATION, "Application"),
        (ENTITY_REVIEW, "Review"),
        (ENTITY_AWARD, "Award"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_audit_events")
    entity_type = models.CharField(max_length=24, choices=ENTITY_CHOICES)
    entity_id = models.UUIDField()

    action = models.CharField(max_length=64)
    actor_user = models.ForeignKey(UserAccount, on_delete=models.PROTECT, null=True, blank=True, related_name="aid_audit_events")

    timestamp = models.DateTimeField(default=timezone.now)
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "entity_type", "entity_id"]),
            models.Index(fields=["school", "timestamp"]),
            models.Index(fields=["school", "action"]),
        ]

    def __str__(self) -> str:
        return f"{self.timestamp} — {self.entity_type}:{self.entity_id} — {self.action}"

    @staticmethod
    def log(
        school: School,
        entity_type: str,
        entity_id,
        action: str,
        actor_user: UserAccount | None = None,
        details: dict | None = None,
    ):
        return AidAuditEvent.objects.create(
            school=school,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user=actor_user,
            timestamp=timezone.now(),
            details_json=details or {},
        )
