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
    return BellSchedule.objects.filter(
        school__id=school_id,
        academic_year=academic_year,
        is_active=True,
    ).first()


def _canonical_section_for_session(section_id, school_id, sess):
    return AcademicSection.objects.select_related("course", "term_ref").filter(
        id=section_id,
        school_id=school_id,
        term_ref__academic_year_id=sess.academic_year_id,
        term=sess.term_code,
    ).first()


def _teacher_ids(section_id, school_id):
    return set(
        TeacherAssignment.objects.filter(
            school_id=school_id,
            section_id=section_id,
        ).values_list("staff_id", flat=True)
    )


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
    if not MarkingPeriod.objects.filter(
        term_structure__school__id=school_id,
        term_structure__academic_year=ay,
        code=term_code,
    ).exists():
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
    sections = list(
        AcademicSection.objects.filter(
            school_id=school_id,
            term_ref__academic_year_id=sess.academic_year_id,
            term=sess.term_code,
        ).select_related("course").order_by("course__code", "id")
    )
    section_rows = [
        {"section_id": str(section.id), "course_code": section.course.code, "course_name": section.course.name, "grade_band": section.grade_band}
        for section in sections
    ]
    room_rows = [
        {"room_id": str(room.id), "code": room.code, "name": room.name, "capacity": room.capacity}
        for room in Room.objects.filter(school__id=school_id, is_active=True).order_by("code")
    ]
    templates = []
    for template in DayTemplate.objects.filter(schedule=schedule).order_by("ordering", "template_code"):
        blocks = [
            {"period_block_id": str(block.id), "code": block.code, "name": block.label, "start_time": str(block.start_time), "end_time": str(block.end_time)}
            for block in PeriodBlock.objects.filter(template=template).order_by("ordering", "start_time", "code")
        ]
        templates.append({"day_template_id": str(template.id), "template_code": template.template_code, "name": template.template_code, "blocks": blocks})
    return Response({"academic_year_id": str(sess.academic_year_id), "term_code": sess.term_code, "sections": section_rows, "rooms": room_rows, "day_templates": templates})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT)
def set_sections(request, session_id):
    school_id = get_request_school_id(request, required=True)
    sess = _get_session(session_id, school_id)
    if sess.status not in ("configured", "sections_set"):
        return Response({"error": "set_sections requires configured state"}, status=400)
    rows = request.data.get("sections")
    if not isinstance(rows, list) or not rows:
        return Response({"error": "sections must be a non-empty list"}, status=400)
    schedule = _active_schedule(school_id, sess.academic_year)
    if not schedule:
        return Response({"error": "No active BellSchedule for this AcademicYear"}, status=400)
    normalized = []
    seen_sections = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            return Response({"error": f"sections[{i}] must be an object"}, status=400)
        try:
            section_id = _uuid(row.get("section_id"), f"sections[{i}].section_id")
            template_id = _uuid(row.get("day_template_id"), f"sections[{i}].day_template_id")
            block_id = _uuid(row.get("period_block_id"), f"sections[{i}].period_block_id")
            room_id = _uuid(row.get("room_id"), f"sections[{i}].room_id") if row.get("room_id") else None
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        if section_id in seen_sections:
            return Response({"error": f"sections[{i}].section_id is duplicated"}, status=400)
        seen_sections.add(section_id)
        section = _canonical_section_for_session(section_id, school_id, sess)
        if not section:
            return Response({"error": f"sections[{i}].section_id is not a canonical section for this school/year/term"}, status=400)
        template = DayTemplate.objects.filter(id=template_id, schedule=schedule).first()
        if not template:
            return Response({"error": f"sections[{i}].day_template_id is invalid"}, status=400)
        block = PeriodBlock.objects.filter(id=block_id, template=template).first()
        if not block:
            return Response({"error": f"sections[{i}].period_block_id is invalid for the selected template"}, status=400)
        if room_id and not Room.objects.filter(id=room_id, school__id=school_id, is_active=True).exists():
            return Response({"error": f"sections[{i}].room_id is not an active room for this school"}, status=400)
        normalized.append({"section_id": str(section_id), "room_id": str(room_id) if room_id else None, "day_template_id": str(template_id), "period_block_id": str(block_id)})
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
    if sess.status == "committed":
        return Response({"status": sess.status, **(sess.commit_result or {})})
    if sess.status != "sections_set":
        return Response({"error": "Commit requires sections_set state"}, status=400)
    if request.data.get("confirm") is not True:
        return Response({"error": "confirm must be true"}, status=400)
    ay = sess.academic_year
    created = 0
    updated = 0
    try:
        with transaction.atomic():
            AcademicYear.objects.select_for_update().get(id=ay.id, school_id=school_id)
            staged_section_ids = {UUID(row["section_id"]) for row in (sess.sections or [])}
            existing = list(SectionPlacement.objects.filter(school_id=school_id, academic_year=ay, is_active=True).exclude(section_id__in=staged_section_ids))
            existing_room_slots = {(p.room_id, p.day_template_id, p.period_block_id) for p in existing if p.room_id}
            existing_teacher_slots = defaultdict(set)
            for placement in existing:
                existing_teacher_slots[(placement.day_template_id, placement.period_block_id)].update(_teacher_ids(placement.section_id, school_id))
            batch_room_slots = set()
            batch_teacher_slots = defaultdict(set)
            resolved = []
            for i, row in enumerate(sess.sections or []):
                section = _canonical_section_for_session(UUID(row["section_id"]), school_id, sess)
                if not section:
                    return Response({"error": f"sections[{i}] canonical section no longer valid"}, status=400)
                template = DayTemplate.objects.filter(id=row["day_template_id"], schedule__school__id=school_id, schedule__academic_year=ay, schedule__is_active=True).first()
                block = PeriodBlock.objects.filter(id=row["period_block_id"], template=template).first() if template else None
                if not template or not block:
                    return Response({"error": f"sections[{i}] bell-schedule placement no longer valid"}, status=400)
                room = None
                if row.get("room_id"):
                    room = Room.objects.filter(id=row["room_id"], school__id=school_id, is_active=True).first()
                    if not room:
                        return Response({"error": f"sections[{i}] room no longer valid"}, status=400)
                slot = (template.id, block.id)
                room_slot = (room.id if room else None, template.id, block.id)
                if room and (room_slot in existing_room_slots or room_slot in batch_room_slots):
                    return Response({"error": f"Room collision at {template.template_code}:{block.code}"}, status=400)
                if room:
                    batch_room_slots.add(room_slot)
                teachers = _teacher_ids(section.id, school_id)
                if teachers & existing_teacher_slots[slot] or teachers & batch_teacher_slots[slot]:
                    return Response({"error": f"Teacher collision at {template.template_code}:{block.code}"}, status=400)
                batch_teacher_slots[slot].update(teachers)
                resolved.append((section, room, template, block))
            for section, room, template, block in resolved:
                _, was_created = SectionPlacement.objects.update_or_create(section=section, defaults={"school_id": school_id, "academic_year": ay, "room": room, "day_template": template, "period_block": block, "is_active": True})
                created += int(was_created)
                updated += int(not was_created)
            sess.commit_result = {"created": created, "updated": updated, "total": len(resolved), "replace_semantics": False}
            sess.status = "committed"
            sess.save(update_fields=["commit_result", "status"])
    except IntegrityError:
        return Response({"error": "Schedule collision detected while publishing; no changes were committed"}, status=409)
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
    staged_ids = [row["section_id"] for row in (sess.sections or [])]
    placements = list(
        SectionPlacement.objects.filter(school_id=school_id, academic_year_id=sess.academic_year_id, section_id__in=staged_ids, is_active=True)
        .select_related("section__course", "room", "day_template", "period_block")
        .order_by("section__course__code", "section_id")
    )
    rows = [{"section_id": str(p.section_id), "course_code": p.section.course.code, "room_code": p.room.code if p.room else None, "template_code": p.day_template.template_code, "block_code": p.period_block.code} for p in placements]
    if len(rows) != len(staged_ids):
        return Response({"error": "Placement verification mismatch", "expected": len(staged_ids), "actual": len(rows)}, status=409)
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "sections": rows, "count": len(rows)})
