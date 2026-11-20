"""Append-only, non-operational Diadem safety reviews (#595).

These records are evidence and planning decisions only. No model here grants
licensing, qualification for custody, room activation, or on-duty coverage.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .daycare_models import DaycareScopedRecord


class _InertSafetyReview(DaycareScopedRecord):
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
    )
    reviewed_at = models.DateTimeField(default=timezone.now)
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField()
    source_authority = models.CharField(max_length=160)
    source_reference = models.CharField(max_length=255)
    request_key = models.UUIDField()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        self._require_same_school("reviewed_by")
        if (not self.reviewed_by_id or not self.reviewed_by.is_active
                or not self.source_authority.strip()
                or not self.source_reference.strip()):
            raise ValidationError("Attributed review and external source are required.")
        for value in (self.reviewed_at, self.effective_from, self.effective_until):
            if value is None or timezone.is_naive(value):
                raise ValidationError("Safety review timestamps must be timezone-aware.")
        if self.effective_from >= self.effective_until:
            raise ValidationError("Safety review interval must have positive duration.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Safety reviews are append-only; supersede to correct or revoke.")
        return super().save(*args, **kwargs)


class DaycareStaffQualificationReview(_InertSafetyReview):
    """Evidence-verified suitability review, not a live coverage grant."""

    DECISIONS = [
        ("VERIFIED", "External evidence reviewed"),
        ("REJECTED", "Evidence rejected"),
        ("REVOKED", "Previous review revoked"),
    ]
    site = models.ForeignKey(
        "aftercare.DaycareSite", on_delete=models.PROTECT, related_name="staff_qualification_reviews",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="daycare_qualification_reviews",
    )
    qualification_code = models.CharField(max_length=64)
    decision = models.CharField(max_length=12, choices=DECISIONS)
    supersedes = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="successor",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "request_key"], name="dia_qual_review_retry_uq",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "site", "staff"], name="dia_qual_staff_scope_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site", "staff", "supersedes")
        if self.reviewed_by_id == self.staff_id:
            raise ValidationError("Staff cannot independently review themselves.")
        if not self.qualification_code.strip():
            raise ValidationError("Qualification category is required.")
        if self.supersedes_id and (
            self.supersedes.site_id != self.site_id
            or self.supersedes.staff_id != self.staff_id
            or self.supersedes.qualification_code != self.qualification_code
        ):
            raise ValidationError("Qualification review chain must retain its subject.")
        if self.decision == "REVOKED" and not self.supersedes_id:
            raise ValidationError("Revocation must reference a prior review.")


class DaycareRoomPolicyReview(_InertSafetyReview):
    """Versioned jurisdictional review; cannot set DaycareRoom.is_active."""

    DECISIONS = [
        ("APPROVED", "Policy evidence reviewed"),
        ("REJECTED", "Policy evidence rejected"),
        ("REVOKED", "Previous review revoked"),
    ]
    site = models.ForeignKey(
        "aftercare.DaycareSite", on_delete=models.PROTECT, related_name="room_policy_reviews",
    )
    room = models.ForeignKey(
        "aftercare.DaycareRoom", on_delete=models.PROTECT, related_name="safety_policy_reviews",
    )
    jurisdiction = models.CharField(max_length=16)
    policy_version = models.CharField(max_length=64)
    facility_license_reference = models.CharField(max_length=160)
    age_min_months = models.PositiveIntegerField()
    age_max_months = models.PositiveIntegerField()
    licensed_capacity = models.PositiveIntegerField()
    max_group_size = models.PositiveIntegerField()
    max_children_per_staff = models.PositiveIntegerField()
    decision = models.CharField(max_length=12, choices=DECISIONS)
    supersedes = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="successor",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "request_key"], name="dia_policy_review_retry_uq",
            ),
            models.CheckConstraint(
                condition=models.Q(age_max_months__gte=models.F("age_min_months")),
                name="dia_policy_age_range_ck",
            ),
            models.CheckConstraint(
                condition=models.Q(licensed_capacity__gt=0, max_group_size__gt=0,
                                   max_children_per_staff__gt=0),
                name="dia_policy_positive_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "site", "room"], name="dia_policy_room_scope_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site", "room", "supersedes")
        if self.room_id and self.site_id and self.room.site_id != self.site_id:
            raise ValidationError("Policy review room and site mismatch.")
        if (not self.jurisdiction.strip() or self.jurisdiction != self.site.jurisdiction
                or not self.policy_version.strip()
                or not self.facility_license_reference.strip()):
            raise ValidationError("Matching jurisdiction and source-identified license are required.")
        if (self.age_min_months > self.age_max_months
                or not all((self.licensed_capacity, self.max_group_size,
                            self.max_children_per_staff))):
            raise ValidationError("Explicit, positive room policy limits required.")
        if self.supersedes_id and (
            self.supersedes.site_id != self.site_id
            or self.supersedes.room_id != self.room_id
        ):
            raise ValidationError("Policy review chain must retain its room.")
        if self.decision == "REVOKED" and not self.supersedes_id:
            raise ValidationError("Revocation must reference a prior policy review.")


class DaycareStaffAssignmentReview(_InertSafetyReview):
    """Audited approval of a proposal *for planning only*, never activation."""

    DECISIONS = [
        ("APPROVED", "Planning assignment reviewed"),
        ("REJECTED", "Planning assignment rejected"),
        ("REVOKED", "Previous planning review revoked"),
    ]
    proposal = models.ForeignKey(
        "aftercare.DaycareRoomStaffCoverage", on_delete=models.PROTECT,
        related_name="planning_approval_reviews",
    )
    qualification_review = models.ForeignKey(
        DaycareStaffQualificationReview, on_delete=models.PROTECT,
        related_name="planning_assignment_reviews",
    )
    room_policy_review = models.ForeignKey(
        DaycareRoomPolicyReview, on_delete=models.PROTECT,
        related_name="planning_assignment_reviews",
    )
    decision = models.CharField(max_length=12, choices=DECISIONS)
    supersedes = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="successor",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "request_key"], name="dia_assign_review_retry_uq",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "proposal"], name="dia_assign_prop_scope_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school(
            "proposal", "qualification_review", "room_policy_review", "supersedes",
        )
        if (self.proposal_id and (
            self.qualification_review.staff_id != self.proposal.staff_id
            or self.qualification_review.site_id != self.proposal.site_id
            or self.room_policy_review.site_id != self.proposal.site_id
            or self.room_policy_review.room_id != self.proposal.room_id
        )):
            raise ValidationError("Reviews do not match the proposed assignment.")
        if self.reviewed_by_id == self.proposal.staff_id:
            raise ValidationError("Staff cannot independently approve their own assignment.")
        if self.effective_from < self.proposal.starts_at or self.effective_until > self.proposal.ends_at:
            raise ValidationError("Planning review must remain within the proposed shift.")
        if self.supersedes_id and self.supersedes.proposal_id != self.proposal_id:
            raise ValidationError("Assignment review chain must retain its proposal.")
        if self.decision == "REVOKED" and not self.supersedes_id:
            raise ValidationError("Revocation must reference a prior assignment review.")
