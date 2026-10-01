import hashlib
import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import StudentIdentityLink, UserRole
from crown_api.models import AttendanceRecord
from households.scoping import get_request_school_id
from .experience_access import is_leader, taught_sections
from .family_views import text, timestamp
from .models import Section, Enrollment, LessonPlan
from .operations_models import ClassroomAttendanceSession, ClassroomSubstituteGrant, ClassroomEmergencySession, ClassroomEmergencyCheck, ClassroomOperationEvent
from .attendance_evidence import record_attendance_evidence
from .submission_workflow_views import _uuid


def grants(user, school):
    now = timezone.now()
    return ClassroomSubstituteGrant.objects.filter(school_id=school, account=user, starts_at__lte=now, expires_at__gt=now, revoked_at__isnull=True, section__school_id=school)


def operational_sections(user, school):
    if not user.is_active:
        raise PermissionDenied('Active account required.')
    all_sections = Section.objects.filter(school_id=school, course__school_id=school)
    if is_leader(user, school):
        return all_sections
    own = taught_sections(user, school).values('id')
    return all_sections.filter(Q(id__in=own) | Q(id__in=grants(user, school).values('section_id')))


def day_for(value):
    try:
        day = parse_date(value)
    except (ValueError, TypeError):
        day = None
    if not day or day > timezone.localdate() or day < timezone.localdate() - timedelta(days=365):
        raise ValidationError('Choose a date within the last year, including today.')
    return day


def emergency_data(session):
    return {'id': session.id, 'title': session.title, 'kind': session.kind, 'version': session.version,
            'started_at': session.started_at, 'completed_at': session.completed_at, 'completion_note': session.completion_note,
            'checks': list(session.checks.values('student_id', 'state', 'note', 'checked_at'))}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classroom_operations(request):
    school = get_request_school_id(request, required=True)
    sections = operational_sections(request.user, school)
    if not sections.exists() and not is_leader(request.user, school):
        raise PermissionDenied('Assigned classroom or active substitute grant required.')
    if request.method == 'GET':
        result = {'source': 'live', 'generated_at': timezone.now(), 'sections': list(sections.values('id', 'course__name', 'term')[:200]),
                  'substitute_candidates': list(get_user_model().objects.filter(is_active=True, roles__school_id=school,
                     roles__role_code__in=['TEACHER', 'teacher', 'SUBSTITUTE']).distinct().values('id', 'username')[:200])}
        if not request.query_params.get('section_id'):
            return Response(result)
        section = get_object_or_404(sections, id=_uuid(request.query_params['section_id'], 'section_id'))
        day = day_for(request.query_params.get('date', timezone.localdate().isoformat()))
        students = [e.student for e in Enrollment.objects.filter(school_id=school, section=section, student__school_id=school, student__is_active=True).select_related('student')]
        identities = StudentIdentityLink.objects.filter(school_id=school, verification_status='verified', compatibility_student__in=students,
                            core_student__school_id=school, compatibility_student__school_id=school).exclude(evidence_reference='')
        links = {l.compatibility_student_id: l.core_student_id for l in identities if l.evidence_reference.strip()}
        attendance = {r.student_id: r.status for r in AttendanceRecord.objects.filter(student_id__in=links.values(), section=section, date=day)}
        session = ClassroomAttendanceSession.objects.filter(school_id=school, section=section, date=day).first()
        emergencies = ClassroomEmergencySession.objects.filter(school_id=school, section=section).order_by('-started_at')
        own_authority = is_leader(request.user, school) or taught_sections(request.user, school).filter(id=section.id).exists()
        result.update({'section_id': section.id, 'date': day, 'can_delegate': own_authority, 'attendance_version': session.version if session else 0,
            'roster': [{'id': s.id, 'name': f'{s.first_name} {s.last_name}', 'identity_verified': s.id in links,
                        'attendance': attendance.get(links.get(s.id))} for s in students],
            'attendance_history': list(session.events.values('version', 'changes', 'reason', 'created_at')) if session else [],
            'packet': {'prepared_at': timezone.now(), 'lesson_plans': list(LessonPlan.objects.filter(school_id=school, section=section, plan_date=day).values('plan_date', 'objectives', 'materials', 'activities', 'homework')),
                       'substitute_instructions': list(grants(request.user, school).filter(section=section).values_list('instructions', flat=True)),
                       'limitations': ['Roster accountability is not an emergency dispatch or medical record.', 'Absence explanations do not change attendance.']},
            'emergencies': [emergency_data(s) for s in emergencies[:20]],
            'delegations': list(ClassroomSubstituteGrant.objects.filter(school_id=school, section=section).values('id', 'account_id', 'starts_at', 'expires_at', 'revoked_at')) if own_authority else []})
        return Response(result)
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
    operation = data.get('operation')
    if operation not in {'attendance', 'grant', 'revoke', 'emergency', 'check', 'complete'}:
        raise ValidationError('Invalid classroom operation.')
    own_authority = is_leader(request.user, school) or taught_sections(request.user, school).filter(id=section.id).exists()
    if operation in {'grant', 'revoke'} and not own_authority:
        raise PermissionDenied('Substitutes cannot delegate or extend access.')
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        Section.objects.select_for_update().get(id=section.id)
        if not operational_sections(request.user, school).filter(id=section.id).exists():
            raise PermissionDenied('Classroom access expired or was revoked.')
        previous = ClassroomOperationEvent.objects.filter(school_id=school, actor=request.user, request_key=key).first()
        if previous:
            return Response(previous.result) if previous.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
        if operation == 'attendance':
            day = day_for(data.get('date'))
            session = ClassroomAttendanceSession.objects.filter(school_id=school, section=section, date=day).first()
            expected = data.get('version')
            if isinstance(expected, bool) or not isinstance(expected, int) or expected != (session.version if session else 0):
                return Response({'detail': 'Attendance changed; refresh before saving.'}, status=409)
            items = data.get('items')
            if not isinstance(items, list) or not 1 <= len(items) <= 200 or any(not isinstance(v, dict) for v in items):
                raise ValidationError('Provide 1–200 attendance rows.')
            from crown_api.views_academics import _verified_attendance_identity
            prepared = []; seen = set()
            for item in items:
                student_id = _uuid(item.get('student_id'), 'student_id')
                core, student = _verified_attendance_identity(student_id, school)
                get_object_or_404(Enrollment, school_id=school, section=section, student=student, student__is_active=True)
                status = item.get('status')
                if student.id in seen or status not in {'PRESENT', 'ABSENT', 'TARDY', 'EXCUSED'}:
                    raise ValidationError('Attendance students must be unique and statuses valid.')
                seen.add(student.id)
                before = AttendanceRecord.objects.filter(student=core, section=section, date=day).values_list('status', flat=True).first()
                prepared.append((core, student, before, status))
            reason = text(data, 'reason')
            changes = []
            for core, student, before, status in prepared:
                AttendanceRecord.objects.update_or_create(student=core, section=section, date=day, defaults={'status': status})
                changes.append({'student_id': str(student.id), 'core_student_id': str(core.id), 'before': before, 'after': status})
            version = record_attendance_evidence(section, day, request.user, changes, reason)
            result = {'saved': True, 'version': version}
        elif operation == 'grant':
            account = get_object_or_404(get_user_model(), id=_uuid(data.get('account_id'), 'account_id'), is_active=True)
            if not UserRole.objects.filter(user=account, school_id=school, role_code__in=['TEACHER', 'teacher', 'SUBSTITUTE']).exists():
                raise ValidationError('Choose a school-authorized teacher or substitute account.')
            start, expiry = timestamp(data, 'starts_at'), timestamp(data, 'expires_at')
            if expiry <= timezone.now() or not timedelta(minutes=5) <= expiry - start <= timedelta(days=7):
                raise ValidationError('Substitute access must last 5 minutes–7 days and expire in the future.')
            grant = ClassroomSubstituteGrant.objects.create(school_id=school, section=section, account=account, granted_by=request.user,
                    starts_at=start, expires_at=expiry, instructions=text(data, 'instructions'))
            result = {'saved': True, 'grant_id': grant.id}
        elif operation == 'revoke':
            grant = get_object_or_404(ClassroomSubstituteGrant, school_id=school, section=section, id=_uuid(data.get('grant_id'), 'grant_id'))
            text(data, 'reason'); grant.revoked_at = timezone.now(); grant.save()
            result = {'saved': True}
        elif operation == 'emergency':
            if data.get('kind') not in {'drill', 'incident'}:
                raise ValidationError('Choose drill or incident.')
            session = ClassroomEmergencySession.objects.create(school_id=school, section=section, title=text(data, 'title', 160), kind=data['kind'], started_by=request.user)
            for enrollment in Enrollment.objects.filter(school_id=school, section=section, student__school_id=school, student__is_active=True):
                ClassroomEmergencyCheck.objects.create(session=session, student=enrollment.student)
            result = {'emergency': emergency_data(session)}
        else:
            session = get_object_or_404(ClassroomEmergencySession.objects.select_for_update(), id=_uuid(data.get('session_id'), 'session_id'), school_id=school, section=section)
            if isinstance(data.get('version'), bool) or data.get('version') != session.version or session.completed_at:
                return Response({'detail': 'Accountability session changed or is complete; refresh.'}, status=409)
            if operation == 'check':
                check = get_object_or_404(session.checks, student_id=_uuid(data.get('student_id'), 'student_id'))
                if data.get('state') not in {'present', 'missing', 'released'}:
                    raise ValidationError('Choose present, missing or released.')
                check.state = data['state']; check.note = text(data, 'note'); check.checked_by = request.user; check.checked_at = timezone.now(); check.save()
            else:
                if session.checks.filter(state__in=['unknown', 'missing']).exists():
                    return Response({'detail': 'Unaccounted students remain; resolve each check before completing.'}, status=409)
                session.completion_note = text(data, 'note'); session.completed_at = timezone.now()
            session.version += 1; session.save()
            result = {'emergency': emergency_data(session)}
        result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
        ClassroomOperationEvent.objects.create(school_id=school, section=section, actor=request.user, request_key=key, fingerprint=fingerprint, operation=operation, payload=data, result=result)
        return Response(result)
