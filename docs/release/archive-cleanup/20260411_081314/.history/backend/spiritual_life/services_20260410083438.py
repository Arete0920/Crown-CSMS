from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Sum
from django.utils import timezone

try:
    from onboarding.models_tasks import HelpArticle
except Exception:  # pragma: no cover - optional on some branches
    HelpArticle = None

from portrait.services import build_portrait_record_summary
from servicehours.models import ServiceEntry
from spiritual_life import models as spiritual_models

ChapelAttendance = spiritual_models.ChapelAttendance
ChapelEvent = spiritual_models.ChapelEvent
PastoralNote = spiritual_models.PastoralNote
PrayerRequest = spiritual_models.PrayerRequest
SmallGroup = spiritual_models.SmallGroup
SmallGroupMember = spiritual_models.SmallGroupMember
SpiritualAssessment = spiritual_models.SpiritualAssessment
StudentSpiritualProfile = spiritual_models.StudentSpiritualProfile
BiblicalIntegrationRecord = getattr(spiritual_models, "BiblicalIntegrationRecord", None)
DevotionalContent = getattr(spiritual_models, "DevotionalContent", None)
SpiritualDomainRating = getattr(spiritual_models, "SpiritualDomainRating", None)

LEADERSHIP_TRACK_LIBRARY = [
    "Chapel Leadership",
    "Student Council / Government",
    "Worship Team / Music Ministry",
    "Athletics Captains",
    "Service & Outreach Coordinators",
    "Peer Tutoring / Mentorship",
    "Event Planning Team",
]
LEADERSHIP_KEYWORDS = (
    "leadership",
    "chapel",
    "worship",
    "student council",
    "government",
    "mentor",
    "mentoring",
    "tutor",
    "tutoring",
    "outreach",
    "event",
    "captain",
    "peer",
)
LEADERSHIP_SOLOMON_ARTICLES = (
    {
        "slug": "servant-leadership-foundations",
        "title": "Servant Leadership Foundations",
        "summary": "A biblical framework for developing student leaders with humility and courage.",
        "content": (
            "Student leadership in Crown2026 is framed as servant leadership — developing Christ-like character through responsibility, initiative, and service.\n\n"
            "Key scriptures: Mark 10:45, Philippians 2:3–8, and 1 Timothy 4:12.\n"
            "Leadership should emphasize character over position, service over status, and accountability under mentorship."
        ),
    },
    {
        "slug": "student-leadership-reflection-prompts",
        "title": "Student Leadership Reflection Prompts",
        "summary": "Monthly questions for helping student leaders reflect on service, humility, and faithfulness.",
        "content": (
            "Suggested prompts for advisors and students:\n"
            "- What does servant leadership look like in this role?\n"
            "- How did you put others first this month?\n"
            "- Where is God growing your humility, courage, or faithfulness through service?\n"
            "- How can your leadership strengthen worship, outreach, and school culture?"
        ),
    },
)


def _to_float(value, digits: int = 2):
    if value is None:
        return 0.0
    return round(float(value), digits)


def _ensure_student_leadership_articles() -> list[str]:
    if HelpArticle is None:
        return [item["slug"] for item in LEADERSHIP_SOLOMON_ARTICLES]

    slugs: list[str] = []
    for article_data in LEADERSHIP_SOLOMON_ARTICLES:
        article, _ = HelpArticle.objects.update_or_create(
            slug=article_data["slug"],
            defaults={
                "title": article_data["title"],
                "summary": article_data["summary"],
                "content": article_data["content"],
                "module": "spiritual_life",
                "article_type": HelpArticle.TYPE_GUIDE,
                "visibility": HelpArticle.VISIBILITY_STAFF,
                "state": HelpArticle.STATE_PUBLISHED,
                "published": True,
            },
        )
        slugs.append(article.slug)
    return slugs


def _is_leadership_entry(entry) -> bool:
    haystack = " ".join(
        [
            str(getattr(entry, "category", "") or ""),
            str(getattr(entry, "organization", "") or ""),
            str(getattr(entry, "notes", "") or ""),
        ]
    ).lower()
    return any(keyword in haystack for keyword in LEADERSHIP_KEYWORDS)


def _build_student_leadership_summary(*, service_qs, avg_chapel_attendance_pct) -> dict:
    leadership_hours = 0.0
    pending_hours = 0.0
    student_totals: dict[str, float] = {}

    for entry in service_qs:
        if not _is_leadership_entry(entry):
            continue
        hours = _to_float(getattr(entry, "hours", 0))
        student_name = (
            f"{getattr(entry.student, 'first_name', '')} {getattr(entry.student, 'last_name', '')}".strip()
            if getattr(entry, "student", None) is not None
            else "Unknown Student"
        )
        if str(getattr(entry, "status", "")).lower() in {"approved", "teacher_approved"}:
            leadership_hours += hours
            student_totals[student_name] = round(student_totals.get(student_name, 0.0) + hours, 2)
        elif str(getattr(entry, "status", "")).lower() == "pending":
            pending_hours += hours

    participant_count = len(student_totals)
    readiness_pct = round(
        min(
            100.0,
            (float(avg_chapel_attendance_pct or 0) * 0.45)
            + min(leadership_hours * 6, 35)
            + min(participant_count * 5, 20),
        ),
        1,
    )
    if readiness_pct >= 85:
        readiness_label = "Strong"
    elif readiness_pct >= 65:
        readiness_label = "Building"
    else:
        readiness_label = "Emerging"

    top_students = [
        {"student_name": name, "hours": hours}
        for name, hours in sorted(student_totals.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]

    return {
        "tracks": LEADERSHIP_TRACK_LIBRARY,
        "participation_count": participant_count,
        "approved_hours": round(leadership_hours, 2),
        "pending_hours": round(pending_hours, 2),
        "leadership_readiness_pct": readiness_pct,
        "leadership_readiness_label": readiness_label,
        "top_students": top_students,
        "solomon_article_slugs": _ensure_student_leadership_articles(),
        "reflection_prompt": "What does servant leadership look like in this role, and how did you put others first this month?",
        "program_note": "Leadership service can reinforce discipleship, service hours, and optional work-study or aid partnership plans.",
    }


def build_spiritual_life_dashboard(school):
    if not hasattr(school, "id"):
        from core.models import School

        school = School.objects.get(pk=school)

    today = timezone.localdate()

    assessment_rows = list(
        SpiritualAssessment.objects.filter(
            school=school,
            score__isnull=False,
            max_score__isnull=False,
            max_score__gt=0,
        ).values_list("score", "max_score")
    )
    assessment_average_pct = None
    if assessment_rows:
        assessment_average_pct = round(
            sum((float(score) / float(max_score)) * 100 for score, max_score in assessment_rows)
            / len(assessment_rows),
            1,
        )

    total_attendance = ChapelAttendance.objects.filter(school=school).count()
    present_attendance = ChapelAttendance.objects.filter(
        school=school, status__in=["present", "late"]
    ).count()
    avg_chapel_attendance_pct = (
        round((present_attendance / total_attendance) * 100, 1) if total_attendance else None
    )

    service_qs = ServiceEntry.objects.filter(school=school).select_related("student")
    approved_hours = service_qs.filter(status="approved").aggregate(total=Sum("hours"))["total"] or 0
    pending_hours = service_qs.filter(status__in=["pending", "teacher_approved"]).aggregate(total=Sum("hours"))["total"] or 0

    student_leadership = _build_student_leadership_summary(
        service_qs=service_qs.select_related("student"),
        avg_chapel_attendance_pct=avg_chapel_attendance_pct,
    )

    queue_items = []
    for entry in service_qs.filter(status__in=["pending", "teacher_approved"]).order_by("-created_at")[:8]:
        queue_items.append(
            {
                "id": str(entry.id),
                "student_name": f"{getattr(entry.student, 'first_name', '')} {getattr(entry.student, 'last_name', '')}".strip(),
                "hours": _to_float(entry.hours),
                "category": entry.category,
                "organization": entry.organization,
                "date": entry.date.isoformat() if entry.date else None,
                "status": entry.status,
            }
        )

    recent_devotionals = []
    if DevotionalContent is not None:
        recent_devotionals = list(
            DevotionalContent.objects.filter(school=school, is_published=True)
            .order_by("-week_number", "audience")
            .values(
                "id",
                "week_number",
                "audience",
                "title",
                "scripture_reference",
                "summary",
                "reflection_question",
                "prayer_focus",
            )[:6]
        )

    upcoming_chapel = list(
        ChapelEvent.objects.filter(school=school, event_date__gte=today)
        .order_by("event_date", "start_time")
        .values("id", "title", "event_date", "speaker", "location", "theme")[:5]
    )

    recent_integrations = []
    if BiblicalIntegrationRecord is not None:
        recent_integrations = list(
            BiblicalIntegrationRecord.objects.filter(school=school)
            .order_by("-integration_date", "-created_at")
            .values(
                "id",
                "student_id",
                "grade_label",
                "subject",
                "integration_date",
                "scripture_reference",
                "summary",
            )[:6]
        )

    audience_breakdown = {}
    if DevotionalContent is not None:
        for key, _label in DevotionalContent.AUDIENCE_CHOICES:
            audience_breakdown[key] = DevotionalContent.objects.filter(
                school=school, audience=key, is_published=True
            ).count()

    avg_domain_rating = None
    if SpiritualDomainRating is not None:
        avg_domain_rating = SpiritualDomainRating.objects.filter(school=school).aggregate(avg=Avg("rating"))["avg"]
    active_small_groups = SmallGroup.objects.filter(school=school, is_active=True).count()
    small_group_members = SmallGroupMember.objects.filter(school=school, group__is_active=True).count()
    pastoral_note_count = PastoralNote.objects.filter(school=school).count()
    open_private_prayer_requests = PrayerRequest.objects.filter(
        school=school,
        status="open",
        visibility="private",
    ).count()
    recent_prayer_requests = list(
        PrayerRequest.objects.filter(school=school)
        .order_by("-updated_at", "-created_at")
        .values("id", "title", "visibility", "status", "created_at", "updated_at")[:6]
    )
    recent_pastoral_notes = list(
        PastoralNote.objects.filter(school=school)
        .order_by("-note_date", "-created_at")
        .values("id", "student_id", "note_date", "is_sensitive", "body")[:5]
    )

    care_alerts = []
    if open_private_prayer_requests:
        care_alerts.append(
            {
                "title": f"{open_private_prayer_requests} private prayer requests need pastoral follow-up",
                "level": "High",
                "secondary": "Restricted prayer requests remain open in the chaplain queue.",
            }
        )
    if pastoral_note_count and PastoralNote.objects.filter(
        school=school,
        note_date__lte=today - timedelta(days=7),
    ).exists():
        care_alerts.append(
            {
                "title": "Pastoral follow-up notes are aging beyond 7 days",
                "level": "Medium",
                "secondary": "Review counseling and discipleship notes for next-step closure.",
            }
        )
    if active_small_groups == 0:
        care_alerts.append(
            {
                "title": "No active small groups are configured",
                "level": "Medium",
                "secondary": "Launch or re-activate discipleship cohorts for spiritual formation coverage.",
            }
        )
    if not care_alerts:
        care_alerts.append(
            {
                "title": "No high-risk spiritual care alerts are currently flagged",
                "level": "Low",
                "secondary": "Prayer, chapel, and discipleship workflows look stable right now.",
            }
        )

    care_queue = [
        {
            "id": f"prayer-{item['id']}",
            "label": item["title"],
            "secondary": f"{item['visibility']} • {item['status']}",
            "type": "prayer_request",
        }
        for item in recent_prayer_requests[:4]
    ]
    care_queue.extend(
        [
            {
                "id": f"chapel-{item['id']}",
                "label": item["title"],
                "secondary": f"{item['event_date']} • {item.get('speaker') or 'Speaker TBD'}",
                "type": "chapel_event",
            }
            for item in upcoming_chapel[:3]
        ]
    )

    return {
        "profile_count": StudentSpiritualProfile.objects.filter(school=school).count(),
        "assessment_count": SpiritualAssessment.objects.filter(school=school).count(),
        "assessment_average_pct": assessment_average_pct,
        "open_prayer_requests": PrayerRequest.objects.filter(school=school, status="open").count(),
        "open_private_prayer_requests": open_private_prayer_requests,
        "chapel_event_count": ChapelEvent.objects.filter(school=school).count(),
        "avg_chapel_attendance_pct": avg_chapel_attendance_pct,
        "approved_service_hours": _to_float(approved_hours),
        "pending_service_hours": _to_float(pending_hours),
        "teacher_review_queue": service_qs.filter(status="pending").count(),
        "sld_review_queue": service_qs.filter(status="teacher_approved").count(),
        "integration_count": BiblicalIntegrationRecord.objects.filter(school=school).count() if BiblicalIntegrationRecord is not None else 0,
        "domain_rating_count": SpiritualDomainRating.objects.filter(school=school).count() if SpiritualDomainRating is not None else 0,
        "avg_domain_rating": round(float(avg_domain_rating), 2) if avg_domain_rating is not None else None,
        "active_small_groups": active_small_groups,
        "small_group_members": small_group_members,
        "pastoral_note_count": pastoral_note_count,
        "recent_devotionals": recent_devotionals,
        "upcoming_chapel": upcoming_chapel,
        "recent_integrations": recent_integrations,
        "recent_prayer_requests": recent_prayer_requests,
        "recent_pastoral_notes": recent_pastoral_notes,
        "care_alerts": care_alerts,
        "care_queue": care_queue,
        "audience_breakdown": audience_breakdown,
        "approval_queue": queue_items,
        "student_leadership": student_leadership,
        "source": "live_db",
    }


def build_mission_metrics_dashboard(school):
    if not hasattr(school, "id"):
        from core.models import School

        school = School.objects.get(pk=school)

    spiritual = build_spiritual_life_dashboard(school)
    portrait = build_portrait_record_summary(school, limit=8)

    approved_hours = float(spiritual.get("approved_service_hours") or 0)
    pending_hours = float(spiritual.get("pending_service_hours") or 0)
    service_total = approved_hours + pending_hours
    service_approval_rate = round((approved_hours / service_total) * 100, 1) if service_total else 0.0

    chapel_pct = float(spiritual.get("avg_chapel_attendance_pct") or 0)
    portrait_avg = float(portrait.get("average_composite_percentage") or 0)
    domain_avg = spiritual.get("avg_domain_rating")
    domain_pct = round((float(domain_avg) / 5) * 100, 1) if domain_avg is not None else 0.0
    readiness_inputs = [value for value in [chapel_pct, portrait_avg, service_approval_rate, domain_pct] if value > 0]
    mission_readiness_pct = round(sum(readiness_inputs) / len(readiness_inputs), 1) if readiness_inputs else 0.0

    partner_organization_count = (
        ServiceEntry.objects.filter(school=school)
        .exclude(organization="")
        .values("organization")
        .distinct()
        .count()
    )

    merged_alerts = list(spiritual.get("care_alerts") or [])
    for item in portrait.get("alerts") or []:
        if len(merged_alerts) >= 6:
            break
        merged_alerts.append(item)

    return {
        "approved_service_hours": approved_hours,
        "pending_service_hours": pending_hours,
        "service_approval_rate": service_approval_rate,
        "portrait_completion_pct": portrait.get("completion_pct", 0),
        "portrait_average_pct": portrait.get("average_composite_percentage"),
        "faith_gate_count": portrait.get("faith_gate_count", 0),
        "chapel_attendance_pct": chapel_pct,
        "assessment_average_pct": spiritual.get("assessment_average_pct"),
        "avg_domain_rating": domain_avg,
        "mission_readiness_pct": mission_readiness_pct,
        "teacher_review_queue": spiritual.get("teacher_review_queue", 0),
        "sld_review_queue": spiritual.get("sld_review_queue", 0),
        "open_prayer_requests": spiritual.get("open_prayer_requests", 0),
        "open_private_prayer_requests": spiritual.get("open_private_prayer_requests", 0),
        "active_small_groups": spiritual.get("active_small_groups", 0),
        "partner_organization_count": partner_organization_count,
        "approval_queue": spiritual.get("approval_queue", []),
        "portrait_review_queue": portrait.get("review_queue", []),
        "recent_portrait_records": portrait.get("recent_records", []),
        "top_portrait_domains": portrait.get("top_domains", []),
        "recent_integrations": spiritual.get("recent_integrations", []),
        "recent_devotionals": spiritual.get("recent_devotionals", []),
        "alerts": merged_alerts,
        "source": "live_db",
    }
