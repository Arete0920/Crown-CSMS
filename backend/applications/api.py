from __future__ import annotations

import ast
import json
import logging
from decimal import Decimal
from uuid import UUID

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from households.models import Household
from households.scoping import get_request_school_id
from .models import Application, Applicant, ApplicationEvent, ApplicationStatus
from .services import submit_application
from .services import decide_application


logger = logging.getLogger(__name__)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": {"message": message}}, status=status)


def _envelope(data, status: int = 200) -> JsonResponse:
    return JsonResponse({"ok": True, "data": data}, status=status, safe=False)


def _parse_json(request: HttpRequest):
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        # Django test Client often sends a Python dict string when content_type=application/json.
        # Keep this boring and forgiving.
        try:
            return ast.literal_eval(request.body.decode("utf-8"))
        except Exception:
            return None


def _app_to_dict(app: Application):
    return {
        "id": str(app.id),
        "school_id": str(app.school_id),
        "household_id": str(app.household_id),
        "status": app.status,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "decided_at": app.decided_at.isoformat() if app.decided_at else None,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
    }


def _applicant_to_dict(a: Applicant):
    return {
        "id": str(a.id),
        "school_id": str(a.school_id),
        "application_id": str(a.application_id),
        "student_id": str(a.student_id) if a.student_id else None,
        "first_name": a.first_name,
        "last_name": a.last_name,
        "grade_applying_for": a.grade_applying_for,
        "dob": a.dob.isoformat() if a.dob else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _event_to_dict(e: ApplicationEvent):
    return {
        "id": str(e.id),
        "event_type": e.event_type,
        "payload": e.payload,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@login_required
@require_http_methods(["GET", "POST"])
def applications(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = Application.objects.filter(school_id=sid).order_by("-created_at")
        return _envelope([_app_to_dict(a) for a in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    household_id = payload.get("household_id") or payload.get("household")
    if not household_id:
        return _json_error("household_id is required", status=400)

    # no-leak: ensure the household belongs to this school
    try:
        household_uuid = UUID(str(household_id))
        Household.objects.get(pk=household_uuid, school_id=sid)
    except Household.DoesNotExist:
        return _json_error("Not found", status=404)
    except Exception:
        return _json_error("Invalid household_id", status=400)

    app = Application.objects.create(
        school_id=sid,
        household_id=household_uuid,
        status=ApplicationStatus.DRAFT,
    )

    ApplicationEvent.objects.create(
        school_id=sid,
        application=app,
        event_type="APPLICATION_CREATED",
        payload={},
    )

    return _envelope(_app_to_dict(app), status=201)


@login_required
@require_http_methods(["GET"])
def application_detail(request: HttpRequest, application_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        app = Application.objects.get(pk=UUID(application_id), school_id=sid)
    except Application.DoesNotExist:
        # no-leak: behave as not found
        return _json_error("Not found", status=404)

    data = _app_to_dict(app)

    applicants = Applicant.objects.filter(application=app, school_id=sid).order_by("last_name", "first_name")
    events = ApplicationEvent.objects.filter(application=app, school_id=sid).order_by("created_at")

    data["applicants"] = [_applicant_to_dict(a) for a in applicants]
    data["events"] = [_event_to_dict(e) for e in events]

    return _envelope(data, status=200)


@login_required
@require_http_methods(["POST"])
def application_submit(request: HttpRequest, application_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        app = Application.objects.get(pk=UUID(application_id), school_id=sid)
    except Application.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        result = submit_application(app)
    except ValueError as e:
        logger.exception("Application submit failed")
        return _json_error("Request failed.", status=400)

    return _envelope(_app_to_dict(result.application), status=200)


@login_required
@require_http_methods(["POST"])
def applicants(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    application_id = payload.get("application_id") or payload.get("application")
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")

    if not application_id:
        return _json_error("application_id is required", status=400)
    if not first_name or not last_name:
        return _json_error("first_name and last_name are required", status=400)

    # ensure the application is in-scope (no-leak)
    try:
        app = Application.objects.get(pk=UUID(str(application_id)), school_id=sid)
    except Application.DoesNotExist:
        return _json_error("Not found", status=404)

    student_id = payload.get("student_id") or payload.get("student")
    a = Applicant.objects.create(
        school_id=sid,
        application=app,
        student_id=UUID(str(student_id)) if student_id else None,
        first_name=first_name,
        last_name=last_name,
        grade_applying_for=payload.get("grade_applying_for", "") or "",
        dob=payload.get("dob") or None,
    )

    return _envelope(_applicant_to_dict(a), status=201)


@login_required
@require_http_methods(["POST"])
def application_decision(request: HttpRequest, application_id: str):
    """
    Body:
    {
      "decision": "ACCEPT" | "DENY",
      "enrollment_fee": "100.00"   # optional, ACCEPT only
    }
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    decision = payload.get("decision")
    fee = payload.get("enrollment_fee")

    try:
        app = Application.objects.get(pk=UUID(application_id), school_id=sid)
    except Application.DoesNotExist:
        return _json_error("Not found", status=404)

    fee_amt = None
    if fee is not None:
        try:
            fee_amt = Decimal(str(fee))
        except Exception:
            return _json_error("enrollment_fee must be a decimal", status=400)

    try:
        students = decide_application(
            application=app,
            decision=decision,
            enrollment_fee_amount=fee_amt,
        )
    except ValueError as e:
        logger.exception("Application decision failed")
        return _json_error("Request failed.", status=400)

    return _envelope(
        {
            "application_id": str(app.id),
            "decision": decision,
            "students_created": [str(s.id) for s in students],
        },
        status=200,
    )
