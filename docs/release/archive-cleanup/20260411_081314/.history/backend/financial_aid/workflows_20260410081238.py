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
from .need_index import calculate_need_index


SOLOMON_ARTICLE_SLUG = "christian-principles-for-aid-distribution"


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


def _ensure_solomon_article() -> str:
    article, _ = HelpArticle.objects.update_or_create(
        slug=SOLOMON_ARTICLE_SLUG,
        defaults={
            "title": "Christian principles for aid distribution",
            "summary": "A consistent Crown2026 guide for transparent, fair financial-aid review.",
            "content": (
                "Financial aid decisions should remain transparent, school-scoped, and evidence-based.\n\n"
                "Use household need, mission fit, and hardship context carefully. Record the rationale, "
                "route complex cases to committee review, and preserve an audit trail for every decision."
            ),
            "module": "financial_aid",
            "article_type": HelpArticle.TYPE_GUIDE,
            "visibility": HelpArticle.VISIBILITY_STAFF,
            "state": HelpArticle.STATE_PUBLISHED,
            "published": True,
        },
    )
    return article.slug


def _update_crown_compass(*, application: FinancialAidApplication, need_index: int, amount: Decimal) -> bool:
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
        f"with Need Index {need_index} and provisional aid ${amount}."
    )
    if summary not in highlights:
        highlights.append(summary)

    if need_index >= 75:
        watch_item = (
            f"High-need financial aid case for household {application.household_id} is awaiting final approval."
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

    need_index = calculate_need_index(application)
    recommended_amount = _recommended_amount(need_index)
    recommended_bucket = _recommended_bucket(need_index)
    actor_uuid = _normalize_optional_uuid(actor_user_id)

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

    AidAuditEvent.objects.bulk_create(
        [
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
    )

    solomon_article_slug = _ensure_solomon_article()
    crown_compass_refreshed = _update_crown_compass(
        application=application,
        need_index=need_index,
        amount=recommended_amount,
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
        "crown_compass_refreshed": crown_compass_refreshed,
        "crown_discernment": discernment,
    }
