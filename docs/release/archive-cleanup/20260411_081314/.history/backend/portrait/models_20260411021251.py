from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import School
from core.tenant_models import TenantScopedModel, tenant_context


SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]

RECOMMENDATION_CHOICES = [
    ("strong_accept", "Strong Accept — Exemplary Mission Alignment"),
    ("accept", "Accept — Good Mission Alignment"),
    ("accept_review", "Accept with Review — Partial Alignment"),
    ("hold", "Hold — Needs Admissions Committee Review"),
    ("decline", "Decline — Mission Misalignment Concern"),
]

FAITH_DOMAIN_CHOICES = [
    ("faith_formation", "Faith Formation / Discipleship"),
    ("biblical_worldview", "Biblical Worldview"),
    ("academic_excellence", "Academic Excellence & Vocation"),
    ("character_leadership", "Character & Servant Leadership"),
    ("community_mission", "Community & Great Commission"),
    ("custom", "Custom Domain"),
]

CONTEXT_CHOICES = [
    ("inquiry", "Inquiry"),
    ("application", "Application Review"),
    ("interview", "Family Interview"),
    ("placement", "Placement Assessment"),
    ("reenrollment", "Re-Enrollment Review"),
    ("annual", "Annual Character Review"),
]

CHURCH_ATTENDANCE_CHOICES = [
    ("active", "Active — Weekly or near-weekly"),
    ("regular", "Regular — Several times per month"),
    ("occasional", "Occasional — Monthly or less"),
    ("sporadic", "Sporadic — Rarely"),
    ("none", "None"),
]


class PortraitConfig(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="portrait_configs")
    name = models.CharField(max_length=120)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)
    preamble = models.TextField(blank=True)
    covenant_text = models.TextField(blank=True)
    scripture_anchor = models.CharField(max_length=120, blank=True)

    threshold_strong_accept = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("80.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    threshold_accept = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("65.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    threshold_accept_review = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("50.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    threshold_hold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("35.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    require_faith_formation_minimum = models.BooleanField(default=True)
    faith_minimum_score = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "is_active"])]
        verbose_name = "Portrait of Graduate Config"
        verbose_name_plural = "Portrait of Graduate Configs"

    def __str__(self):
        return f"{self.name} v{self.version}"

    def clean(self):
        if not (
            self.threshold_hold
            < self.threshold_accept_review
            <= self.threshold_accept
            <= self.threshold_strong_accept
        ):
            raise ValidationError(
                "Thresholds must satisfy: Hold < Accept with Review <= Accept <= Strong Accept."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        if self.is_active:
            with tenant_context(self.school):
                PortraitConfig.objects.filter(school=self.school, is_active=True).exclude(pk=self.pk).update(is_active=False)

    @property
    def domain_weights_valid(self) -> bool:
        total = sum((d.weight for d in self.domains.filter(is_active=True)), Decimal("0.0000"))
        return abs(total - Decimal("1.0000")) < Decimal("0.0100")


class PoGDomain(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="portrait_domains")
    config = models.ForeignKey(PortraitConfig, on_delete=models.CASCADE, related_name="domains")
    name = models.CharField(max_length=120)
    domain_type = models.CharField(max_length=40, choices=FAITH_DOMAIN_CHOICES, default="custom")
    description = models.TextField()
    scripture_reference = models.CharField(max_length=200, blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.2000"),
        validators=[
            MinValueValidator(Decimal("0.0001")),
            MaxValueValidator(Decimal("1.0000")),
        ],
    )
    is_faith_anchor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["config", "is_active", "order"])]
        verbose_name = "PoG Domain"
        verbose_name_plural = "PoG Domains"

    def __str__(self):
        return f"{self.config.name} — {self.name}"

    @property
    def weight_percentage(self) -> float:
        return round(float(self.weight) * 100, 1)


class PoGRubricLevel(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="portrait_rubric_levels")
    domain = models.ForeignKey(PoGDomain, on_delete=models.CASCADE, related_name="rubric_levels")
    level = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    label = models.CharField(max_length=60)
    descriptor = models.TextField()

    class Meta:
        ordering = ["level"]
        unique_together = [["domain", "level"]]
        verbose_name = "Rubric Level"
        verbose_name_plural = "Rubric Levels"

    def __str__(self):
        return f"{self.domain.name} — {self.level}: {self.label}"


class AdmissionsPoGRecord(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="portrait_records")
    applicant_id = models.CharField(max_length=60, db_index=True)
    config = models.ForeignKey(PortraitConfig, on_delete=models.PROTECT, related_name="pog_records")
    context = models.CharField(max_length=20, choices=CONTEXT_CHOICES, default="interview")
    scored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portrait_scores_given",
    )
    scored_at = models.DateTimeField(auto_now_add=True)

    family_faith_statement = models.TextField(blank=True)
    church_attendance = models.CharField(max_length=20, choices=CHURCH_ATTENDANCE_CHOICES, blank=True)
    church_name = models.CharField(max_length=120, blank=True)
    student_faith_notes = models.TextField(blank=True)
    general_interview_notes = models.TextField(blank=True)

    composite_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    composite_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, blank=True)
    faith_gate_triggered = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scored_at"]
        indexes = [
            models.Index(fields=["school", "applicant_id", "scored_at"]),
            models.Index(fields=["school", "recommendation"]),
        ]
        verbose_name = "Admissions PoG Record"
        verbose_name_plural = "Admissions PoG Records"

    def __str__(self):
        pct = self.composite_percentage if self.composite_percentage is not None else "—"
        rec = self.recommendation or "pending"
        return f"PoG Record — applicant {self.applicant_id} ({pct}%) [{rec}]"

    @property
    def scored_domains_count(self) -> int:
        return self.domain_scores.filter(score__isnull=False).count()

    @property
    def required_domains_count(self) -> int:
        return self.config.domains.filter(is_active=True).count()


class PoGDomainScore(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="portrait_domain_scores")
    record = models.ForeignKey(AdmissionsPoGRecord, on_delete=models.CASCADE, related_name="domain_scores")
    domain = models.ForeignKey(PoGDomain, on_delete=models.PROTECT, related_name="scores_given")
    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=SCORE_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    rubric_level = models.ForeignKey(
        PoGRubricLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_scores",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain__order"]
        unique_together = [["record", "domain"]]
        verbose_name = "PoG Domain Score"
        verbose_name_plural = "PoG Domain Scores"

    def __str__(self):
        return f"{self.domain.name}: {self.score or '—'}/5"

    def clean(self):
        if self.rubric_level and self.rubric_level.domain_id != self.domain_id:
            raise ValidationError("Rubric level must belong to the selected domain.")
        if self.score and self.rubric_level and self.score != self.rubric_level.level:
            raise ValidationError("Score must match the selected rubric level.")

    @property
    def weighted_score(self) -> Decimal | None:
        if self.score is None:
            return None
        return Decimal(str(self.score)) * self.domain.weight
