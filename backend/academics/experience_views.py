"""Current classroom records, with explicit reporting windows and provenance."""
from datetime import timedelta
from uuid import UUID
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from gradebook.models import GradeEntry
from .experience_access import classroom_scope
from .grade_evidence import resolve_grade
from .instruction_models import ClassroomDeadlineAdjustment
from .models import Assignment, AssignmentCategory, Enrollment, LessonPlan, Submission, Grade


def reporting_window(request):
    today = timezone.localdate()
    try:
        start = parse_date(request.query_params.get("from", today.isoformat()))
        end = parse_date(request.query_params.get("to", (today + timedelta(days=14)).isoformat()))
    except ValueError:
        raise ValidationError("Invalid reporting date.")
    if start is None or end is None or end < start or (end - start).days > 31:
        raise ValidationError("Choose a valid date window of at most 32 days.")
    return start, end


def report_sections(school_id, sections, start, end):
    """School board gets aggregate operational facts, never student/teacher names."""
    enrollments = Enrollment.objects.filter(school_id=school_id, section__in=sections,
                                            student__school_id=school_id)
    assignments = Assignment.objects.filter(school_id=school_id, section__in=sections,
                                             is_published=True, due_date__range=(start, end))
    submissions = Submission.objects.filter(school_id=school_id, assignment__in=assignments,
                                             enrollment__in=enrollments)
    return {
        "sections": sections.count(), "section_enrollments": enrollments.count(),
        "published_assignments_due": assignments.count(),
        "recorded_submissions": submissions.filter(submitted_at__isnull=False).count(),
        "lesson_plans": LessonPlan.objects.filter(school_id=school_id, section__in=sections,
                                                   plan_date__range=(start, end)).count(),
        "definitions": {"section_enrollments": "One student in one section; not unique student count.",
                        "recorded_submissions": "Submission timestamps; does not imply grading or mastery."},
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def classroom_workspace(request):
    school_id = get_request_school_id(request, required=True)
    audience = request.query_params.get("audience", "teacher")
    if audience not in {"teacher", "student", "parent", "admin", "board"}:
        raise ValidationError("Invalid classroom audience.")
    sections, students = classroom_scope(request.user, school_id, audience)
    start, end = reporting_window(request)
    term = request.query_params.get("term", "")
    available_terms = list(sections.order_by("term").values_list("term", flat=True).distinct())
    if term:
        sections = sections.filter(term=term)
    result = {"audience": audience, "from": start, "to": end, "terms": available_terms,
              "generated_at": timezone.now(), "source": "live",
              "provenance": ["academics.Section", "academics.Enrollment", "academics.Assignment",
                             "academics.LessonPlan", "academics.Submission", "gradebook.GradeEntry"],
              "limitations": ["Sections are course rosters, not a verified daily bell schedule.",
                              "Attendance requires the verified student identity bridge.",
                              "Grades below are recorded assignment points, not weighted report-card totals."],
              "summary": report_sections(school_id, sections, start, end)}
    if audience == "board":
        return Response(result)
    section_id = request.query_params.get("section_id")
    for key in ("section_id", "student_id"):
        value = request.query_params.get(key)
        if value:
            try:
                UUID(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{key} must be a UUID.")
    if section_id:
        sections = sections.filter(id=section_id)
    enrollments = Enrollment.objects.filter(school_id=school_id, section__in=sections,
                                            student__in=students, student__school_id=school_id)
    if audience in {"parent", "student"}:
        student_id = request.query_params.get("student_id")
        if student_id:
            students = students.filter(id=student_id)
            enrollments = enrollments.filter(student__in=students)
            sections = sections.filter(id__in=enrollments.values("section_id"))
    assignments = Assignment.objects.filter(school_id=school_id, section__in=sections).select_related("category", "section__course")
    if audience in {"parent", "student"}:
        assignments = assignments.filter(is_published=True)
    assignments = assignments.filter(Q(due_date__range=(start, end)) | Q(due_date__isnull=True) | Q(deadline_adjustments__student__in=students, deadline_adjustments__due_date__range=(start, end))).distinct().order_by("due_date", "id")
    total = assignments.count()
    rows = list(assignments[:200])
    submissions = Submission.objects.filter(school_id=school_id, assignment__in=rows,
                                             enrollment__in=enrollments).select_related("enrollment")
    submission_map = {(s.assignment_id, s.enrollment.student_id): s for s in submissions}
    grades = GradeEntry.objects.filter(school_id=school_id, assignment__in=rows, student__in=students,
                                       section__in=sections)
    grade_map = {(g.assignment_id, g.student_id): g for g in grades}
    academic_grades = Grade.objects.filter(school_id=school_id, submission__assignment__in=rows,
                                           submission__enrollment__in=enrollments).select_related('submission__enrollment')
    academic_map = {(g.submission.assignment_id, g.submission.enrollment.student_id): g for g in academic_grades}
    adjustments = {(r.assignment_id, r.student_id): r for r in ClassroomDeadlineAdjustment.objects.filter(school_id=school_id, assignment__in=rows, student__in=students)}
    tasks = []
    for a in rows:
        targets = enrollments.filter(section_id=a.section_id) if audience in {"parent", "student"} else [None]
        for e in targets:
            adjustment = adjustments.get((a.id, e.student_id)) if e else None
            due = adjustment.due_date if adjustment else a.due_date
            if e and due and not start <= due <= end:
                continue
            s = submission_map.get((a.id, e.student_id)) if e else None
            g = grade_map.get((a.id, e.student_id)) if e else None
            academic = academic_map.get((a.id, e.student_id)) if e else None
            evidence = resolve_grade(a, g, academic)
            recorded_points, possible = evidence['earned'], evidence['possible']
            grade_source, conflict = evidence['source'], evidence['conflict']
            state = "draft" if not a.is_published else "submitted" if s and s.submitted_at else "assigned"
            if s and s.status in {"draft", "returned"}:
                state = s.status
            elif conflict:
                state = 'grade_conflict'
            elif recorded_points is not None:
                state = "graded"
            elif state == "submitted":
                state = "awaiting_grading"
            elif s and s.status == "missing":
                state = "missing"
            elif due and due < timezone.localdate() and state == "assigned":
                state = "overdue_unconfirmed"
            tasks.append({"id": str(a.id), "name": a.name, **{key: getattr(a, key) for key in ("purpose", "instructions", "success_criteria", "home_support")}, "section_id": str(a.section_id),
                          "course": a.section.course.name, "student_id": str(e.student_id) if e else None,
                          "due_date": due, "original_due_date": a.due_date, "makeup_instructions": adjustment.instructions if adjustment else "", "rubric": {"title": a.classroom_rubric.title, "criteria": a.classroom_rubric.criteria} if a.classroom_rubric_id else None, "published": a.is_published, "state": state,
                          "submitted_at": s.submitted_at if s else None,
                          "points_earned": recorded_points, "grade_source": grade_source,
                          "points_possible": possible, "category": a.category.name})
    plans = LessonPlan.objects.filter(school_id=school_id, section__in=sections, plan_date__range=(start, end)).order_by("plan_date", "id")
    plan_fields = ["id", "section_id", "plan_date", "objectives", "materials", "activities", "homework"]
    result.update({"sections": list(sections.order_by("course__name", "id").values("id", "course__name", "term")[:200]),
                   "students": list(students.order_by("last_name", "id").values("id", "first_name", "last_name", "grade_level")[:200]),
                   "assignments": tasks, "assignments_total": total, "truncated": total > 200 or plans.count() > 200,
                   "lesson_plans": list(plans.values(*plan_fields)[:200]),
                   "categories": list(AssignmentCategory.objects.filter(school_id=school_id, section__in=sections).values("id", "section_id", "name", "weight_percent", "is_active")),
                   "can_manage": audience in {"teacher", "admin"}})
    return Response(result)
