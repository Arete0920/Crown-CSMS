from __future__ import annotations

from collections import Counter
from django.utils import timezone

from .models import CampaignTouchpoint, LeadStage, MarketingLead


def register_admissions_submit(application, *, source: str = "", start_term: str = ""):
    leads = list(MarketingLead.objects.filter(school_id=application.school_id, application=application))
    if not leads:
        leads = [
            MarketingLead.objects.create(
                school_id=application.school_id,
                application=application,
                stage=LeadStage.APPLICATION_SUBMITTED,
                first_source=source or "",
                primary_source=source or "",
            )
        ]
    for lead in leads:
        lead.stage = LeadStage.APPLICATION_SUBMITTED
        if source and not lead.first_source:
            lead.first_source = source
        if source:
            lead.primary_source = source
        lead.save(update_fields=["stage", "first_source", "primary_source", "updated_at"])
    return leads


def register_workflow_update(application, *, stage: str, summary: str, payload=None, created_by=None):
    leads = list(MarketingLead.objects.filter(school_id=application.school_id, application=application))
    if not leads:
        leads = [MarketingLead.objects.create(school_id=application.school_id, application=application, stage=stage)]
    now = timezone.now()
    for lead in leads:
        lead.stage = stage
        lead.last_touch_at = now
        if stage == LeadStage.ENROLLED and not lead.conversion_source:
            lead.conversion_source = lead.primary_source or lead.first_source
        lead.save(update_fields=["stage", "last_touch_at", "conversion_source", "updated_at"])
        CampaignTouchpoint.objects.create(
            school_id=application.school_id,
            campaign=lead.campaign,
            lead=lead,
            channel="system",
            summary=summary[:240],
            outcome=stage,
            metadata_json=payload or {},
            occurred_at=now,
            created_by_user_id=getattr(created_by, "id", None),
        )
    return leads


def record_touchpoint(*, lead, channel: str, summary: str, outcome: str = "", metadata=None, created_by=None):
    now = timezone.now()
    lead.last_touch_at = now
    lead.save(update_fields=["last_touch_at", "updated_at"])
    return CampaignTouchpoint.objects.create(
        school=lead.school,
        campaign=lead.campaign,
        lead=lead,
        channel=channel,
        summary=summary[:240],
        outcome=outcome[:120],
        metadata_json=metadata or {},
        occurred_at=now,
        created_by_user_id=getattr(created_by, "id", None),
    )


def build_follow_up_playbook(stage: str):
    playbooks = {
        LeadStage.INQUIRY: [
            {"day": 0, "action": "Acknowledge inquiry and confirm family priorities."},
            {"day": 1, "action": "Personal admissions call or message."},
            {"day": 3, "action": "Invite family to tour or next admissions event."},
            {"day": 7, "action": "Share a mission/Portrait story aligned to family interests."},
        ],
        LeadStage.TOUR_SCHEDULED: [
            {"day": 0, "action": "Confirm tour details and family goals."},
            {"day": 1, "action": "Send post-tour thank-you and next-step application link."},
            {"day": 4, "action": "Answer unresolved questions and affordability concerns."},
        ],
        LeadStage.APPLICATION_STARTED: [
            {"day": 0, "action": "Confirm application support contact."},
            {"day": 3, "action": "Remind family of incomplete application items."},
            {"day": 7, "action": "Offer financial-aid pathway when affordability is a barrier."},
        ],
        LeadStage.APPLICATION_SUBMITTED: [
            {"day": 0, "action": "Confirm receipt and decision timeline."},
            {"day": 3, "action": "Resolve missing checklist or interview items."},
        ],
        LeadStage.ACCEPTED: [
            {"day": 0, "action": "Celebrate acceptance and explain enrollment steps."},
            {"day": 2, "action": "Follow up on contract, deposit, and affordability questions."},
            {"day": 7, "action": "Escalate unresolved accepted-to-enrolled barriers."},
        ],
    }
    return playbooks.get(stage, [])


def build_campaign_snapshot(campaign):
    from aid.models import AidAward
    from core.models import Enrollment
    from enrollment_period_wizard.models import GradeCapacity
    from spiritual_life.formation_models import PortraitDomain

    grade = campaign.target_grade_code
    year = campaign.academic_year
    capacity = None
    current_enrolled = 0
    if grade and year:
        capacity = GradeCapacity.objects.filter(school=campaign.school, academic_year=year, grade_code=grade).first()
        current_enrolled = Enrollment.objects.filter(
            school=campaign.school,
            academic_year=year,
            grade_level__code=grade,
            status="ENROLLED",
        ).count()
    target_seats = int(capacity.target_seats) if capacity else None
    empty_seats = max(target_seats - current_enrolled, 0) if target_seats is not None else None

    portrait_qs = PortraitDomain.objects.filter(school=campaign.school, is_active=True)
    selected_ids = [str(v) for v in (campaign.portrait_domain_ids or [])]
    if selected_ids:
        portrait_qs = portrait_qs.filter(id__in=selected_ids)
    portrait = list(portrait_qs.values("id", "name", "description", "scripture_anchor")[:12])
    for row in portrait:
        row["id"] = str(row["id"])

    aid_committed_cents = 0
    if grade and year:
        aid_committed_cents = sum(
            AidAward.objects.filter(
                school=campaign.school,
                academic_year=year,
                student__current_grade_level__code=grade,
                award_type=AidAward.TYPE_MARKETING,
                decision_status=AidAward.DECISION_ACCEPTED,
            ).values_list("awarded_cents", flat=True)
        )

    leads = campaign.leads.all()
    stage_counts = Counter(leads.values_list("stage", flat=True))
    enrolled = int(stage_counts.get(LeadStage.ENROLLED, 0))
    inquiry_count = int(stage_counts.get(LeadStage.INQUIRY, 0))
    application_count = int(stage_counts.get(LeadStage.APPLICATION_SUBMITTED, 0)) + int(stage_counts.get(LeadStage.APPLICATION_STARTED, 0))
    due_followups = leads.filter(next_follow_up_at__lte=timezone.now()).exclude(stage__in=[LeadStage.ENROLLED, LeadStage.LOST]).count()

    tuition = int(campaign.tuition_per_student_cents or 0)
    goal = int(campaign.enrollment_goal or 0)
    planned_aid_each = int((campaign.aid_strategy or {}).get("planned_aid_per_enrollment_cents") or 0)
    projected_gross = goal * tuition
    projected_aid = goal * planned_aid_each
    projected_net_first_year = max(projected_gross - projected_aid - int(campaign.budget_cents or 0), 0)
    projected_lifetime_net = max(
        goal * max(tuition - planned_aid_each, 0) * int(campaign.expected_retention_years or 1) - int(campaign.budget_cents or 0),
        0,
    )
    actual_gross = enrolled * tuition
    actual_net_before_aid = max(actual_gross - int(campaign.actual_spend_cents or 0), 0)

    return {
        "campaign_id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "capacity": {
            "grade_code": grade or None,
            "target_seats": target_seats,
            "current_enrolled": current_enrolled,
            "empty_seats": empty_seats,
            "new_students_allowed": bool(capacity.new_students_allowed) if capacity else None,
        },
        "portrait": portrait,
        "target_segment": campaign.target_segment or {},
        "aid": {
            "strategy": campaign.aid_strategy or {},
            "accepted_marketing_aid_cents_for_grade": aid_committed_cents,
            "campaign_attribution_verified": False,
        },
        "follow_up_playbooks": {stage: build_follow_up_playbook(stage) for stage in stage_counts.keys()},
        "funnel": {
            "total_leads": leads.count(),
            "inquiries": inquiry_count,
            "applications": application_count,
            "enrolled": enrolled,
            "by_stage": dict(stage_counts),
            "followups_due": due_followups,
            "touchpoints": campaign.touchpoints.count(),
        },
        "economics": {
            "budget_cents": int(campaign.budget_cents or 0),
            "actual_spend_cents": int(campaign.actual_spend_cents or 0),
            "tuition_per_student_cents": tuition,
            "projected_gross_tuition_cents": projected_gross,
            "projected_aid_cents": projected_aid,
            "projected_net_first_year_cents": projected_net_first_year,
            "projected_lifetime_net_tuition_cents": projected_lifetime_net,
            "actual_gross_tuition_cents": actual_gross,
            "actual_net_before_aid_cents": actual_net_before_aid,
            "cost_per_enrollment_cents": round(int(campaign.actual_spend_cents or 0) / enrolled) if enrolled else None,
            "actual_net_after_aid_cents": None,
            "actual_net_after_aid_note": "Unavailable until aid is explicitly linked to campaign-attributed enrollments.",
        },
    }
