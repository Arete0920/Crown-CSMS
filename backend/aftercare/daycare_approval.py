"""Director-scoped, default-off Diadem evidence reviews (#595).

No action in this service sets is_active/is_qualified, policy_verified_at,
or the room's operational limits. Independent external determinations remain
a prerequisite to any future operational activation.
"""
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from audit.models import AuditLog
from core.models import UserAccount, UserRole
from core.permissions import user_has_permission

from .daycare_checkin_models import DaycareRoomStaffCoverage
from .daycare_models import DaycareSite, DaycareRoom
from .daycare_setup import require_configuration
from .daycare_approval_models import (
    DaycareStaffQualificationReview, DaycareRoomPolicyReview,
    DaycareStaffAssignmentReview,
)

REVIEW_PERMISSION = "diadem.daycare.safety_review"
class SafetyReviewConflict(Exception):
    pass


def require_reviewer(school_id, actor_id):
    """No implicit director/superuser grant for safety reviews."""
    school, actor = require_configuration(school_id, actor_id)
    if not user_has_permission(actor, REVIEW_PERMISSION, school=school):
        raise PermissionDenied("Explicit safety-review permission required.")
    return school, actor


def _scope(school, site_id, room_id, *, lock=True):
    sites = DaycareSite.objects.select_for_update() if lock else DaycareSite.objects
    rooms = DaycareRoom.objects.select_for_update() if lock else DaycareRoom.objects
    site = sites.filter(pk=site_id, school=school).first()
    if site is None:
        raise NotFound()
    room = rooms.filter(pk=room_id, site=site, school=school).first()
    if room is None:
        raise NotFound()
    return site, room


def _audit(review, actor, kind):
    AuditLog.objects.create(
        user_id=actor.pk, action=f"diadem.daycare.safety_review.{kind}",
        model=type(review).__name__, object_id=str(review.pk),
        metadata={
            "school_id": str(review.school_id),
            "site_id": str(review.site_id) if hasattr(review, "site_id") else str(review.proposal.site_id),
            "room_id": str(review.room_id) if hasattr(review, "room_id") else (
                str(review.proposal.room_id) if hasattr(review, "proposal_id") else None
            ),
            "subject_id": str(
                review.staff_id if hasattr(review, "staff_id")
                else review.room_id if hasattr(review, "room_id")
                else review.proposal_id
            ),
            "decision": review.decision,
            "request_key": str(review.request_key),
            "supersedes_id": str(review.supersedes_id) if review.supersedes_id else None,
            "operational_activation": False,
        },
    )


def _review_is_audited(review, kind):
    """Only an attributable committed review event establishes provenance.

    Direct ORM creation or historical unverified rows must never appear as
    independently reviewed evidence on the decision/readback path.
    """
    return AuditLog.objects.filter(
        action=f"diadem.daycare.safety_review.{kind}",
        model=type(review).__name__,
        object_id=str(review.pk),
        user_id=review.reviewed_by_id,
        metadata__school_id=str(review.school_id),
        metadata__request_key=str(review.request_key),
        metadata__decision=review.decision,
        metadata__operational_activation=False,
    ).exists()


def _existing_or_new(model, school, actor, kind, values):
    """One idempotent decision and one audit, or a conflict without partial writes."""
    existing = model.objects.filter(school=school, request_key=values["request_key"]).first()
    if existing is not None:
        for key, value in values.items():
            if key == "reviewed_at":
                continue  # server-generated on first commit; never a client input
            if getattr(existing, key) != value:
                raise SafetyReviewConflict("Request key is already used for another review.")
        if existing.reviewed_by_id != actor.pk:
            raise SafetyReviewConflict("Review ownership differs from the original request.")
        if not _review_is_audited(existing, kind):
            raise SafetyReviewConflict("Existing review lacks an attributable audit event.")
        return existing, False
    # Exactly one current decision per subject. Corrections must explicitly
    # supersede the latest decision, preventing contradictory unsuperseded
    # reviews from later being mistaken for activation-ready evidence.
    if model is DaycareStaffQualificationReview:
        subject = model.objects.filter(
            school=school, site=values["site"], staff=values["staff"],
            qualification_code=values["qualification_code"],
        )
    elif model is DaycareRoomPolicyReview:
        subject = model.objects.filter(school=school, room=values["room"])
    else:
        subject = model.objects.filter(school=school, proposal=values["proposal"])
    superseded = model.objects.filter(
        supersedes__isnull=False,
    ).values_list("supersedes_id", flat=True)
    current = list(subject.exclude(pk__in=superseded).values_list("pk", flat=True))
    predecessor_id = values.get("supersedes_id")
    if len(current) > 1 or (
        (current and predecessor_id != current[0])
        or (not current and predecessor_id is not None)
    ):
        raise SafetyReviewConflict("A new decision must supersede the current subject review.")
    if values.get("supersedes_id"):
        previous = model.objects.select_for_update().filter(
            pk=values["supersedes_id"], school=school,
        ).first()
        if previous is None:
            raise ValidationError({"supersedes_id": "Review to supersede was not found."})
        if model.objects.filter(supersedes=previous).exists():
            raise SafetyReviewConflict("This review was already superseded.")
    values = {**values, "school": school, "reviewed_by": actor}
    try:
        review = model.objects.create(**values)
    except (ModelValidationError, IntegrityError) as exc:
        raise SafetyReviewConflict("Review values conflict with existing safety evidence.") from exc
    _audit(review, actor, kind)
    return review, True


def submit_qualification(*, school_id, actor_id, site_id, room_id, values):
    with transaction.atomic():
        school, actor = require_reviewer(school_id, actor_id)
        site, _room = _scope(school, site_id, room_id)
        staff = UserAccount.objects.select_for_update().filter(
            pk=values["staff_id"], school=school, is_active=True,
        ).first()
        if (staff is None or staff.pk == actor.pk or not UserRole.objects.filter(
                user=staff, school=school, role_code="DAYCARE_STAFF",
        ).exists()):
            raise ValidationError({"staff_id": "Independently reviewed school-bound staff required."})
        return _existing_or_new(
            DaycareStaffQualificationReview, school, actor, "qualification",
            {**values, "site": site, "staff": staff, "staff_id": staff.pk,
             "reviewed_at": timezone.now()},
        )


def submit_policy(*, school_id, actor_id, site_id, room_id, values):
    with transaction.atomic():
        school, actor = require_reviewer(school_id, actor_id)
        site, room = _scope(school, site_id, room_id)
        if values["jurisdiction"] != site.jurisdiction or not site.jurisdiction:
            raise ValidationError({"jurisdiction": "Policy must match the site's declared jurisdiction."})
        return _existing_or_new(
            DaycareRoomPolicyReview, school, actor, "policy",
            {**values, "site": site, "room": room, "reviewed_at": timezone.now()},
        )


def _latest_review(record, model):
    return not model.objects.filter(supersedes=record).exists()


def submit_assignment(*, school_id, actor_id, site_id, room_id, values):
    with transaction.atomic():
        school, actor = require_reviewer(school_id, actor_id)
        site, room = _scope(school, site_id, room_id)
        proposal = DaycareRoomStaffCoverage.objects.select_for_update().filter(
            pk=values["proposal_id"], school=school, site=site, room=room,
            is_active=False, is_qualified=False, verified_at__isnull=True,
            verified_by__isnull=True, qualification_evidence="",
        ).first()
        if proposal is None or proposal.staff_id == actor.pk:
            raise ValidationError({"proposal_id": "An unapproved school-bound proposal is required."})
        if not AuditLog.objects.filter(
            action="diadem.daycare.staff_proposal.created",
            model="DaycareRoomStaffCoverage", object_id=str(proposal.pk),
            metadata__school_id=str(school.pk),
            metadata__site_id=str(site.pk),
            metadata__room_id=str(room.pk),
            metadata__staff_id=str(proposal.staff_id),
        ).exists():
            raise SafetyReviewConflict("Proposal has no attributed creation event.")
        qualification = DaycareStaffQualificationReview.objects.select_for_update().filter(
            pk=values["qualification_review_id"], school=school, site=site,
            staff_id=proposal.staff_id,
        ).first()
        policy = DaycareRoomPolicyReview.objects.select_for_update().filter(
            pk=values["room_policy_review_id"], school=school, site=site, room=room,
        ).first()
        if qualification is None or policy is None:
            raise ValidationError({"detail": "Referenced reviews must match school, staff and room."})
        if (not _review_is_audited(qualification, "qualification")
                or not _review_is_audited(policy, "policy")):
            raise SafetyReviewConflict("Referenced safety reviews lack attributed audit events.")
        if values["decision"] == "APPROVED":
            now = timezone.now()
            if (qualification.decision != "VERIFIED" or policy.decision != "APPROVED"
                    or not _latest_review(qualification, DaycareStaffQualificationReview)
                    or not _latest_review(policy, DaycareRoomPolicyReview)
                    or qualification.effective_from > values["effective_from"]
                    or qualification.effective_until < values["effective_until"]
                    or policy.effective_from > values["effective_from"]
                    or policy.effective_until < values["effective_until"]
                    or values["effective_until"] <= now):
                raise SafetyReviewConflict("Current qualification and policy evidence do not cover this interval.")
        return _existing_or_new(
            DaycareStaffAssignmentReview, school, actor, "assignment",
            {
                "proposal": proposal,
                "qualification_review": qualification,
                "room_policy_review": policy,
                **{k: v for k, v in values.items() if k not in (
                    "proposal_id", "qualification_review_id", "room_policy_review_id",
                )},
                "reviewed_at": timezone.now(),
            },
        )


def list_reviews(*, school_id, actor_id, site_id, room_id):
    """Readback is deliberately factual, not a representation of live coverage."""
    with transaction.atomic():
        school, _actor = require_reviewer(school_id, actor_id)
        site, room = _scope(school, site_id, room_id, lock=False)
        room_staff = DaycareRoomStaffCoverage.objects.filter(
            school=school, site=site, room=room,
        ).values_list("staff_id", flat=True)
        qualifications = DaycareStaffQualificationReview.objects.filter(
            school=school, site=site, staff_id__in=room_staff,
        ).order_by("created_at", "pk")
        policies = DaycareRoomPolicyReview.objects.filter(
            school=school, site=site, room=room,
        ).order_by("created_at", "pk")
        assignments = DaycareStaffAssignmentReview.objects.filter(
            school=school, proposal__site=site, proposal__room=room,
        ).order_by("created_at", "pk")
        def item(row, subject):
            record = {
                "review_id": str(row.pk), "subject_id": str(subject),
                "decision": row.decision,
                "effective_from": row.effective_from.isoformat(),
                "effective_until": row.effective_until.isoformat(),
                "reviewed_at": row.reviewed_at.isoformat(),
                "reviewed_by_id": str(row.reviewed_by_id),
                "source_authority": row.source_authority,
                "source_reference": row.source_reference,
                "supersedes_id": str(row.supersedes_id) if row.supersedes_id else None,
                "superseded": type(row).objects.filter(supersedes=row).exists(),
                "operational_activation": False,
            }
            if isinstance(row, DaycareStaffQualificationReview):
                record["qualification_code"] = row.qualification_code
            elif isinstance(row, DaycareRoomPolicyReview):
                record.update({
                    "jurisdiction": row.jurisdiction,
                    "policy_version": row.policy_version,
                    "facility_license_reference": row.facility_license_reference,
                    "age_min_months": row.age_min_months,
                    "age_max_months": row.age_max_months,
                    "licensed_capacity": row.licensed_capacity,
                    "max_group_size": row.max_group_size,
                    "max_children_per_staff": row.max_children_per_staff,
                })
            else:
                qualification = row.qualification_review
                policy = row.room_policy_review
                proposal = row.proposal
                now = timezone.now()
                planning_evidence_current = bool(
                    row.decision == "APPROVED"
                    and not record["superseded"]
                    and row.effective_from <= now < row.effective_until
                    and qualification.decision == "VERIFIED"
                    and policy.decision == "APPROVED"
                    and _latest_review(qualification, DaycareStaffQualificationReview)
                    and _latest_review(policy, DaycareRoomPolicyReview)
                    and _review_is_audited(qualification, "qualification")
                    and _review_is_audited(policy, "policy")
                    and qualification.effective_from <= row.effective_from
                    and qualification.effective_until >= row.effective_until
                    and policy.effective_from <= row.effective_from
                    and policy.effective_until >= row.effective_until
                    and not proposal.is_active
                    and not proposal.is_qualified
                    and not proposal.qualification_evidence
                    and proposal.verified_by_id is None
                    and proposal.verified_at is None
                    and proposal.staff.is_active
                )
                record.update({
                    "qualification_review_id": str(row.qualification_review_id),
                    "room_policy_review_id": str(row.room_policy_review_id),
                    # A current *planning-evidence* indication is not
                    # childcare approval and never confers on-duty authority.
                    "planning_evidence_current": planning_evidence_current,
                })
            return record
        return {
            "school_id": str(school.pk), "site_id": str(site.pk),
            "room_id": str(room.pk), "as_of": timezone.now().isoformat(),
            "operational_activation": False,
            "qualifications": [
                item(row, row.staff_id) for row in qualifications
                if _review_is_audited(row, "qualification")
            ],
            "policies": [
                item(row, row.room_id) for row in policies
                if _review_is_audited(row, "policy")
            ],
            "assignments": [
                item(row, row.proposal_id) for row in assignments
                if _review_is_audited(row, "assignment")
            ],
        }
