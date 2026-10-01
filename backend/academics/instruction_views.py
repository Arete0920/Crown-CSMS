import hashlib
import json
from datetime import timedelta
from urllib.parse import urlparse
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from .experience_access import classroom_scope
from .assignment_teacher_views import _can_manage_section
from .family_views import text
from .models import Assignment, Enrollment, Lesson, LessonPlan, LessonResource, PublisherObjective, Section, MasteryRecord
from .instruction_models import ClassroomRubric, ClassroomDeadlineAdjustment, ClassroomInstructionEvent, ClassroomMasteryEvidence
from .lesson_execution_models import LessonPlanLesson
from .lesson_plan_views import _validate_lesson_ids_for_section
from .submission_workflow_views import _uuid


def date_value(value):
    try:
        day = parse_date(value)
    except (ValueError, TypeError):
        day = None
    if day is None:
        raise ValidationError('A date in YYYY-MM-DD format is required.')
    return day


def criteria_for(data):
    criteria = data.get('criteria')
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 12:
        raise ValidationError('A rubric needs 1–12 criteria.')
    seen = set()
    for c in criteria:
        if not isinstance(c, dict) or set(c) != {'name', 'description', 'levels'}:
            raise ValidationError('Each criterion needs a name, description and levels.')
        name = text(c, 'name', 120)
        if name in seen:
            raise ValidationError('Criterion names must be unique.')
        seen.add(name); text(c, 'description', 2000)
        levels = c['levels']
        if not isinstance(levels, list) or not 2 <= len(levels) <= 6 or any(not isinstance(v, str) or not v.strip() or len(v) > 2000 for v in levels):
            raise ValidationError('Each criterion needs 2–6 descriptive performance levels.')
    return criteria


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classroom_instruction(request):
    school = get_request_school_id(request, required=True)
    audience = request.query_params.get('audience', 'teacher')
    sections, students = classroom_scope(request.user, school, audience)
    if audience == 'board':
        raise PermissionDenied('Instruction details are not board reports.')
    if request.method == 'GET':
        lessons = Lesson.objects.filter(school_id=school, unit__school_id=school, unit__course_id__in=sections.values('course_id'))
        if audience in {'parent', 'student'}:
            planned_ids = LessonPlanLesson.objects.filter(school_id=school, lesson_plan__section__in=sections).values('lesson_id')
            lessons = lessons.filter(id__in=planned_ids)
        assignments = Assignment.objects.filter(school_id=school, section__in=sections)
        if audience in {'parent', 'student'}:
            assignments = assignments.filter(is_published=True)
        rubrics = ClassroomRubric.objects.filter(school_id=school)
        if audience in {'parent', 'student'}:
            rubrics = rubrics.filter(id__in=assignments.values('classroom_rubric_id'))
        from .classroom_progress import progress_rows
        return Response({'progress': progress_rows(school, sections, students), 'mastery_history': list(ClassroomMasteryEvidence.objects.filter(school_id=school, record__student__in=students, assignment__section__in=sections).values('record__student_id', 'record__objective_id', 'level', 'note', 'created_at')[:200]), 'source': 'live', 'lessons': list(lessons.values('id', 'title', 'unit__course_id')[:200]),
           'objectives': list(PublisherObjective.objects.filter(school_id=school, lesson__in=lessons).values('id', 'lesson_id', 'objective_code', 'description')[:200]),
           'plans': list(LessonPlan.objects.filter(school_id=school, section__in=sections).values('id', 'section_id', 'plan_date', 'objectives')[:200]),
           'rubrics': list(rubrics.values('id', 'title', 'criteria')[:100]),
           'adjustments': list(ClassroomDeadlineAdjustment.objects.filter(school_id=school, assignment__in=assignments, student__in=students).values('assignment_id', 'student_id', 'due_date', 'instructions', 'version')[:200]),
           'resources': list(LessonResource.objects.filter(school_id=school, lesson__in=lessons).values('id', 'lesson_id', 'title', 'url', 'accessible_description', 'alternative_instructions')[:200]),
           'limits': {'lessons': 200, 'objectives': 200, 'plans': 200, 'rubrics': 100, 'adjustments': 200, 'resources': 200}})
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
    if not _can_manage_section(request.user, school, section):
        raise PermissionDenied('Active assigned teacher profile or explicit school leadership required.')
    operation = data.get('operation')
    if operation not in {'rubric', 'attach_rubric', 'curriculum', 'copy_plan', 'deadline', 'resource', 'mastery'}:
        raise ValidationError('Invalid instruction operation.')
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        Section.objects.select_for_update().get(id=section.id)
        previous = ClassroomInstructionEvent.objects.filter(school_id=school, actor=request.user, request_key=key).first()
        if previous:
            return Response(previous.result) if previous.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
        if operation == 'rubric':
            rubric = ClassroomRubric.objects.create(school_id=school, title=text(data, 'title', 160), criteria=criteria_for(data), created_by=request.user)
            result = {'saved': True, 'rubric_id': rubric.id}
        elif operation == 'attach_rubric':
            assignment = get_object_or_404(Assignment.objects.select_for_update(), id=_uuid(data.get('assignment_id'), 'assignment_id'), school_id=school, section=section)
            if assignment.submissions.exists():
                return Response({'detail': 'Work evidence exists; create a new assignment to change its rubric.'}, status=409)
            rubric = get_object_or_404(ClassroomRubric, id=_uuid(data.get('rubric_id'), 'rubric_id'), school_id=school)
            assignment.classroom_rubric = rubric; assignment.save()
            result = {'saved': True, 'assignment_id': assignment.id, 'rubric_id': rubric.id}
        elif operation == 'curriculum':
            assignment = get_object_or_404(Assignment.objects.select_for_update(), id=_uuid(data.get('assignment_id'), 'assignment_id'), school_id=school, section=section)
            objective = get_object_or_404(PublisherObjective, id=_uuid(data.get('objective_id'), 'objective_id'), school_id=school, lesson__unit__course=section.course, lesson__school_id=school, lesson__unit__school_id=school)
            assignment.lesson = objective.lesson; assignment.objective = objective; assignment.save()
            result = {'saved': True, 'assignment_id': assignment.id, 'objective_id': objective.id}
        elif operation == 'copy_plan':
            source = get_object_or_404(LessonPlan, id=_uuid(data.get('plan_id'), 'plan_id'), school_id=school, section__in=sections)
            if not _can_manage_section(request.user, school, source.section):
                raise PermissionDenied('Assigned authority required for the source plan.')
            day = date_value(data.get('plan_date'))
            if LessonPlan.objects.filter(school_id=school, section=section, plan_date=day).exists():
                return Response({'detail': 'A lesson plan already exists for this classroom and date.'}, status=409)
            _validate_lesson_ids_for_section(school_id=school, section=section, lesson_ids=source.lesson_ids)
            plan = LessonPlan.objects.create(school_id=school, section=section, plan_date=day, lesson_ids=source.lesson_ids,
                   created_by=request.user, updated_by=request.user, **{k: getattr(source, k) for k in ['objectives', 'materials', 'activities', 'homework']})
            for link in source.lesson_links.all():
                if link.lesson.school_id != school or link.lesson.unit.course_id != section.course_id:
                    raise ValidationError('Every linked lesson must belong to the target course.')
                target, _ = LessonPlanLesson.objects.get_or_create(school_id=school, lesson_plan=plan, lesson=link.lesson)
                target.sequence_order = link.sequence_order; target.planned_minutes = link.planned_minutes; target.delivery_status = 'planned'; target.save()
            result = {'saved': True, 'plan_id': plan.id}
        elif operation == 'mastery':
            assignment = get_object_or_404(Assignment, id=_uuid(data.get('assignment_id'), 'assignment_id'), school_id=school, section=section, is_published=True)
            student = get_object_or_404(students, id=_uuid(data.get('student_id'), 'student_id'))
            get_object_or_404(Enrollment.objects.select_for_update(), school_id=school, section=section, student=student)
            if not assignment.objective_id:
                raise ValidationError('Link a curriculum objective before recording mastery evidence.')
            level = data.get('level')
            if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 4:
                raise ValidationError('Mastery level must be 1–4.')
            record, _ = MasteryRecord.objects.update_or_create(school_id=school, student=student, objective=assignment.objective,
                defaults={'mastery_level': level, 'evidence_assignment': assignment})
            evidence = ClassroomMasteryEvidence.objects.create(school_id=school, record=record, assignment=assignment, actor=request.user, level=level, note=text(data, 'note'))
            result = {'saved': True, 'evidence_id': evidence.id}
        elif operation == 'deadline':
            assignment = get_object_or_404(Assignment, id=_uuid(data.get('assignment_id'), 'assignment_id'), school_id=school, section=section, is_published=True)
            student = get_object_or_404(students, id=_uuid(data.get('student_id'), 'student_id'))
            get_object_or_404(Enrollment.objects.select_for_update(), school_id=school, section=section, student=student)
            day = date_value(data.get('due_date'))
            if day < timezone.localdate() or day > timezone.localdate() + timedelta(days=365):
                raise ValidationError('Choose a deadline within the coming year.')
            adjustment = ClassroomDeadlineAdjustment.objects.filter(school_id=school, assignment=assignment, student=student).first()
            expected = data.get('version')
            if isinstance(expected, bool) or not isinstance(expected, int) or expected != (adjustment.version if adjustment else 0):
                return Response({'detail': 'Deadline changed; refresh before saving.'}, status=409)
            defaults = {'due_date': day, 'instructions': text(data, 'instructions'), 'reason_private': text(data, 'reason_private'), 'updated_by': request.user, 'version': (adjustment.version + 1) if adjustment else 1}
            adjustment, _ = ClassroomDeadlineAdjustment.objects.update_or_create(school_id=school, assignment=assignment, student=student, defaults=defaults)
            result = {'saved': True, 'version': adjustment.version, 'due_date': day}
        else:
            lesson = get_object_or_404(Lesson, id=_uuid(data.get('lesson_id'), 'lesson_id'), school_id=school, unit__course=section.course, unit__school_id=school)
            url = data.get('url')
            if not isinstance(url, str) or len(url) > 200 or urlparse(url).scheme != 'https' or not urlparse(url).netloc:
                raise ValidationError('Resources require a valid HTTPS URL of at most 200 characters.')
            resource = LessonResource.objects.create(school_id=school, lesson=lesson, title=text(data, 'title', 255), url=url,
                  accessible_description=text(data, 'accessible_description'), alternative_instructions=text(data, 'alternative_instructions'))
            result = {'saved': True, 'resource_id': resource.id}
        result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
        ClassroomInstructionEvent.objects.create(school_id=school, section=section, actor=request.user, request_key=key, fingerprint=fingerprint, operation=operation, payload=data, result=result)
        return Response(result)
