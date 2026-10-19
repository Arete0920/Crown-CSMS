"""School-scoped prospect capture and capability-based application continuity."""
from __future__ import annotations

import json
import re
import uuid
from datetime import timedelta

from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from core.models import RolePermission, UserAccount
from .models import CampaignTouchpoint, LeadStage, MarketingCampaign, MarketingLead


TOKEN_SALT = "crm_marketing.inquiry.continuation.v1"
TOKEN_MAX_AGE = 30 * 24 * 60 * 60
UTM_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "landing_page", "referrer"}


def bounded_text(payload, key, limit, *, required=False):
    value = payload.get(key, "")
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f"{key} must be text no longer than {limit} characters.")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{key} contains unsupported Unicode characters.") from exc
    value = value.strip()
    if required and not value:
        raise ValueError(f"{key} is required.")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{key} contains unsupported control characters.")
    return value


def normalize_inquiry(payload, school):
    values = {
        key: bounded_text(payload, key, limit, required=required)
        for key, limit, required in (
            ("parent_name", 160, True), ("email", 254, True),
            ("phone", 32, False), ("grade_interest", 16, True),
            ("entry_year", 32, True), ("campus", 120, False),
            ("source", 80, False), ("referral_type", 40, False),
            ("referral_detail", 180, False),
        )
    }
    values["campus"] = values["campus"] or school.name[:120]
    values["email"] = values["email"].lower()
    try:
        validate_email(values["email"])
    except ValidationError as exc:
        raise ValueError("A valid email address is required.") from exc
    for key, default, choices in (
        ("request_type", "info", {"info", "tour", "open_house"}),
        ("contact_preference", "email", {"email", "phone", "sms"}),
    ):
        value = payload.get(key, default)
        if not isinstance(value, str) or value not in choices:
            raise ValueError(f"Invalid {key}.")
        values[key] = value
    if values["contact_preference"] != "email" and not values["phone"]:
        raise ValueError("phone is required for the selected contact preference.")
    if values["contact_preference"] == "sms" and not re.fullmatch(r"\+[1-9]\d{6,14}", values["phone"]):
        raise ValueError("For SMS, use a country code and digits, for example +13025550100.")
    if payload.get("response_consent") is not True:
        raise ValueError("Permission to respond to this inquiry is required.")
    if not isinstance(payload.get("follow_up_consent", False), bool):
        raise ValueError("follow_up_consent must be a boolean.")
    values["response_consent"] = True
    values["follow_up_consent"] = payload.get("follow_up_consent", False)
    attribution = payload.get("utm", {})
    if not isinstance(attribution, dict) or set(attribution) - UTM_KEYS:
        raise ValueError("utm must contain only supported attribution fields.")
    values["attribution_json"] = {
        key: bounded_text(attribution, key, 500) for key in attribution
    }
    campaign_id = payload.get("campaign_id")
    values["campaign_id"] = None
    if campaign_id:
        try:
            campaign_id = uuid.UUID(str(campaign_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("Invalid campaign.") from exc
        if not MarketingCampaign.objects.filter(id=campaign_id, school=school, status="active").exists():
            raise ValueError("Invalid campaign.")
        values["campaign_id"] = campaign_id
    return values


def eligible_owners(school):
    roles = RolePermission.objects.filter(permission__code="admissions.edit").values("role_code")
    return UserAccount.objects.filter(
        is_active=True, roles__school=school, roles__role_code__in=roles,
    ).distinct().order_by("id")


def _initial_owner(school):
    owners = list(eligible_owners(school))
    counts = dict(MarketingLead.objects.filter(
        school=school, assigned_to_user_id__in=[owner.id for owner in owners],
    ).exclude(stage__in=[LeadStage.LOST, LeadStage.ENROLLED]).values(
        "assigned_to_user_id",
    ).annotate(total=Count("id")).values_list("assigned_to_user_id", "total"))
    return min(owners, key=lambda owner: counts.get(owner.id, 0)).id if owners else None


def public_receipt(lead, *, replayed=False):
    token = signing.dumps({
        "school": str(lead.school_id), "lead": str(lead.id),
        "nonce": str(lead.continuation_nonce),
    }, salt=TOKEN_SALT)
    return {
        "inquiry_id": str(lead.id), "school_id": str(lead.school_id),
        "school_name": lead.school.name, "continuation_token": token,
        "expires_at": lead.continuation_expires_at.isoformat(),
        "stage": lead.stage, "replayed": replayed,
        "next_step": "Admissions will respond to your request. You may continue your application now.",
    }


@transaction.atomic
def capture_inquiry(*, school, payload, request_key):
    values = normalize_inquiry(payload, school)
    digest = salted_hmac("inquiry-payload", json.dumps(values, sort_keys=True, default=str), algorithm="sha256").hexdigest()
    key = salted_hmac("inquiry-idempotency", f"{school.id}:{request_key}", algorithm="sha256").hexdigest()
    now = timezone.now()
    source = (values.pop("source") or values["attribution_json"].get("utm_source") or "website")[:80]
    lead, created = MarketingLead.objects.get_or_create(
        intake_request_key=key,
        defaults={
            **values, "school": school, "intake_payload_digest": digest,
            "first_source": source, "primary_source": source,
            "inquiry_received_at": now, "consent_at": now,
            "continuation_nonce": uuid.uuid4(),
            "continuation_expires_at": now + timedelta(seconds=TOKEN_MAX_AGE),
            "next_follow_up_at": now + timedelta(days=1),
            "assigned_to_user_id": _initial_owner(school),
            "family_follow_up_enabled": values["follow_up_consent"],
        },
    )
    if not constant_time_compare(lead.intake_payload_digest, digest):
        raise ValueError("Idempotency-Key was already used for a different inquiry.")
    if lead.continuation_expires_at is None or lead.continuation_expires_at <= now:
        raise ValueError("This request key has expired. Start a new inquiry.")
    if created:
        CampaignTouchpoint.objects.create(
            school=school, campaign=lead.campaign, lead=lead, channel="system",
            summary="Family inquiry received", outcome=LeadStage.INQUIRY,
            occurred_at=now,
            metadata_json={"response_consent": True, "follow_up_consent": lead.follow_up_consent, "consent_version": "inquiry-v1"},
        )
        from .inquiry_notifications import queue_inquiry_notifications
        queue_inquiry_notifications(lead, event="created")
    return lead, created


def lock_inquiry(*, school_id, inquiry_id, token):
    """Call inside transaction.atomic; return no record on an invalid capability."""
    try:
        if not isinstance(token, str) or len(token) > 1024:
            return None
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
        if not isinstance(data, dict) or data.get("school") != str(school_id) or data.get("lead") != str(inquiry_id):
            return None
        inquiry_id = uuid.UUID(str(inquiry_id))
    except (signing.BadSignature, ValueError, TypeError, AttributeError):
        return None
    lead = MarketingLead.objects.select_for_update().filter(
        id=inquiry_id, school_id=school_id, inquiry_received_at__isnull=False,
        continuation_expires_at__gt=timezone.now(),
    ).first()
    if lead is None or not constant_time_compare(str(lead.continuation_nonce), str(data.get("nonce", ""))):
        return None
    return lead


def mark_application_started(lead):
    if lead.application_started_at is None:
        lead.application_started_at = timezone.now()
        if lead.application_id is None:
            lead.stage = LeadStage.APPLICATION_STARTED
        lead.save(update_fields=["application_started_at", "stage", "updated_at"])
        CampaignTouchpoint.objects.create(
            school=lead.school, campaign=lead.campaign, lead=lead, channel="system",
            summary="Family started application", outcome=LeadStage.APPLICATION_STARTED,
            occurred_at=lead.application_started_at,
        )


def link_applications(lead, applications):
    if any(app.school_id != lead.school_id for app in applications):
        raise ValueError("Application and inquiry school must match.")
    lead.application = applications[0]
    lead.stage = LeadStage.APPLICATION_SUBMITTED
    lead.save(update_fields=["application", "stage", "updated_at"])
    lead.applications.add(*applications)
    CampaignTouchpoint.objects.create(
        school=lead.school, campaign=lead.campaign, lead=lead, channel="system",
        summary="Family application submitted", outcome=LeadStage.APPLICATION_SUBMITTED,
        occurred_at=timezone.now(), metadata_json={"application_ids": [str(app.id) for app in applications]},
    )


def save_submission_receipt(lead, response):
    fields = (
        "ok", "application_id", "applicant_id", "application_ids", "applicant_ids",
        "application_count", "stage", "message", "checklist_hub", "inquiry_id",
    )
    lead.submission_receipt = {key: response[key] for key in fields if key in response}
    lead.save(update_fields=["submission_receipt", "updated_at"])
