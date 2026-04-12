from __future__ import annotations

from collections import defaultdict

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id
from core.models import AcademicYear, School
from section_scheduler_wizard.models import Section, SectionSchedulerWizardSession

from course_catalog_wizard.models import Course
from staff_setup_wizard.models import StaffMember
from room_setup_wizard.models import Room
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from term_structure_wizard.models import MarkingPeriod

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


class SectionSchedulerErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class SectionSchedulerSessionResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    status = serializers.CharField()


class SectionSchedulerConfigureRequestSerializer(serializers.Serializer):
    academic_year_id = serializers.CharField()
    term_code = serializers.CharField()


class SectionSchedulerConfigureResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    academic_year_id = serializers.CharField()
    term_code = serializers.CharField()


class SectionSchedulerSectionInputSerializer(serializers.Serializer):
    section_code = serializers.CharField()
    course_code = serializers.CharField()
    teacher_email = serializers.CharField(required=False, allow_blank=True)
    room_code = serializers.CharField(required=False, allow_blank=True)
    template_code = serializers.CharField()
    block_code = serializers.CharField()


class SectionSchedulerSetSectionsRequestSerializer(serializers.Serializer):
    sections = SectionSchedulerSectionInputSerializer(many=True)


class SectionSchedulerSetSectionsResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class SectionSchedulerCommitResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    total = serializers.IntegerField()


class SectionSchedulerVerifySectionSerializer(serializers.Serializer):
    section_code = serializers.CharField()
    term_code = serializers.CharField()
    template_code = serializers.CharField()
    block_code = serializers.CharField()


class SectionSchedulerVerifyResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    sections = SectionSchedulerVerifySectionSerializer(many=True)
    count = serializers.IntegerField()


def _get_session(session_id, school_id):
    return get_object_or_404(SectionSchedulerWizardSession, id=session_id, school__id=school_id)


@extend_schema(
    operation_id="section_scheduler_create_session",
    tags=["Scheduling"],
    responses={201: SectionSchedulerSessionResponseSerializer},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    sess = SectionSchedulerWizardSession.objects.create(school=school)
    return Response({"session_id": str(sess.id), "status": sess.status}, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="section_scheduler_configure_session",
    tags=["Scheduling"],
    request=SectionSchedulerConfigureRequestSerializer,
    responses={200: SectionSchedulerConfigureResponseSerializer, 400: SectionSchedulerErrorSerializer, 404: SectionSchedulerErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "draft":
        return Response({"error": "Session not in draft state"}, status=status.HTTP_400_BAD_REQUEST)

    ay_id = request.data.get("academic_year_id")
    term_code = str(request.data.get("term_code", "")).strip().upper()
    if not ay_id:
        return Response({"error": "academic_year_id required"}, status=status.HTTP_400_BAD_REQUEST)
    if not term_code:
        return Response({"error": "term_code required"}, status=status.HTTP_400_BAD_REQUEST)

    ay = AcademicYear.objects.filter(pk=ay_id, school_id=school_id).first()
    if not ay:
        return Response({"error": "AcademicYear not found"}, status=status.HTTP_404_NOT_FOUND)

    ok = MarkingPeriod.objects.filter(
        term_structure__school__id=school_id,
        term_structure__academic_year=ay,
        code=term_code,
    ).exists()
    if not ok:
        return Response(
            {"error": f"term_code '{term_code}' not found in TermStructure for this AcademicYear"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sess.academic_year = ay
    sess.term_code = term_code
    sess.status = "configured"
    sess.save(update_fields=["academic_year", "term_code", "status"])
    return Response({"status": sess.status, "academic_year_id": str(ay.id), "term_code": term_code})


@extend_schema(
    operation_id="section_scheduler_set_sections",
    tags=["Scheduling"],
    request=SectionSchedulerSetSectionsRequestSerializer,
    responses={200: SectionSchedulerSetSectionsResponseSerializer, 400: SectionSchedulerErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_sections(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "configured":
        return Response({"error": "set_sections requires configured state"}, status=status.HTTP_400_BAD_REQUEST)

    sections = request.data.get("sections")
    if not isinstance(sections, list) or not sections:
        return Response({"error": "sections must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    normalized = []
    for i, row in enumerate(sections):
        if not isinstance(row, dict):
            return Response({"error": f"sections[{i}] must be an object"}, status=status.HTTP_400_BAD_REQUEST)
        section_code = str(row.get("section_code", "")).strip().upper()
        course_code = str(row.get("course_code", "")).strip().upper()
        template_code = str(row.get("template_code", "")).strip().upper()
        block_code = str(row.get("block_code", "")).strip().upper()
        if not section_code or not course_code or not template_code or not block_code:
            return Response(
                {"error": f"sections[{i}] requires section_code, course_code, template_code, block_code"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        normalized.append({
            "section_code": section_code,
            "course_code": course_code,
            "teacher_email": str(row.get("teacher_email", "")).strip().lower(),
            "room_code": str(row.get("room_code", "")).strip().upper(),
            "template_code": template_code,
            "block_code": block_code,
        })

    # Validate bell schedule blocks for this AY
    ay = sess.academic_year
    sched = BellSchedule.objects.filter(school__id=school_id, academic_year=ay, is_active=True).first()
    if not sched:
        return Response({"error": "No active BellSchedule for this AcademicYear"}, status=status.HTTP_400_BAD_REQUEST)

    tpl_blocks: dict[str, set] = defaultdict(set)
    for tpl in DayTemplate.objects.filter(schedule=sched):
        for b in PeriodBlock.objects.filter(template=tpl):
            tpl_blocks[tpl.template_code].add(b.code)

    for row in normalized:
        if row["template_code"] not in tpl_blocks:
            return Response({"error": f"Unknown template_code: {row['template_code']}"}, status=status.HTTP_400_BAD_REQUEST)
        if row["block_code"] not in tpl_blocks[row["template_code"]]:
            return Response(
                {"error": f"Unknown block_code '{row['block_code']}' for template '{row['template_code']}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    sess.sections = normalized
    sess.status = "sections_set"
    sess.save(update_fields=["sections", "status"])
    return Response({"status": sess.status, "count": len(normalized)})


@extend_schema(
    operation_id="section_scheduler_commit_session",
    tags=["Scheduling"],
    responses={200: SectionSchedulerCommitResponseSerializer, 400: SectionSchedulerErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "sections_set":
        return Response({"error": "Commit requires sections_set state"}, status=status.HTTP_400_BAD_REQUEST)

    ay = sess.academic_year

    # Collision checks
    teacher_slot: set = set()
    room_slot: set = set()

    # Pre-resolve foreign keys
    course_by_code = {c.code: c for c in Course.objects.filter(school__id=school_id)}
    staff_by_email = {s.email: s for s in StaffMember.objects.filter(school__id=school_id, is_active=True)}
    room_by_code = {r.code: r for r in Room.objects.filter(school__id=school_id, is_active=True)}

    for row in sess.sections or []:
        te = row.get("teacher_email") or ""
        if te:
            key = (te, row["template_code"], row["block_code"])
            if key in teacher_slot:
                return Response(
                    {"error": f"Teacher collision: {te} at {row['template_code']}:{row['block_code']}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            teacher_slot.add(key)
        rc = row.get("room_code") or ""
        if rc:
            key = (rc, row["template_code"], row["block_code"])
            if key in room_slot:
                return Response(
                    {"error": f"Room collision: {rc} at {row['template_code']}:{row['block_code']}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            room_slot.add(key)

    created = 0
    updated = 0

    with transaction.atomic():
        # Lock AY row for this operation
        list(AcademicYear.objects.select_for_update().filter(id=ay.id))

        keep_codes = []
        for row in sess.sections or []:
            keep_codes.append(row["section_code"])
            course = course_by_code.get(row["course_code"])
            if not course:
                return Response({"error": f"Unknown course_code: {row['course_code']}"}, status=status.HTTP_400_BAD_REQUEST)

            teacher = staff_by_email.get(row.get("teacher_email") or "")
            room = room_by_code.get(row.get("room_code") or "")

            _, was_created = Section.objects.update_or_create(
                school_id=sess.school_id,
                academic_year=ay,
                section_code=row["section_code"],
                defaults={
                    "course": course,
                    "term_code": sess.term_code,
                    "teacher": teacher,
                    "room": room,
                    "template_code": row["template_code"],
                    "block_code": row["block_code"],
                    "is_active": True,
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        # Delete stale sections scoped to this term only
        Section.objects.filter(
            school_id=sess.school_id,
            academic_year=ay,
            term_code=sess.term_code,
        ).exclude(section_code__in=keep_codes).delete()

        sess.commit_result = {"created": created, "updated": updated, "total": len(keep_codes)}
        sess.status = "committed"
        sess.save(update_fields=["commit_result", "status"])

    return Response({"status": sess.status, **sess.commit_result})


@extend_schema(
    operation_id="section_scheduler_verify_session",
    tags=["Scheduling"],
    responses={200: SectionSchedulerVerifyResponseSerializer, 400: SectionSchedulerErrorSerializer},
)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status not in ("committed", "verified"):
        return Response({"error": "Verify requires committed state"}, status=status.HTTP_400_BAD_REQUEST)

    ay = sess.academic_year
    sections = list(
        Section.objects.filter(school_id=sess.school_id, academic_year=ay, term_code=sess.term_code)
        .values("section_code", "term_code", "template_code", "block_code")
        .order_by("section_code")
    )
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "sections": sections, "count": len(sections)})
