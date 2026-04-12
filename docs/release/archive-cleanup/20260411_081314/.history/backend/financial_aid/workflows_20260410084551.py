from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from core.models import School
from onboarding.models_tasks import HelpArticle
from signals.models import BoardExecutiveMetric

from .models import AidAuditEvent, AidAward, AidBucket, FinancialAidApplication
from .need_index import calculate_need_index_breakdown


SOLOMON_ARTICLE_SLUG = "christian-principles-for-aid-distribution"
SOLOMON_RELATED_ARTICLES = (
    {
        "slug": "christian-principles-for-aid-distribution",
        "title": "Biblical Principles for Financial Aid Distribution",
        "summary": "A mission-aligned guide to stewardship, justice, mercy, and wise aid review.",
        "content": (
            "Financial aid is not only an administrative task; it is a ministry of stewardship, justice, and mercy.\n\n"
            "1. Stewardship (Luke 12:48; 1 Corinthians 4:2) — Aid is a sacred trust. Schools should steward donor and tuition funds wisely, prioritizing families with genuine need while encouraging responsibility.\n"
            "2. Justice & Mercy (Micah 6:8; Matthew 23:23) — Use consistent criteria while still reviewing hardship with compassion.\n"
            "3. Care for the Vulnerable (James 1:27; Proverbs 19:17) — Give careful attention to families facing hardship, including single-parent, missionary, pastoral, and large-family contexts.\n"
            "4. Generosity & Cheerfulness (2 Corinthians 9:7) — Aid should be offered with grace, not suspicion or entitlement.\n"
            "5. Equity, Not Equality (2 Corinthians 8:13–15) — Seek fairness in opportunity, not identical awards.\n"
            "6. Wisdom & Discernment (Proverbs 3:5–6; James 1:5) — Review need data prayerfully with multiple trusted leaders.\n"
            "7. Dignity & Responsibility (2 Thessalonians 3:10; Proverbs 6:6–11) — Where appropriate, pair assistance with work-study, service, or follow-through expectations."
        ),
    },
    {
        "slug": "mercy-and-justice-in-aid-decisions",
        "title": "How to Apply Mercy and Justice in Aid Decisions",
        "summary": "How committees can balance consistent criteria with compassion for real hardship.",
        "content": (
            "Use the Crown Discernment Need Index as a transparent starting point, then document any hardship, ministry, or family factors that call for extra mercy.\n\n"
            "Committee checklist:\n"
            "- Confirm the quantitative need signal and note the strongest drivers.\n"
            "- Review hardship details prayerfully and consistently.\n"
            "- Document why an award aligns with both fairness and compassion.\n"
            "- Where appropriate, include a work-study or service expectation that protects dignity and responsibility."
        ),
    },
    {
        "slug": "stewardship-guidelines-for-aid-budgets",
        "title": "Stewardship Guidelines for Aid Budgets",
        "summary": "Budget guardrails for mission-aligned aid distribution.",
        "content": (
            "Aid budgets should be stewarded carefully so the school can serve families over the long term.\n\n"
            "Recommended guardrails:\n"
            "- Prioritize demonstrated need and documented hardship.\n"
            "- Review aggregate aid commitments regularly against tuition projections.\n"
            "- Escalate exceptions to committee review instead of making isolated one-off decisions.\n"
            "- Preserve a clear audit trail for every recommendation and final award."
        ),
    },
    {
        "slug": "biblical-view-of-work-and-diligence",
        "title": "Biblical View of Work and Diligence",
        "summary": "How work-study reflects diligence, stewardship, and service.",
        "content": (
            "Work-study can be a practical expression of Christian diligence and partnership.\n\n"
            "Key themes:\n"
            "- 2 Thessalonians 3:10 reminds us to value faithful effort and responsibility.\n"
            "- Proverbs 6:6–11 commends diligence and wise planning.\n"
            "- Colossians 3:23 calls students to work heartily as for the Lord.\n"
            "Schools can use work-study to reduce tuition burden while building character and ownership."
        ),
    },
    {
        "slug": "how-work-study-builds-character",
        "title": "How Work-Study Builds Character",
        "summary": "A practical guide for pairing tuition support with meaningful service opportunities.",
        "content": (
            "A healthy work-study program should reinforce dignity, accountability, and service.\n\n"
            "Best practices:\n"
            "- Assign age-appropriate, meaningful responsibilities.\n"
            "- Track hours and credit transparently.\n"
            "- Pair work with reflection and encouragement.\n"
            "- Celebrate students who serve faithfully and grow in responsibility."
        ),
    },
    {
        "slug": "biblical-mentorship-multiplication",
        "title": "Biblical Mentorship and Multiplication",
        "summary": "A guide to discipleship-centered mentorship rooted in 2 Timothy 2:2 and Titus 2.",
        "content": (
            "Mentorship can strengthen a student’s faith, character, and academic resilience through intentional discipleship.\n\n"
            "Schools can use mentorship pathways to pair students with trusted peers or adults who provide encouragement, accountability, and practical support."
        ),
    },
    {
        "slug": "mentorship-reflection-prompts",
        "title": "Mentorship Reflection Prompts",
        "summary": "Questions mentors and mentees can use to reflect on growth and service each term.",
        "content": (
            "Suggested prompts:\n"
            "- What have you learned that you can pass on to someone else?\n"
            "- How is God using this relationship to build humility, wisdom, or perseverance?\n"
            "- What next step would help this student flourish spiritually and academically?"
        ),
    },
)

BIBLICAL_FINANCIAL_AID_PRINCIPLES = [
    {
        "title": "Stewardship",
        "scripture": "Luke 12:48; 1 Corinthians 4:2",
        "summary": "Aid is a sacred trust and should be stewarded wisely.",
    },
    {
        "title": "Justice & Mercy",
        "scripture": "Micah 6:8; Matthew 23:23",
        "summary": "Balance fairness in criteria with compassion for hardship.",
    },
    {
        "title": "Care for the Vulnerable",
        "scripture": "James 1:27; Proverbs 19:17",
        "summary": "Pay special attention to families facing genuine hardship.",
    },
    {
        "title": "Generosity & Cheerfulness",
        "scripture": "2 Corinthians 9:7",
        "summary": "Give with grace rather than judgment or entitlement.",
    },
    {
        "title": "Equity, Not Equality",
        "scripture": "2 Corinthians 8:13–15",
        "summary": "Aim for fair opportunity rather than identical outcomes.",
    },
    {
        "title": "Wisdom & Discernment",
        "scripture": "Proverbs 3:5–6; James 1:5",
        "summary": "Review each case prayerfully using transparent data.",
    },
    {
        "title": "Dignity & Responsibility",
        "scripture": "2 Thessalonians 3:10; Proverbs 6:6–11",
        "summary": "Encourage diligence and responsibility where appropriate.",
    },
]

WORK_STUDY_HOURLY_CREDIT = Decimal("15.00")
WORK_STUDY_MAX_HOURS_PER_WEEK = 8
WORK_STUDY_SOLOMON_SLUGS = [
    "biblical-view-of-work-and-diligence",
    "how-work-study-builds-character",
]
MENTORSHIP_SOLOMON_SLUGS = [
    "biblical-mentorship-multiplication",
    "mentorship-reflection-prompts",
]
WORK_STUDY_ROLE_LIBRARY = [
    {
        "title": "Office Help",
        "category": "Work-Study: Office Support",
        "description": "Front-office hospitality, filing, mailers, and welcome-desk support.",
    },
    {
        "title": "Groundskeeping Support",
        "category": "Work-Study: Campus Care",
        "description": "Light campus setup, cleanup, and stewardship tasks under supervision.",
    },
    {
        "title": "Tutoring Assistant",
        "category": "Work-Study: Peer Tutoring",
        "description": "Assist younger students with study halls, reading support, or homework labs.",
    },
    {
        "title": "Chapel & Event Setup",
        "category": "Work-Study: Chapel Setup",
        "description": "Help prepare chairs, materials, AV setup, and event hospitality.",
    },
]


def _normalize_optional_uuid(value: UUID | str | None) -> UUID | None:
    if value in (None, ""):
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _recommended_bucket(need_index: float) -> str:
    if need_index >= 85:
        return AidBucket.HARDSHIP
    if need_index >= 65:
        return AidBucket.NEED
    if need_index >= 45:
        return AidBucket.MISSION
    return AidBucket.MARKETING


def _recommended_amount(need_index: float) -> Decimal:
    if need_index >= 85:
        return Decimal("12000.00")
    if need_index >= 65:
        return Decimal("8000.00")
    if need_index >= 45:
        return Decimal("5000.00")
    if need_index >= 25:
        return Decimal("2500.00")
    return Decimal("0.00")


def _ensure_solomon_articles() -> list[str]:
    slugs: list[str] = []
    for article_data in SOLOMON_RELATED_ARTICLES:
        article, _ = HelpArticle.objects.update_or_create(
            slug=article_data["slug"],
            defaults={
                "title": article_data["title"],
                "summary": article_data["summary"],
                "content": article_data["content"],
                "module": "financial_aid",
                "article_type": HelpArticle.TYPE_GUIDE,
                "visibility": HelpArticle.VISIBILITY_STAFF,
                "state": HelpArticle.STATE_PUBLISHED,
                "published": True,
            },
        )
        slugs.append(article.slug)
    return slugs


def _build_review_guidance(*, application: FinancialAidApplication, need_index: float, recommended_amount: Decimal, breakdown: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if bool(getattr(application, "is_pastor_family", False)):
        reasons.append("pastoral or ministry family")
    if bool(getattr(application, "has_financial_hardship", False)):
        reasons.append("reported financial hardship")
    if bool(getattr(application, "has_medical_hardship", False)):
        reasons.append("medical hardship")
    if int(getattr(application, "dependents_in_school", 0) or 0) >= 2:
        reasons.append("multiple children in Christian education")
    if need_index >= 75 and not reasons:
        reasons.append("high calculated need")

    if need_index >= 85:
        discernment_label = "High Need"
    elif need_index >= 65:
        discernment_label = "Moderate-High Need"
    elif need_index >= 45:
        discernment_label = "Moderate Need"
    else:
        discernment_label = "Emerging Need"

    mercy_label = "High Mercy Opportunity" if reasons else "Stewardship Review"
    considerations = [
        "Scripture calls us to steward resources wisely while showing mercy.",
        "Document the rationale clearly for committee and audit review.",
    ]
    if reasons:
        considerations.insert(0, f"This case reflects {', '.join(reasons)}.")

    return {
        "discernment_label": discernment_label,
        "mercy_opportunity": {
            "label": mercy_label,
            "reasons": reasons,
        },
        "biblical_principles": BIBLICAL_FINANCIAL_AID_PRINCIPLES,
        "need_index_breakdown": breakdown,
        "committee_review_text": (
            f"Need Index: {need_index:.1f}/100 ({discernment_label}). "
            f"Recommended action: review a provisional award of ${recommended_amount} "
            f"with prayerful attention to justice, mercy, and stewardship."
        ),
        "mentorship_pathway": {
            "summary": "Mentorship can provide discipleship, accountability, and academic encouragement alongside aid support.",
            "solomon_articles": MENTORSHIP_SOLOMON_SLUGS,
            "reflection_prompt": "Who could faithfully encourage this student in faith, academics, and character this term?",
            "service_hours_can_count": True,
        },
        "considerations": considerations,
    }


def _build_work_study_plan(*, application: FinancialAidApplication, need_index: float, recommended_amount: Decimal) -> dict[str, Any]:
    if need_index >= 85:
        recommended_hours = 8
    elif need_index >= 65:
        recommended_hours = 6
    elif need_index >= 45:
        recommended_hours = 4
    elif need_index >= 25:
        recommended_hours = 3
    else:
        recommended_hours = 0

    enabled = bool(recommended_amount > 0 and recommended_hours > 0)
    monthly_credit = (WORK_STUDY_HOURLY_CREDIT * Decimal(recommended_hours) * Decimal("4")).quantize(Decimal("0.01"))
    semester_credit = (WORK_STUDY_HOURLY_CREDIT * Decimal(recommended_hours) * Decimal("16")).quantize(Decimal("0.01"))
    if recommended_amount > 0:
        semester_credit = min(semester_credit, recommended_amount)

    partnership_note = (
        "Many families appreciate the opportunity to partner with the school through meaningful service, "
        "allowing diligence and responsibility to offset part of the tuition burden."
    )

    return {
        "status": "recommended" if enabled else "optional",
        "recommended_hours_per_week": recommended_hours,
        "max_hours_per_week": WORK_STUDY_MAX_HOURS_PER_WEEK,
        "hourly_credit_rate": str(WORK_STUDY_HOURLY_CREDIT),
        "projected_credit": str(monthly_credit),
        "projected_semester_credit": str(semester_credit),
        "suggested_roles": WORK_STUDY_ROLE_LIBRARY,
        "solomon_articles": WORK_STUDY_SOLOMON_SLUGS,
        "reflection_prompt": "How can this opportunity help the student work heartily as for the Lord? (Colossians 3:23)",
        "program_note": partnership_note,
        "recommended_for_household": str(application.household_id),
        "mentorship_credit_eligible": True,
        "mentorship_note": "Approved mentorship hours may also support service-based partnership expectations when the school allows it.",
    }


def _update_crown_compass(*, application: FinancialAidApplication, need_index: float, amount: Decimal, guidance: dict[str, Any], work_study_plan: dict[str, Any]) -> bool:
    try:
        school = School.objects.get(pk=application.school_id)
    except School.DoesNotExist:
        return False

    metric, _ = BoardExecutiveMetric.objects.get_or_create(
        school=school,
        as_of_date=timezone.localdate(),
    )

    highlights = list(metric.highlights or [])
    watchlist = list(metric.watchlist or [])

    summary = (
        f"Financial aid review prepared household {application.household_id} for committee review "
        f"with Need Index {need_index:.1f} ({guidance.get('discernment_label')}) and provisional aid ${amount}."
    )
    if summary not in highlights:
        highlights.append(summary)

    work_study_summary = (
        f"Work-study could offset up to ${work_study_plan.get('projected_semester_credit')} for household {application.household_id}."
        if work_study_plan.get("status") == "recommended"
        else None
    )
    if work_study_summary and work_study_summary not in highlights:
        highlights.append(work_study_summary)

    mentorship_summary = guidance.get("mentorship_pathway", {}).get("summary")
    if mentorship_summary and mentorship_summary not in highlights and need_index >= 45:
        highlights.append(mentorship_summary)

    if need_index >= 75 or guidance.get("mercy_opportunity", {}).get("label") == "High Mercy Opportunity":
        watch_item = (
            f"{guidance.get('mercy_opportunity', {}).get('label', 'Aid review')} for household {application.household_id} "
            f"is awaiting final approval."
        )
        if watch_item not in watchlist:
            watchlist.append(watch_item)

    metric.highlights = highlights[:10]
    metric.watchlist = watchlist[:10]
    metric.save(update_fields=["highlights", "watchlist"])
    return True


def _run_discernment(*, application: FinancialAidApplication, student_features: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not student_features:
        return {"status": "not_run", "reason": "student_features not provided"}

    try:
        from analytics.predictors import run_retention_risk
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    try:
        school = School.objects.get(pk=application.school_id)
        result = run_retention_risk(school, student_features)
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    if isinstance(result, dict) and result.get("error"):
        return {"status": "error", "reason": result["error"]}
    return {"status": "completed", "result": result}


@transaction.atomic
def process_financial_aid_application(
    *,
    application_id: UUID | str,
    student_features: list[dict[str, Any]] | None = None,
    actor_user_id: UUID | str | None = None,
) -> dict[str, Any]:
    """Advance a submitted application into review using existing Crown2026 models."""
    application = FinancialAidApplication.objects.select_for_update().get(pk=application_id)
    if application.status != "submitted":
        return {
            "status": "error",
            "message": "Only submitted financial-aid applications can be processed.",
            "application_id": str(application.id),
        }

    breakdown = calculate_need_index_breakdown(application)
    need_index = breakdown["need_index"]
    recommended_amount = _recommended_amount(need_index)
    recommended_bucket = _recommended_bucket(need_index)
    actor_uuid = _normalize_optional_uuid(actor_user_id)
    review_guidance = _build_review_guidance(
        application=application,
        need_index=need_index,
        recommended_amount=recommended_amount,
        breakdown=breakdown,
    )
    work_study_plan = _build_work_study_plan(
        application=application,
        need_index=need_index,
        recommended_amount=recommended_amount,
    )
    review_guidance["work_study_connection"] = {
        "summary": (
            f"Recommended work-study partnership could offset up to ${work_study_plan['projected_semester_credit']} this term."
            if work_study_plan["status"] == "recommended"
            else "Work-study remains available as an optional discipleship and responsibility pathway."
        ),
        "reflection_prompt": work_study_plan["reflection_prompt"],
    }
    if work_study_plan["status"] == "recommended":
        review_guidance["considerations"].append(
            f"Consider pairing aid with a work-study component worth up to ${work_study_plan['projected_semester_credit']} over the term."
        )
    review_guidance["considerations"].append(
        "Consider whether a mentor or peer-support relationship would strengthen follow-through, encouragement, and belonging for this student."
    )

    application.status = "in_review"
    application.save(update_fields=["status"])

    rationale = (
        f"Need Index {need_index:.1f}/100 based on household income ${application.household_income} "
        f"and household size {application.household_size}."
    )
    award, _ = AidAward.objects.update_or_create(
        application=application,
        school_id=application.school_id,
        defaults={
            "bucket": recommended_bucket,
            "amount": recommended_amount,
            "rationale": rationale,
            "approved_by_user_id": actor_uuid,
        },
    )

    audit_events = [
        AidAuditEvent(
            school_id=application.school_id,
            event_type="APPLICATION_VALIDATED",
            entity_type="FINANCIAL_AID_APPLICATION",
            entity_id=application.id,
            actor_user_id=actor_uuid,
            message=f"Calculated Need Index {need_index}.",
        ),
        AidAuditEvent(
            school_id=application.school_id,
            event_type="DISCERNMENT_REVIEW_CREATED",
            entity_type="FINANCIAL_AID_APPLICATION",
            entity_id=application.id,
            actor_user_id=actor_uuid,
            message=f"Created provisional {recommended_bucket} award recommendation for ${recommended_amount}.",
        ),
        AidAuditEvent(
            school_id=application.school_id,
            event_type="APPLICATION_READY_FOR_REVIEW",
            entity_type="FINANCIAL_AID_APPLICATION",
            entity_id=application.id,
            actor_user_id=actor_uuid,
            message="Application advanced to committee review.",
        ),
    ]
    if work_study_plan["status"] == "recommended":
        audit_events.append(
            AidAuditEvent(
                school_id=application.school_id,
                event_type="WORK_STUDY_RECOMMENDED",
                entity_type="FINANCIAL_AID_APPLICATION",
                entity_id=application.id,
                actor_user_id=actor_uuid,
                message=(
                    f"Recommended work-study plan at ${work_study_plan['hourly_credit_rate']}/hour "
                    f"for up to {work_study_plan['recommended_hours_per_week']} hours weekly."
                ),
            )
        )
    AidAuditEvent.objects.bulk_create(audit_events)

    solomon_related_articles = _ensure_solomon_articles()
    solomon_article_slug = SOLOMON_ARTICLE_SLUG
    crown_compass_refreshed = _update_crown_compass(
        application=application,
        need_index=need_index,
        amount=recommended_amount,
        guidance=review_guidance,
        work_study_plan=work_study_plan,
    )
    discernment = _run_discernment(application=application, student_features=student_features)

    return {
        "status": "success",
        "application_id": str(application.id),
        "review_status": application.status,
        "need_index": need_index,
        "recommended_bucket": recommended_bucket,
        "recommended_amount": str(recommended_amount),
        "award_id": str(award.id),
        "solomon_article_slug": solomon_article_slug,
        "solomon_related_articles": solomon_related_articles,
        "review_guidance": review_guidance,
        "work_study_plan": work_study_plan,
        "crown_compass_refreshed": crown_compass_refreshed,
        "crown_discernment": discernment,
    }
