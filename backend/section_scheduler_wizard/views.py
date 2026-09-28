from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import Section as AcademicSection, TeacherAssignment
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import SectionPlacement, SectionSchedulerWizardSession
from term_structure_wizard.models import MarkingPeriod
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.exceptions import ValidationError
from .services import normalize, publish, undo, snapshot

_AUTH = [JWTAuthentication, SessionAuthentication]
_VIEW = [CrownModulePermission("scheduling.view")]
_CONFIGURE = [CrownModulePermission("scheduling.view", write_code="scheduling.configure")]
_EDIT = [CrownModulePermission("scheduling.view", write_code="scheduling.edit")]
_PUBLISH = [CrownModulePermission("scheduling.view", write_code="scheduling.publish")]


def _get_session(session_id, school_id):
    return get_object_or_404(SectionSchedulerWizardSession, id=session_id, school__id=school_id)


def _uuid(value, field_name):
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        raise ValueError(f"{field_name} must be a valid UUID")


def _active_schedule(school_id, academic_year):
    return BellSchedule.objects.filter(school__id=school_id, academic_year=academic_year, is_active=True).first()


def _canonical_section_for_session(section_id, school_id, sess):
    return AcademicSection.objects.select_related("course", "term_ref").filter(
        id=section_id,
        school_id=school_id,
        term_ref__academic_year_id=sess.academic_year_id,
        term=sess.term_code,
    ).first()


def _teacher_ids(section_id, school_id):
    return set(TeacherAssignment.objects.filter(school_id=school_id, section_id=section_id).values_list("staff_id", flat=True))


def _placement_key(section_id, day_template_id, period_block_id):
    return (UUID(str(section_id)), UUID(str(day_template_id)), UUID(str(period_block_id)))


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_CONFIGURE)
def create_session(request):
    school_id = get_request_school_id(request, required=True)
    school = get_object_or_404(School, id=school_id)
    sess = SectionSchedulerWizardSession.objects.create(school=school)
    return Response({"session_id": str(sess.id), "status": sess.status}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_CONFIGURE)
def configure(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status != "draft":
        return Response({"error": "Session not in draft state"}, status=400)
    ay_id = request.data.get("academic_year_id")
    term_code = str(request.data.get("term_code", "")).strip().upper()
    if not ay_id:
        return Response({"error": "academic_year_id required"}, status=400)
    if not term_code:
        return Response({"error": "term_code required"}, status=400)
    ay = AcademicYear.objects.filter(pk=ay_id, school_id=school_id).first()
    if not ay:
        return Response({"error": "AcademicYear not found"}, status=404)
    if not MarkingPeriod.objects.filter(term_structure__school__id=school_id, term_structure__academic_year=ay, code=term_code).exists():
        return Response({"error": f"term_code '{term_code}' not found in TermStructure for this AcademicYear"}, status=400)
    if not _active_schedule(school_id, ay):
        return Response({"error": "No active BellSchedule for this AcademicYear"}, status=400)
    sess.academic_year = ay
    sess.term_code = term_code
    sess.status = "configured"
    sess.save(update_fields=["academic_year", "term_code", "status"])
    return Response({"status": sess.status, "academic_year_id": str(ay.id), "term_code": term_code})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_VIEW)
def options(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status not in ("configured", "sections_set", "committed", "verified"):
        return Response({"error": "Configure the session first"}, status=400)
    schedule = _active_schedule(school_id, sess.academic_year)
    if not schedule:
        return Response({"error": "No active BellSchedule for this AcademicYear"}, status=400)
    sections = list(AcademicSection.objects.filter(school_id=school_id, term_ref__academic_year_id=sess.academic_year_id, term=sess.term_code).select_related("course").order_by("course__code", "id"))
    section_rows = [{"section_id": str(section.id), "course_code": section.course.code, "course_name": section.course.name, "grade_band": section.grade_band} for section in sections]
    room_rows = [{"room_id": str(room.id), "code": room.code, "name": room.name, "capacity": room.capacity} for room in Room.objects.filter(school__id=school_id, is_active=True).order_by("code")]
    templates = []
    for template in DayTemplate.objects.filter(schedule=schedule).order_by("ordering", "template_code"):
        blocks = [{"period_block_id": str(block.id), "code": block.code, "name": block.label, "start_time": str(block.start_time), "end_time": str(block.end_time)} for block in PeriodBlock.objects.filter(template=template).order_by("ordering", "start_time", "code")]
        templates.append({"day_template_id": str(template.id), "template_code": template.template_code, "name": template.template_code, "blocks": blocks})
    return Response({"academic_year_id": str(sess.academic_year_id), "term_code": sess.term_code, "sections": section_rows, "rooms": room_rows, "day_templates": templates, "placements": [snapshot(p) for p in SectionPlacement.objects.filter(school_id=school_id, academic_year_id=sess.academic_year_id, section__term=sess.term_code, is_active=True)]})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT)
def set_sections(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status not in ("configured", "sections_set"):
        return Response({"error": "set_sections requires configured state"}, status=400)
    with transaction.atomic():
        sess = SectionSchedulerWizardSession.objects.select_for_update().get(id=sess.id, school_id=school_id)
        if sess.status not in ("configured", "sections_set"):
            return Response({"error": "Reload the schedule before editing"}, status=409)
        normalized = normalize(request.data.get("sections"), sess)
        sess.sections = normalized
        sess.status = "sections_set"
        sess.save(update_fields=["sections", "status"])
    return Response({"status": sess.status, "count": len(normalized)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PUBLISH)
def commit(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status in ("committed", "verified"):
        return Response({"status": sess.status, **(sess.commit_result or {})})
    if sess.status != "sections_set":
        return Response({"error": "Commit requires sections_set state"}, status=400)
    if request.data.get("confirm") is not True:
        return Response({"error": "confirm must be true"}, status=400)
    try:
        with transaction.atomic():
            sess = SectionSchedulerWizardSession.objects.select_for_update().get(id=sess.id, school_id=school_id)
            if sess.status in ("committed", "verified"):
                return Response({"status": sess.status, **(sess.commit_result or {})})
            if sess.status != "sections_set":
                return Response({"error": "Reload the schedule before publishing"}, status=409)
            AcademicYear.objects.select_for_update().get(id=sess.academic_year_id, school_id=school_id)
            sess.commit_result = publish(sess)
            sess.status = "committed"
            sess.save(update_fields=["commit_result", "status"])
    except IntegrityError:
        return Response({"error": "Schedule collision detected; no changes were committed"}, status=409)
    return Response({"status": sess.status, **sess.commit_result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_VIEW)
def verify(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status not in ("committed", "verified"):
        return Response({"error": "Verify requires committed state"}, status=400)
    receipt = sess.commit_result or {}
    if receipt.get("undone"):
        return Response({"error": "This publication has been undone"}, status=409)
    if "after" in receipt:
        actual = {str(p.id): p for p in SectionPlacement.objects.filter(
            school_id=school_id, academic_year_id=sess.academic_year_id,
            id__in=[r["placement_id"] for r in receipt["after"]], is_active=True)}
        if any(r["placement_id"] not in actual or
               snapshot(actual[r["placement_id"]]) != r for r in receipt["after"]):
            return Response({"error": "The published schedule has changed"}, status=409)
        if SectionPlacement.objects.filter(school_id=school_id,
                id__in=[r["placement_id"] for r in receipt["before"]], is_active=True).exists():
            return Response({"error": "A removed meeting has been restored"}, status=409)
        sess.status = "verified"
        sess.save(update_fields=["status"])
        return Response({"status": sess.status, "count": len(actual), "placements": receipt["after"]})
    # Preserve verification for publications made before reversible receipts existed.
    expected = sess.sections or []
    actual = {(str(p.section_id), str(p.day_template_id), str(p.period_block_id)): p
              for p in SectionPlacement.objects.filter(school_id=school_id,
                  academic_year_id=sess.academic_year_id, is_active=True)}
    for row in expected:
        placement = actual.get((row["section_id"], row["day_template_id"], row["period_block_id"]))
        if placement is None or (str(placement.room_id) if placement.room_id else None) != row.get("room_id"):
            return Response({"error": "Placement verification mismatch"}, status=409)
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "count": len(expected)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PUBLISH)
def undo_publication(request, session_id):
    school_id = get_request_school_id(request, required=True)
    if request.data.get("confirm") is not True:
        return Response({"error": "confirm must be true"}, status=400)
    try:
        with transaction.atomic():
            sess = get_object_or_404(SectionSchedulerWizardSession.objects.select_for_update(),
                                    id=session_id, school_id=school_id)
            if sess.status not in ("committed", "verified"):
                return Response({"error": "Only a published schedule can be undone"}, status=409)
            AcademicYear.objects.select_for_update().get(id=sess.academic_year_id, school_id=school_id)
            sess.commit_result = undo(sess)
            sess.save(update_fields=["commit_result"])
    except IntegrityError:
        return Response({"error": "The previous schedule now conflicts; nothing was changed"}, status=409)
    return Response({"status": "undone", **sess.commit_result})
