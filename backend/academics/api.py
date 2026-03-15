from __future__ import annotations

import json
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.scoping import get_request_school_id
from households.models import Student
from .models import Course, Section, Enrollment


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
        return None


def _course_to_dict(c: Course):
    return {
        "id": str(c.id),
        "school_id": str(c.school_id),
        "code": c.code,
        "name": c.name,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _section_to_dict(s: Section):
    return {
        "id": str(s.id),
        "school_id": str(s.school_id),
        "course_id": str(s.course_id),
        "term": s.term,
        "teacher_name": s.teacher_name,
        "grade_band": s.grade_band,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _student_to_dict(st: Student):
    # keep minimal; full student serializer later
    return {
        "id": str(st.id),
        "first_name": getattr(st, "first_name", ""),
        "last_name": getattr(st, "last_name", ""),
        "grade_level": getattr(st, "grade_level", ""),
        "household_id": str(getattr(st, "household_id", "")) if getattr(st, "household_id", None) else None,
    }


@login_required
@require_http_methods(["GET", "POST"])
def courses(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = Course.objects.filter(school_id=sid).order_by("code")
        return _envelope([_course_to_dict(c) for c in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    code = (payload.get("code") or "").strip()
    name = (payload.get("name") or "").strip()

    if not code:
        return _json_error("code is required", status=400)
    if not name:
        return _json_error("name is required", status=400)

    c = Course.objects.create(school_id=sid, code=code[:32], name=name[:160])
    return _envelope(_course_to_dict(c), status=201)


@login_required
@require_http_methods(["GET", "POST"])
def sections(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = Section.objects.select_related("course").filter(school_id=sid).order_by("term", "course__code")
        return _envelope([_section_to_dict(s) for s in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    course_id = payload.get("course_id")
    term = (payload.get("term") or "").strip()

    if not course_id:
        return _json_error("course_id is required", status=400)
    if not term:
        return _json_error("term is required", status=400)

    try:
        course = Course.objects.get(pk=UUID(str(course_id)), school_id=sid)
    except Course.DoesNotExist:
        return _json_error("Not found", status=404)

    s = Section.objects.create(
        school_id=sid,
        course=course,
        term=term[:24],
        teacher_name=(payload.get("teacher_name") or "")[:120],
        grade_band=(payload.get("grade_band") or "")[:32],
    )
    return _envelope(_section_to_dict(s), status=201)


@login_required
@require_http_methods(["POST"])
def enroll(request: HttpRequest):
    """
    Body: { "section_id": "<uuid>", "student_id": "<uuid>" }
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    section_id = payload.get("section_id")
    student_id = payload.get("student_id")

    if not section_id:
        return _json_error("section_id is required", status=400)
    if not student_id:
        return _json_error("student_id is required", status=400)

    try:
        section = Section.objects.get(pk=UUID(str(section_id)), school_id=sid)
    except Section.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        student = Student.objects.get(pk=UUID(str(student_id)), school_id=sid)
    except Student.DoesNotExist:
        return _json_error("Not found", status=404)

    e, _created = Enrollment.objects.get_or_create(
        school_id=sid,
        section=section,
        student=student,
    )
    return _envelope({"enrollment_id": str(e.id)}, status=201)


@login_required
@require_http_methods(["GET"])
def section_roster(request: HttpRequest, section_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        section = Section.objects.get(pk=UUID(section_id), school_id=sid)
    except Section.DoesNotExist:
        return _json_error("Not found", status=404)

    enrollments = Enrollment.objects.select_related("student").filter(section=section, school_id=sid)
    students = [_student_to_dict(e.student) for e in enrollments]
    return _envelope({"section_id": str(section.id), "students": students}, status=200)
