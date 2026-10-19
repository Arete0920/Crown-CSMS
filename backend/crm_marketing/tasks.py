"""Scheduled admission-inquiry work; provider delivery stays in the shared outbox."""
from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from core.models import School
from core.tenant_models import tenant_context

from .inquiry_notifications import (
    STOPPED_STAGES, inquiry_notifications_enabled, queue_due_inquiry_followup, queue_inquiry_notifications,
)
from .models import MarketingLead


@shared_task(name="crm_marketing.tasks.process_inquiry_followups")
def process_inquiry_followups(*, school_id=None, batch_size=100):
    """Record up to ``batch_size`` new due events, skipping already handled windows.

Old overdue leads remain visible to staff. They do not consume the batch budget
again on every tick and cannot starve later leads after their reminder is recorded.
"""
    if not inquiry_notifications_enabled():
        return {"status": "disabled", "checked": 0, "events": 0, "queued": 0, "intake_notices_queued": 0}
    now = timezone.now()
    budget = max(1, min(int(batch_size), 500))
    schools = School.objects.filter(is_active=True).order_by("id")
    if school_id is not None:
        schools = schools.filter(pk=school_id)
    result = {"checked": 0, "events": 0, "queued": 0, "intake_notices_queued": 0}
    for school in schools.iterator():
        with tenant_context(school):
            recent = MarketingLead.objects.filter(
                school=school, inquiry_received_at__gte=now - timedelta(days=1),
                response_consent=True, application__isnull=True,
            ).exclude(stage__in=STOPPED_STAGES).order_by("inquiry_received_at", "id")
            for lead in recent.iterator(chunk_size=100):
                if lead.applications.exists():
                    continue
                outcome = queue_inquiry_notifications(lead)
                result["events"] += int(outcome.get("new_event", False))
                result["queued"] += outcome.get("queued", 0)
                result["intake_notices_queued"] += outcome.get("queued", 0)
                if result["events"] >= budget or result["queued"] >= budget * 2:
                    return result
            leads = MarketingLead.objects.filter(
                school=school, inquiry_received_at__isnull=False,
                next_follow_up_at__lte=now, application__isnull=True,
            ).exclude(stage__in=STOPPED_STAGES).order_by("next_follow_up_at", "id")
            for lead in leads.iterator(chunk_size=100):
                outcome = queue_due_inquiry_followup(lead, now=now)
                result["checked"] += 1
                result["events"] += int(outcome["new_event"])
                result["queued"] += outcome["queued"]
                if result["events"] >= budget or result["queued"] >= budget * 2:
                    return result
    return result
