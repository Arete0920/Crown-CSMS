import hashlib
import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from signals.models import InterventionCase, InterventionAction
from discipline.models import DisciplineIncident, DisciplineAction
from households.scoping import get_request_school_id
from .models import Section, Enrollment
from .experience_access import classroom_scope, is_leader
from .assignment_teacher_views import _can_manage_section
from .family_views import text, timestamp
from .submission_workflow_views import _uuid
from .support_models import ClassroomInterventionLink, ClassroomRestorativeLink, ClassroomSupportEvent


def reviewed_date(data):
    date = timestamp(data, 'review_at')
    if not timezone.now() < date <= timezone.now() + timedelta(days=365):
        raise ValidationError('Support review must be within the coming year.')
    return date


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classroom_support(request):
    school = get_request_school_id(request, required=True)
    audience = request.query_params.get('audience', 'teacher')
    sections, students = classroom_scope(request.user, school, audience)
    if audience not in {'teacher', 'admin'}:
        raise PermissionDenied('Staff-only instructional support details.')
    if request.method == 'GET':
        links = ClassroomInterventionLink.objects.filter(school_id=school, section__in=sections, case__school_id=school, case__student__in=students)
        if audience != 'admin': links = links.filter(case__owner_account=request.user)
        restorative = ClassroomRestorativeLink.objects.filter(school_id=school, section__in=sections, student__in=students, incident__school_id=school)
        if audience != 'admin': restorative = restorative.filter(incident__assigned_to=request.user)
        available = InterventionCase.objects.filter(school_id=school, student__in=students)
        if audience != 'admin': available = available.filter(owner_account=request.user)
        return Response({'available_cases': list(available.values('id', 'student_id', 'reason', 'owner_account_id', 'version')[:100]), 'source': 'live', 'cases': [{'id': l.case.id, 'section_id': l.section_id, 'student_id': l.case.student_id,
            'reason': l.case.reason, 'priority': l.case.priority, 'state': l.case.status, 'version': l.case.version,
            'owner_id': l.case.owner_account_id, 'review_at': l.case.review_at, 'overdue_review': bool(l.case.review_at and l.case.review_at < timezone.now() and l.case.status != 'CLOSED'),
            'actions': list(l.case.actions.values('id', 'action_type', 'note', 'created_at'))} for l in links.select_related('case')[:100]],
          'restorative': [{'id': l.incident.id, 'section_id': l.section_id, 'student_id': l.student_id, 'title': l.incident.summary,
            'state': l.incident.status, 'version': l.version, 'review_at': l.review_at,
            'actions': list(l.incident.actions.values('id', 'action_type', 'note', 'created_at'))} for l in restorative.select_related('incident')[:100]],
          'limits': {'cases': 100, 'restorative': 100}})
    data = request.data
    if not isinstance(data, dict): raise ValidationError('Request must be an object.')
    section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
    if not _can_manage_section(request.user, school, section):
        raise PermissionDenied('Active assigned teacher or explicit school leadership required.')
    operation = data.get('operation')
    if operation not in {'case', 'follow_up', 'close_case', 'reopen_case', 'restorative', 'restorative_note', 'close_restorative', 'link_case'}:
        raise ValidationError('Invalid support operation.')
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        Section.objects.select_for_update().get(id=section.id)
        previous = ClassroomSupportEvent.objects.filter(school_id=school, actor=request.user, request_key=key).first()
        if previous:
            return Response(previous.result) if previous.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
        if operation == 'link_case':
            case = get_object_or_404(InterventionCase, id=_uuid(data.get('case_id'), 'case_id'), school_id=school, student__in=students)
            get_object_or_404(Enrollment, school_id=school, section=section, student=case.student)
            if not is_leader(request.user, school) and case.owner_account_id != request.user.id:
                raise PermissionDenied('Only an owned case may be linked to this classroom.')
            ClassroomInterventionLink.objects.get_or_create(school_id=school, section=section, case=case)
            result = {'saved': True, 'case_id': case.id}
        elif operation in {'case', 'restorative'}:
            student = get_object_or_404(students, id=_uuid(data.get('student_id'), 'student_id'))
            get_object_or_404(Enrollment, school_id=school, section=section, student=student)
            review = reviewed_date(data)
            note = text(data, 'note')
            if operation == 'case':
                priority = data.get('priority', 'MED')
                if priority not in {'LOW', 'MED', 'HIGH'}: raise ValidationError('Priority must be LOW, MED or HIGH.')
                owner = get_object_or_404(get_user_model(), id=_uuid(data.get('owner_id', str(request.user.id)), 'owner_id'), is_active=True)
                if not _can_manage_section(owner, school, section): raise ValidationError('Owner must be authorized for this classroom.')
                case = InterventionCase.objects.create(school_id=school, student=student, owner_account=owner, reason=text(data, 'title', 200), priority=priority, review_at=review)
                InterventionAction.objects.create(school_id=school, case=case, created_by_account=request.user, action_type='PLAN', note=note)
                ClassroomInterventionLink.objects.create(school_id=school, section=section, case=case)
                result = {'saved': True, 'case_id': case.id}
            else:
                from crown_api.views_academics import _verified_attendance_identity
                core, _ = _verified_attendance_identity(student.id, school)
                incident = DisciplineIncident.objects.create(school_id=school, student=core, reported_by=request.user, assigned_to=request.user,
                    occurred_at=timezone.now(), location=section.course.name[:120], category='other', summary=text(data, 'title', 180), details=note)
                DisciplineAction.objects.create(incident=incident, actor=request.user, action_type='created', note=note)
                ClassroomRestorativeLink.objects.create(school_id=school, section=section, incident=incident, student=student, review_at=review)
                result = {'saved': True, 'incident_id': incident.id}
        elif operation in {'follow_up', 'close_case', 'reopen_case'}:
            link = get_object_or_404(ClassroomInterventionLink, school_id=school, section=section, case_id=_uuid(data.get('case_id'), 'case_id'), case__school_id=school)
            case = InterventionCase.objects.select_for_update().get(id=link.case_id)
            if not is_leader(request.user, school) and case.owner_account_id != request.user.id:
                raise PermissionDenied('Assigned case owner or school leadership required.')
            if isinstance(data.get('version'), bool) or data.get('version') != case.version:
                return Response({'detail': 'Support case changed; refresh before acting.'}, status=409)
            if operation == 'follow_up' and case.status == 'CLOSED': raise ValidationError('Reopen the case before adding follow-up.')
            note = text(data, 'note')
            if operation == 'close_case': case.status='CLOSED'; case.closed_at=timezone.now()
            else:
                case.status='IN_PROGRESS'; case.closed_at=None
                case.review_at=reviewed_date(data)
            action = InterventionAction.objects.create(school_id=school, case=case, created_by_account=request.user,
                  action_type='FOLLOWUP', note=note)
            case.last_action_at=action.created_at; case.version += 1; case.save()
            result = {'saved': True, 'case_id': case.id, 'version': case.version}
        else:
            link = get_object_or_404(ClassroomRestorativeLink.objects.select_for_update(), school_id=school, section=section, incident_id=_uuid(data.get('incident_id'), 'incident_id'), incident__school_id=school)
            incident = DisciplineIncident.objects.select_for_update().get(id=link.incident_id)
            if not is_leader(request.user, school) and incident.assigned_to_id != request.user.id:
                raise PermissionDenied('Assigned restorative owner or school leadership required.')
            if isinstance(data.get('version'), bool) or data.get('version') != link.version or incident.status == 'closed':
                return Response({'detail': 'Restorative plan changed or closed; refresh.'}, status=409)
            note=text(data, 'note')
            if operation == 'close_restorative': incident.status='closed'
            else: incident.status='investigating'; link.review_at=reviewed_date(data)
            incident.save(); link.version += 1; link.save()
            DisciplineAction.objects.create(incident=incident, actor=request.user, action_type='closed' if operation == 'close_restorative' else 'note', note=note)
            result={'saved': True, 'incident_id': incident.id, 'version': link.version}
        result=json.loads(json.dumps(result, cls=DjangoJSONEncoder))
        ClassroomSupportEvent.objects.create(school_id=school, section=section, actor=request.user, request_key=key, fingerprint=fingerprint, operation=operation, payload=data, result=result)
        return Response(result)
