from __future__ import annotations

from dataclasses import dataclass
from django.utils import timezone

from .models import Application, ApplicationEvent, ApplicationStatus


@dataclass(frozen=True)
class TransitionResult:
    application: Application


def submit_application(app: Application) -> TransitionResult:
    if app.status != ApplicationStatus.DRAFT:
        raise ValueError("Only DRAFT applications can be submitted.")

    app.status = ApplicationStatus.SUBMITTED
    app.submitted_at = timezone.now()
    app.save(update_fields=["status", "submitted_at", "updated_at"])

    ApplicationEvent.objects.create(
        school_id=app.school_id,
        application=app,
        event_type="APPLICATION_SUBMITTED",
        payload={},
    )

    return TransitionResult(application=app)
