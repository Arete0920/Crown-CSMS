import hashlib
import json
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from .experience_access import classroom_scope, is_leader, taught_sections
from .collaboration_models import ClassroomEvent, ClassroomRecord, ClassroomResponse, KINDS
from .models import Assignment, Enrollment
from .assignment_teacher_views import _can_manage_section
from .submission_workflow_views import _uuid

STUDENT_KINDS = {'help_request', 'goal', 'reflection', 'portfolio'}
PRIVATE_SUPPORT = {'accommodation', 'support_plan', 'coaching'}


def context(request):
    school = get_request_school_id(request)
    audience = request.query_params.get('audience', 'student')
    sections, students = classroom_scope(request.user, school, audience)
    if audience == 'board':
        raise PermissionDenied('Individual classroom records are not board reports.')
    return school, audience, sections, students


def visible_records(request, school, audience, sections, students):
    qs = ClassroomRecord.objects.filter(school_id=school, section__in=sections)
    if audience in {'admin', 'teacher'}:
        if audience == 'teacher':
            qs = qs.exclude(Q(kind='coaching') & ~Q(owner=request.user))
        return qs.exclude(Q(visibility='private') & ~Q(created_by=request.user))
    own = Q(created_by=request.user)
    scope = own | Q(visibility='class', student__isnull=True) | Q(visibility='family', student__in=students)
    if audience == 'student':
        scope |= Q(kind='help_request', student__account_id=request.user.id)
    qs = qs.filter(scope).exclude(kind='coaching')
    student_ids = set(str(v) for v in students.values_list('id', flat=True))
    groups = [r.id for r in qs.filter(kind='group_project') if student_ids.intersection(r.metadata.get('members', []))]
    return qs.filter(~Q(kind='group_project') | Q(id__in=groups))


def serialize(record, students, manager, user):
    responses = record.responses.all() if manager else record.responses.filter(student__in=students)
    events = record.events.all() if manager else record.events.filter(Q(student__in=students) | Q(student__isnull=True))
    return {'history': list(events.values('action', 'payload', 'created_at')), 'id': record.id, 'section_id': record.section_id, 'student_id': record.student_id,
            'kind': record.kind, 'title': record.title, 'body': record.body, 'visibility': record.visibility,
            'due_at': record.due_at, 'state': record.state, 'version': record.version, 'metadata': record.metadata,
            'owner_id': record.owner_id, 'created_at': record.created_at,
            'can_close': record.kind != 'coaching' or is_leader(user, record.school_id), 'can_manage': manager, 'can_edit': manager or record.created_by_id == user.id,
            'responses': list(responses.values('id', 'student_id', 'content', 'feedback', 'state', 'version', 'updated_at'))}


def validate_metadata(payload, *, kind, section, school, student):
    metadata = payload.get('metadata', {})
    if not isinstance(metadata, dict) or len(json.dumps(metadata)) > 20000:
        raise ValidationError('Metadata must be an object of at most 20000 characters.')
    allowed = {'formative_check': {'questions'}, 'group_project': {'members', 'roles', 'milestones'},
               'portfolio': {'assignment_id'}, 'service': {'portrait_domain_id', 'worldview_priority_id', 'scripture_reference'},
               'family_service': {'portrait_domain_id', 'worldview_priority_id', 'scripture_reference'}, 'coaching': {'teacher_account_id'},
               'resource': {'reference', 'cost_cents'}, 'interruption': {'minutes'}}.get(kind, set())
    if set(metadata) - allowed:
        raise ValidationError('Unsupported metadata fields for this record kind.')
    if kind == 'formative_check':
        questions = metadata.get('questions', [])
        if not isinstance(questions, list) or not 1 <= len(questions) <= 10 or any(not isinstance(q, str) or not q.strip() or len(q) > 1000 for q in questions):
            raise ValidationError('Provide 1 to 10 brief understanding-check questions.')
    if kind == 'group_project':
        members = metadata.get('members', [])
        if not isinstance(members, list) or not 1 <= len(members) <= 30:
            raise ValidationError('A group needs 1 to 30 roster members.')
        ids = {_uuid(v, 'members') for v in members}
        count = Enrollment.objects.filter(section=section, school_id=school, student_id__in=ids, student__school_id=school).count()
        if count != len(members) or len(ids) != len(members):
            raise ValidationError('Every member must be unique and enrolled in this section.')
        metadata['members'] = [str(v) for v in ids]
        roles = metadata.get('roles', {})
        if not isinstance(roles, dict) or set(roles) - set(metadata['members']) or any(not isinstance(v, str) or len(v) > 120 for v in roles.values()):
            raise ValidationError('Group roles must name actual members.')
        milestones = metadata.get('milestones', [])
        if not isinstance(milestones, list) or len(milestones) > 20 or any(not isinstance(m, str) or len(m) > 500 for m in milestones):
            raise ValidationError('Provide at most 20 brief milestones.')
    if kind == 'portfolio':
        assignment = get_object_or_404(Assignment, id=_uuid(metadata.get('assignment_id'), 'assignment_id'),
                                        section=section, school_id=school, is_published=True)
        if not student or not Enrollment.objects.filter(section=section, student=student, school_id=school).exists():
            raise ValidationError('Portfolio work must belong to an enrolled student.')
        metadata['assignment_id'] = str(assignment.id)
    if kind in {'service', 'family_service'}:
        from spiritual_life.formation_models import PortraitDomain, BiblicalWorldviewPriority
        for field, model in [('portrait_domain_id', PortraitDomain), ('worldview_priority_id', BiblicalWorldviewPriority)]:
            if metadata.get(field):
                obj = get_object_or_404(model, id=_uuid(metadata[field], field), school_id=school, is_active=True)
                metadata[field] = str(obj.id)
        reference = metadata.get('scripture_reference', '')
        if not isinstance(reference, str) or len(reference) > 160:
            raise ValidationError('Scripture reference must be brief text.')
    if kind == 'coaching':
        teacher = get_object_or_404(get_user_model(), id=_uuid(metadata.get('teacher_account_id'), 'teacher_account_id'), is_active=True)
        if not _can_manage_section(teacher, school, section) or not taught_sections(teacher, school).filter(id=section.id).exists():
            raise ValidationError('Coaching teacher must be active and assigned to this classroom.')
        metadata['teacher_account_id'] = str(teacher.id)
    for field in ('minutes', 'cost_cents'):
        if field in metadata and (isinstance(metadata[field], bool) or not isinstance(metadata[field], int) or not 0 <= metadata[field] <= 100000000):
            raise ValidationError(f'{field} must be a non-negative integer.')
    if kind == 'resource' and metadata.get('reference'):
        from urllib.parse import urlparse
        reference = metadata['reference']
        if not isinstance(reference, str) or urlparse(reference).scheme != 'https' or not urlparse(reference).netloc:
            raise ValidationError('Resource references must use a valid HTTPS URL.')
    return metadata


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def record_collection(request):
    school, audience, sections, students = context(request)
    if request.method == 'GET':
        qs = visible_records(request, school, audience, sections, students)
        if request.query_params.get('section_id'):
            qs = qs.filter(section_id=_uuid(request.query_params['section_id'], 'section_id'))
        from spiritual_life.formation_models import PortraitDomain, BiblicalWorldviewPriority
        teachers = []
        if audience == 'admin':
            teachers = [{'id': u.id, 'name': u.get_full_name() or u.username} for u in get_user_model().objects.filter(is_active=True, staff__school_id=school, staff__status='ACTIVE', staff__role_type='TEACHER') if taught_sections(u, school).exists()]
        return Response({'portrait_domains': list(PortraitDomain.objects.filter(school_id=school, is_active=True).values('id', 'name', 'scripture_anchor')),
                         'worldview_priorities': list(BiblicalWorldviewPriority.objects.filter(school_id=school, is_active=True).values('id', 'title', 'scripture_anchor')),
                         'coaching_teachers': teachers, 'records': [serialize(r, students, audience in {'teacher', 'admin'}, request.user) for r in qs[:100]],
                         'total': qs.count(), 'truncated': qs.count() > 100, 'source': 'live'})
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    kind = data.get('kind')
    if kind not in KINDS:
        raise ValidationError('Invalid classroom record kind.')
    section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
    manager = _can_manage_section(request.user, school, section)
    if audience == 'parent' and kind not in {'absence_explanation', 'family_service'}:
        raise PermissionDenied('Parents may record absence explanations and family service participation.')
    if audience == 'student' and kind not in STUDENT_KINDS:
        raise PermissionDenied('Students may create help, goal, reflection and portfolio records.')
    if audience in {'teacher', 'admin'} and not manager:
        raise PermissionDenied('Assigned classroom authority required.')
    if kind == 'coaching' and not is_leader(request.user, school):
        raise PermissionDenied('Coaching records require school leadership.')
    student = None
    if data.get('student_id'):
        student = get_object_or_404(students, id=_uuid(data['student_id'], 'student_id'))
        if not Enrollment.objects.filter(section=section, student=student, school_id=school).exists():
            raise ValidationError('Student must be enrolled in this section.')
    if kind in STUDENT_KINDS | {'absence_explanation', 'family_service', 'accommodation', 'support_plan', 'positive_observation'} and student is None:
        raise ValidationError('Choose the student for this record.')
    visibility = data.get('visibility', 'private' if kind in STUDENT_KINDS else 'family' if student else 'class')
    if kind in PRIVATE_SUPPORT or kind == 'help_request':
        visibility = 'family' if kind == 'support_plan' and visibility == 'family' and is_leader(request.user, school) else 'staff'
    if kind in {'absence_explanation', 'family_service'}:
        visibility = 'family'
    if visibility not in {'class', 'family', 'staff', 'private'} or (student and visibility == 'class'):
        raise ValidationError('Invalid visibility for this record.')
    if audience == 'student' and visibility not in {'private', 'family', 'staff'}:
        raise PermissionDenied('Student work cannot be posted to the entire class.')
    title, body = data.get('title'), data.get('body')
    if not isinstance(title, str) or not title.strip() or len(title) > 160 or not isinstance(body, str) or not body.strip() or len(body) > 20000:
        raise ValidationError('Title and body are required within their supported lengths.')
    due = data.get('due_at')
    try:
        due = parse_datetime(due) if due else None
    except (ValueError, TypeError):
        raise ValidationError('due_at must be an ISO timestamp.')
    if data.get('due_at') and (due is None or timezone.is_naive(due)):
        raise ValidationError('due_at requires an ISO timestamp with timezone.')
    if kind in {'goal', 'support_plan', 'accommodation', 'coaching'} and due is None:
        raise ValidationError('A review date is required for goals, support and coaching.')
    metadata = validate_metadata(data, kind=kind, section=section, school=school, student=student)
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps([str(request.user.id), audience, data], sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        existing = ClassroomRecord.objects.filter(school_id=school, created_by=request.user, request_key=key).first()
        if existing:
            return Response(serialize(existing, students, manager, request.user)) if existing.fingerprint == fingerprint else Response({'detail': 'Creation retry key conflict.'}, status=409)
        record = ClassroomRecord.objects.create(request_key=key, fingerprint=fingerprint, school_id=school, section=section, student=student, kind=kind,
                  title=title.strip(), body=body, visibility=visibility, created_by=request.user,
                  owner_id=metadata['teacher_account_id'] if kind == 'coaching' else section.teacher_id if kind == 'help_request' and section.teacher_id else request.user.id,
                  due_at=due, metadata=metadata)
    return Response(serialize(record, students, manager, request.user), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_action(request, record_id):
    school, audience, sections, students = context(request)
    record = get_object_or_404(visible_records(request, school, audience, sections, students), id=record_id)
    manager = _can_manage_section(request.user, school, record.section)
    if not isinstance(request.data, dict):
        raise ValidationError('Request must be an object.')
    action = request.data.get('action')
    key = _uuid(request.data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps([str(request.user.id), request.data], sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        record = ClassroomRecord.objects.select_for_update().get(id=record.id)
        replay = record.events.filter(request_key=key).first()
        if replay:
            return Response(serialize(record, students, manager, request.user)) if replay.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
        expected = request.data.get('version')
        if isinstance(expected, bool) or not isinstance(expected, int) or expected != record.version:
            return Response({'detail': 'Record changed. Refresh before acting.'}, status=409)
        if record.kind == 'coaching' and action != 'acknowledge' and not is_leader(request.user, school):
            raise PermissionDenied('Only school leadership may resolve or reopen coaching.')
        if action in {'acknowledge', 'resolve', 'reopen'}:
            if not manager:
                raise PermissionDenied('Teacher or school leader follow-through required.')
            note = request.data.get('note', '')
            if not isinstance(note, str) or not note.strip() or len(note) > 20000:
                raise ValidationError('A follow-through note is required.')
            record.state = {'acknowledge': 'acknowledged', 'resolve': 'resolved', 'reopen': 'open'}[action]
        elif action == 'respond':
            if record.state == 'resolved':
                raise ValidationError('This record is closed.')
            if record.kind not in {'practice', 'formative_check', 'group_project', 'service', 'resource', 'announcement', 'home_support'}:
                raise ValidationError('This kind uses teacher follow-through instead of student responses.')
            student = get_object_or_404(students, id=_uuid(request.data.get('student_id'), 'student_id'))
            if student.account_id != request.user.id or not Enrollment.objects.filter(section=record.section, student=student, school_id=school).exists():
                raise PermissionDenied('Only an enrolled student may respond for themselves.')
            if record.kind == 'group_project' and str(student.id) not in record.metadata['members']:
                raise PermissionDenied('Only a group member may submit a contribution.')
            content = request.data.get('content')
            if not isinstance(content, str) or not content.strip() or len(content) > 20000:
                raise ValidationError('A response of at most 20000 characters is required.')
            response, created = ClassroomResponse.objects.get_or_create(record=record, student=student, defaults={'actor': request.user, 'content': content})
            if not created:
                response.content = content; response.feedback = ''; response.state = 'submitted'; response.version += 1; response.save()
        elif action == 'feedback':
            if not manager:
                raise PermissionDenied('Only assigned staff may review responses.')
            response = get_object_or_404(record.responses, id=_uuid(request.data.get('response_id'), 'response_id'))
            feedback = request.data.get('note')
            if not isinstance(feedback, str) or not feedback.strip() or len(feedback) > 20000:
                raise ValidationError('Feedback is required.')
            response.feedback = feedback; response.state = 'reviewed'; response.version += 1; response.save()
        else:
            raise ValidationError('Invalid classroom action.')
        record.version += 1; record.save()
        target = student if action == 'respond' else response.student if action == 'feedback' else None
        ClassroomEvent.objects.create(record=record, student=target, actor=request.user, request_key=key, fingerprint=fingerprint,
                                       action=action, payload=dict(request.data))
        return Response(serialize(record, students, manager, request.user))
