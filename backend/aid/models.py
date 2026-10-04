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
    assets_cents = models.IntegerField(default=0)
    liabilities_cents = models.IntegerField(default=0)
    notes_internal = models.TextField(blank=True, default="")

    # Canonical annual financial profile. Legacy aggregate fields above remain
    # migration-compatible snapshots until all readers move to the profile.
    financial_profile = models.ForeignKey(
        "AidFinancialProfile",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="applications",
    )

    # Mission Alignment Score (MAS) inputs — 0-100 each
    statement_of_faith_score = models.IntegerField(default=0)
    church_involvement_score = models.IntegerField(default=0)
    family_values_survey_score = models.IntegerField(default=0)
    pastoral_reference_score = models.IntegerField(default=0)
    pog_preassessment_score = models.IntegerField(default=0)

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
    TYPE_MARKETING = "MARKETING"
    TYPE_CHOICES = [
        (TYPE_NEED, "Need"),
        (TYPE_MISSION, "Mission"),
        (TYPE_MERIT, "Merit"),
        (TYPE_HARDSHIP, "Hardship"),
        (TYPE_MARKETING, "Marketing"),
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

    # Link back to the application this award was derived from (optional)
    aid_application = models.ForeignKey(
        "AidApplication", null=True, blank=True, on_delete=models.SET_NULL, related_name="awards"
    )

    award_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_NEED)
    awarded_cents = models.IntegerField(default=0)

    # Engine recommendation fields (populated by award_engine.recommend_award)
    recommended_award_cents = models.IntegerField(default=0)
    mas_score = models.IntegerField(default=0)
    mas_modifier_bps = models.IntegerField(default=0)
    explanation_json = models.JSONField(default=dict, blank=True)

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
    ENTITY_PROFILE = "PROFILE"

    ENTITY_CHOICES = [
        (ENTITY_APPLICATION, "Application"),
        (ENTITY_REVIEW, "Review"),
        (ENTITY_AWARD, "Award"),
        (ENTITY_PROFILE, "Financial profile"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_audit_events")
    entity_type = models.CharField(max_length=24, choices=ENTITY_CHOICES)
    # Aid entities currently use integer primary keys. Store identifiers as text
    # so the audit stream can safely cover current and future identifier types.
    entity_id = models.CharField(max_length=64)

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
            entity_id=str(entity_id),
            action=action,
            actor_user=actor_user,
            timestamp=timezone.now(),
            details_json=details or {},
        )


# ---------------------------------------------------------------------------
# Phase 7.5 additions: Policy + Budget governance
# ---------------------------------------------------------------------------

class AidPolicy(TimeStampedModel):
    """
    Per-school, per-year policy configuration.

    Controls need formula guardrails, bucket allocation (basis points, sum to 10,000),
    and MAS weighting (weights are relative; they are normalised at runtime).

    unique_together = (school, academic_year) enforces one active policy per year.
    """

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_policies")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="aid_policies")

    # Need formula guardrails
    need_income_floor_cents = models.BigIntegerField(
        default=0,
        help_text="Income below this floor is treated as $0 for need calculation.",
    )
    max_award_percent = models.IntegerField(
        default=60,
        help_text="Maximum award as % of gross tuition (0-100).",
    )
    min_award_percent = models.IntegerField(
        default=0,
        help_text="Minimum award as % of gross tuition (0-100).",
    )

    # Bucket allocations in basis points (design intent: sum to 10,000)
    bucket_need_bps = models.IntegerField(default=6000)
    bucket_mission_bps = models.IntegerField(default=1500)
    bucket_marketing_bps = models.IntegerField(default=800)
    bucket_merit_bps = models.IntegerField(default=800)
    bucket_hardship_bps = models.IntegerField(default=900)

    # MAS weighting (0-100 each; normalised at runtime)
    mas_weight_statement_of_faith = models.IntegerField(default=25)
    mas_weight_church_involvement = models.IntegerField(default=20)
    mas_weight_family_values = models.IntegerField(default=20)
    mas_weight_pastoral_reference = models.IntegerField(default=15)
    mas_weight_pog_preassessment = models.IntegerField(default=20)

    class Meta:
        unique_together = ("school", "academic_year")

    def __str__(self) -> str:
        return f"AidPolicy — {self.school} — {self.academic_year}"


class AidBudgetTracker(TimeStampedModel):
    """
    Per-school, per-year, per-bucket budget ledger.

    allocated_cents: total available in the bucket.
    awarded_cents: total approved awards against the bucket.
    remaining = allocated_cents - awarded_cents; must be >= award before approval.

    unique_together prevents duplicate rows.  select_for_update() is required before
    any mutation to prevent concurrent budget overruns.
    """

    BUCKET_NEED = AidAward.TYPE_NEED
    BUCKET_MISSION = AidAward.TYPE_MISSION
    BUCKET_MERIT = AidAward.TYPE_MERIT
    BUCKET_HARDSHIP = AidAward.TYPE_HARDSHIP
    BUCKET_MARKETING = AidAward.TYPE_MARKETING
    BUCKET_CHOICES = AidAward.TYPE_CHOICES

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_budget_trackers")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="aid_budget_trackers")
    bucket = models.CharField(max_length=16, choices=BUCKET_CHOICES)

    allocated_cents = models.BigIntegerField(default=0)
    awarded_cents = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ("school", "academic_year", "bucket")

    def __str__(self) -> str:
        return f"Budget — {self.school} — {self.academic_year} — {self.bucket}"

    @property
    def remaining_cents(self) -> int:
        return int(self.allocated_cents - self.awarded_cents)


# ---------------------------------------------------------------------------
# Jireh modernization: annual family profile, provenance, household graph,
# and configurable school questions.
# ---------------------------------------------------------------------------

class AidFinancialProfile(TimeStampedModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_SELF_ATTESTED = "SELF_ATTESTED"
    STATUS_DOCUMENT_REVIEWED = "DOCUMENT_REVIEWED"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SELF_ATTESTED, "Self-attested"),
        (STATUS_DOCUMENT_REVIEWED, "Document reviewed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_financial_profiles")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="aid_financial_profiles")
    family = models.ForeignKey(Family, on_delete=models.PROTECT, related_name="aid_financial_profiles")
    carried_forward_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="carried_forward_profiles",
    )
    verification_status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    consent_to_reuse = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        UserAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="aid_profiles_confirmed",
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "family"],
                name="aid_unique_family_financial_profile_year",
            )
        ]
        indexes = [
            models.Index(
                fields=["school", "academic_year", "verification_status"],
                name="aid_prof_year_status_idx",
            ),
            models.Index(
                fields=["school", "family"],
                name="aid_prof_school_family_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Financial profile — {self.family} — {self.academic_year}"

    def totals(self) -> dict[str, int]:
        totals = {
            "income_annual_cents": 0,
            "assets_cents": 0,
            "liabilities_cents": 0,
            "expenses_annual_cents": 0,
        }
        for item in self.line_items.all():
            amount = int(item.annual_amount_cents or 0)
            if item.category == AidFinancialLineItem.CATEGORY_INCOME:
                totals["income_annual_cents"] += amount
            elif item.category == AidFinancialLineItem.CATEGORY_ASSET:
                totals["assets_cents"] += amount
            elif item.category == AidFinancialLineItem.CATEGORY_LIABILITY:
                totals["liabilities_cents"] += amount
            elif item.category == AidFinancialLineItem.CATEGORY_EXPENSE:
                totals["expenses_annual_cents"] += amount
        return totals


class AidHouseholdMember(TimeStampedModel):
    ROLE_ADULT = "ADULT"
    ROLE_STUDENT = "STUDENT"
    ROLE_DEPENDENT = "DEPENDENT"
    ROLE_CONTRIBUTOR = "CONTRIBUTOR"
    ROLE_CHOICES = [
        (ROLE_ADULT, "Adult"),
        (ROLE_STUDENT, "Student"),
        (ROLE_DEPENDENT, "Dependent"),
        (ROLE_CONTRIBUTOR, "Financial contributor"),
    ]

    profile = models.ForeignKey(AidFinancialProfile, on_delete=models.CASCADE, related_name="household_members")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default="")
    relationship = models.CharField(max_length=64, blank=True, default="")
    student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="aid_household_memberships",
    )
    lives_in_household = models.BooleanField(default=True)
    financially_responsible = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["profile", "role"], name="aid_hh_profile_role_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class AidFinancialLineItem(TimeStampedModel):
    CATEGORY_INCOME = "INCOME"
    CATEGORY_ASSET = "ASSET"
    CATEGORY_LIABILITY = "LIABILITY"
    CATEGORY_EXPENSE = "EXPENSE"
    CATEGORY_CHOICES = [
        (CATEGORY_INCOME, "Income"),
        (CATEGORY_ASSET, "Asset"),
        (CATEGORY_LIABILITY, "Liability"),
        (CATEGORY_EXPENSE, "Expense"),
    ]

    SOURCE_APPLICANT = "APPLICANT"
    SOURCE_PRIOR_YEAR = "PRIOR_YEAR"
    SOURCE_DOCUMENT = "DOCUMENT"
    SOURCE_ADMIN = "ADMIN"
    SOURCE_CHOICES = [
        (SOURCE_APPLICANT, "Applicant entered"),
        (SOURCE_PRIOR_YEAR, "Prior-year verified profile"),
        (SOURCE_DOCUMENT, "Supporting document"),
        (SOURCE_ADMIN, "Administrator adjustment"),
    ]

    profile = models.ForeignKey(AidFinancialProfile, on_delete=models.CASCADE, related_name="line_items")
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=64)
    label = models.CharField(max_length=160, blank=True, default="")
    annual_amount_cents = models.BigIntegerField(default=0)
    source_type = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_APPLICANT)
    source_reference = models.CharField(max_length=255, blank=True, default="")
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        UserAccount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="aid_line_items_verified",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["profile", "category"],
                name="aid_line_prof_cat_idx",
            ),
            models.Index(
                fields=["profile", "verified"],
                name="aid_line_prof_verified_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.category}:{self.subcategory} — {self.annual_amount_cents}"


class AidQuestion(TimeStampedModel):
    TYPE_TEXT = "TEXT"
    TYPE_NUMBER = "NUMBER"
    TYPE_CURRENCY = "CURRENCY"
    TYPE_BOOLEAN = "BOOLEAN"
    TYPE_SELECT = "SELECT"
    TYPE_MULTISELECT = "MULTISELECT"
    TYPE_CHOICES = [
        (TYPE_TEXT, "Text"),
        (TYPE_NUMBER, "Number"),
        (TYPE_CURRENCY, "Currency"),
        (TYPE_BOOLEAN, "Yes/No"),
        (TYPE_SELECT, "Single select"),
        (TYPE_MULTISELECT, "Multi-select"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="aid_questions")
    academic_year = models.ForeignKey(
        AcademicYear,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="aid_questions",
    )
    key = models.SlugField(max_length=80)
    prompt = models.CharField(max_length=500)
    response_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_TEXT)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    options_json = models.JSONField(default=list, blank=True)
    conditions_json = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "key"],
                name="aid_unique_question_key_year",
            )
        ]
        ordering = ("display_order", "id")

    def __str__(self) -> str:
        return self.prompt


class AidResponse(TimeStampedModel):
    application = models.ForeignKey(AidApplication, on_delete=models.CASCADE, related_name="custom_responses")
    question = models.ForeignKey(AidQuestion, on_delete=models.PROTECT, related_name="responses")
    response_json = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "question"],
                name="aid_unique_application_question_response",
            )
        ]

    def __str__(self) -> str:
        return f"{self.application_id}:{self.question_id}"
