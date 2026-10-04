import hashlib
import json
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.models import Guardian, Student
from households.scoping import get_request_school_id
from .experience_access import classroom_scope, is_leader, related_students, taught_sections
from .family_models import ClassroomDisclosure, ClassroomNotificationPreference, ClassroomConferenceSlot, ClassroomFamilyThread, ClassroomFamilyMessage, ClassroomFamilyMutation, ClassroomFamilyNotice
from .models import Assignment, Enrollment, Submission
from .family_notifications import queue_notice
from .family_digest import weekly_agenda
from .submission_workflow_views import _uuid


def text(data, key, limit=20000):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValidationError(f'{key} requires text of at most {limit} characters.')
    return value.strip()


def timestamp(data, key):
    try:
        value = parse_datetime(data.get(key, ''))
    except (TypeError, ValueError):
        value = None
    if value is None or timezone.is_naive(value):
        raise ValidationError(f'{key} requires a timestamp with timezone.')
    return value


def thread_rows(user, school, audience, sections, students):
    qs = ClassroomFamilyThread.objects.filter(school_id=school, section__in=sections, student__school_id=school)
    if audience == 'parent':
        return qs.filter(guardian__account=user, student__in=students)
    if audience in {'teacher', 'admin'}:
        return qs
    raise PermissionDenied('Family conversations require a guardian or assigned staff account.')


def thread_data(row, user):
    return {'id': row.id, 'kind': row.kind, 'title': row.title, 'section_id': row.section_id,
            'student_id': row.student_id, 'guardian_id': row.guardian_id, 'assignment_id': row.assignment_id,
            'state': row.state, 'version': row.version, 'slot_id': row.slot_id,
            'conference': {'starts_at': row.slot.starts_at, 'ends_at': row.slot.ends_at, 'location': row.slot.location} if row.slot_id else None,
            'messages': [{'id': m.id, 'content': m.content, 'decision': m.decision, 'own': m.actor_id == user.id,
                          'created_at': m.created_at} for m in row.messages.all()]}


def guardian_for(school, student, user, manager, data):
    guardians = Guardian.objects.filter(school_id=school, household=student.household,
                                         household__is_active=True, account__is_active=True)
    guardian = get_object_or_404(guardians, id=_uuid(data.get('guardian_id'), 'guardian_id')) if manager else get_object_or_404(guardians, account=user)
    if ClassroomDisclosure.objects.filter(school_id=school, student=student, guardian=guardian, allowed=False).exists():
        raise PermissionDenied('Classroom disclosure is restricted for this guardian.')
    return guardian


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def family_workspace(request):
    school = get_request_school_id(request, required=True)
    audience = request.query_params.get('audience', 'parent')
    sections, students = classroom_scope(request.user, school, audience)
    threads = thread_rows(request.user, school, audience, sections, students)
    manager = audience in {'teacher', 'admin'}
    if request.method == 'GET':
        preferences = ClassroomNotificationPreference.objects.filter(school_id=school, account=request.user).first()
        digest_zone = ZoneInfo(preferences.timezone) if preferences else timezone.get_current_timezone()
        start = timezone.localdate(timezone=digest_zone); end = start + timedelta(days=6)
        assignments = Assignment.objects.filter(school_id=school, section__in=sections, is_published=True, due_date__range=(start, end)).order_by('due_date', 'id')
        if not manager:
            assignments = assignments.filter(section__enrollments__student__in=students, section__enrollments__school_id=school).distinct()
        submitted = Submission.objects.filter(school_id=school, assignment__in=assignments, enrollment__student__in=students, submitted_at__isnull=False)
        agenda = weekly_agenda(school, sections, students, start, end) if not manager else {
            'assignments': list(assignments.values('id', 'section_id', 'name', 'due_date', 'home_support')[:100]),
            'assignments_total': assignments.count(), 'truncated': assignments.count() > 100,
            'recorded_submissions': submitted.count(),
        }
        slots = ClassroomConferenceSlot.objects.filter(school_id=school, section__in=sections, state='available', starts_at__gt=timezone.now())
        guardian_rows = Guardian.objects.filter(school_id=school, household_id__in=students.values('household_id'), account__is_active=True) if manager else Guardian.objects.filter(school_id=school, account=request.user)
        notices = ClassroomFamilyNotice.objects.filter(school_id=school, account=request.user, available_at__lte=timezone.now(), dismissed_at__isnull=True).filter(Q(thread__in=threads) | Q(thread__isnull=True))
        if preferences and not preferences.in_app:
            notices = notices.none()
        return Response({'notices': list(notices.values('id', 'title', 'available_at')[:100]), 'source': 'live', 'generated_at': timezone.now(), 'threads': [thread_data(t, request.user) for t in threads[:100]],
          'truncated': threads.count() > 100 or agenda['truncated'] or slots.count() > 100,
          'slots': list(slots.values('id', 'section_id', 'starts_at', 'ends_at', 'location')[:100]),
          'guardians': list(guardian_rows.values('id', 'household_id', 'first_name', 'last_name')),
          'preferences': {key: getattr(preferences, key) for key in ['in_app', 'digest_day', 'timezone', 'quiet_start', 'quiet_end']} if preferences else {'in_app': True, 'digest_day': 0, 'timezone': 'UTC', 'quiet_start': None, 'quiet_end': None},
          'digest': {'from': start, 'to': end, 'prepared_at': timezone.now(), 'delivery': 'in_app',
                     **agenda, 'open_conversations': threads.filter(state='open').count()},
          'disclosures': list(ClassroomDisclosure.objects.filter(school_id=school).values('student_id', 'guardian_id', 'allowed', 'reason', 'updated_at')) if audience == 'admin' else []})
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    operation = data.get('operation')
    if operation not in {'preferences', 'create', 'reply', 'resolve', 'reopen', 'consent', 'slot', 'book', 'cancel', 'disclosure', 'dismiss'}:
        raise ValidationError('Invalid family operation.')
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps([audience, data], sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        previous = ClassroomFamilyMutation.objects.filter(school_id=school, actor=request.user, request_key=key).first()
        if previous:
            if previous.fingerprint != fingerprint:
                return Response({'detail': 'Retry key conflict.'}, status=409)
            # Current relationship still governs access after a disclosure or staffing change.
            if previous.result.get('thread'):
                get_object_or_404(threads, id=previous.result['thread']['id'])
            return Response(previous.result)
        if operation == 'dismiss':
            notice = get_object_or_404(ClassroomFamilyNotice, id=_uuid(data.get('notice_id'), 'notice_id'), school_id=school, account=request.user)
            if notice.thread_id:
                get_object_or_404(threads, id=notice.thread_id)
            notice.dismissed_at = timezone.now(); notice.save()
            result = {'saved': True}
        elif operation == 'preferences':
            if not isinstance(data.get('in_app'), bool) or isinstance(data.get('digest_day'), bool) or not isinstance(data.get('digest_day'), int) or not 0 <= data['digest_day'] <= 6:
                raise ValidationError('Preferences require a boolean and digest day 0–6 (Monday–Sunday).')
            try:
                ZoneInfo(data.get('timezone', ''))
                quiet = [parse_time(data[v]) if data.get(v) else None for v in ['quiet_start', 'quiet_end']]
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise ValidationError('Use a valid timezone and HH:MM quiet times.')
            if bool(quiet[0]) != bool(quiet[1]) or any(data.get(v) and quiet[i] is None for i, v in enumerate(['quiet_start', 'quiet_end'])):
                raise ValidationError('Quiet hours require both valid times.')
            ClassroomNotificationPreference.objects.update_or_create(school_id=school, account=request.user,
                defaults={'in_app': data['in_app'], 'digest_day': data['digest_day'], 'timezone': data['timezone'], 'quiet_start': quiet[0], 'quiet_end': quiet[1]})
            result = {'saved': True, 'delivery': 'in_app'}
        elif operation == 'disclosure':
            if not is_leader(request.user, school) or audience != 'admin':
                raise PermissionDenied('Disclosure restrictions require school leadership.')
            student = get_object_or_404(Student, id=_uuid(data.get('student_id'), 'student_id'), school_id=school)
            guardian = get_object_or_404(Guardian, id=_uuid(data.get('guardian_id'), 'guardian_id'), school_id=school, household=student.household)
            if not isinstance(data.get('allowed'), bool):
                raise ValidationError('allowed must be a boolean.')
            ClassroomDisclosure.objects.update_or_create(school_id=school, student=student, guardian=guardian,
                defaults={'allowed': data['allowed'], 'reason': text(data, 'reason'), 'updated_by': request.user})
            result = {'saved': True, 'student_id': student.id, 'guardian_id': guardian.id, 'allowed': data['allowed']}
        elif operation == 'slot':
            if not manager:
                raise PermissionDenied('Assigned staff publish conference availability.')
            section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
            teacher = section.teacher if audience == 'admin' else request.user
            if teacher is None:
                raise ValidationError('Assign the responsible teacher first.')
            get_user_model().objects.select_for_update().get(id=teacher.id)
            start, end = timestamp(data, 'starts_at'), timestamp(data, 'ends_at')
            if start <= timezone.now() or not timedelta(minutes=5) <= end - start <= timedelta(hours=2):
                raise ValidationError('Choose a future conference of 5–120 minutes.')
            if ClassroomConferenceSlot.objects.filter(school_id=school, teacher=teacher, starts_at__lt=end, ends_at__gt=start).exclude(state='cancelled').exists():
                return Response({'detail': 'Teacher already has availability or a booking in that interval.'}, status=409)
            slot = ClassroomConferenceSlot.objects.create(school_id=school, section=section, teacher=teacher, starts_at=start, ends_at=end, location=text(data, 'location', 200))
            result = {'saved': True, 'slot_id': slot.id}
        elif operation in {'create', 'book'}:
            section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
            student = get_object_or_404(students, id=_uuid(data.get('student_id'), 'student_id'))
            get_object_or_404(Enrollment, school_id=school, section=section, student=student)
            guardian = guardian_for(school, student, request.user, manager, data)
            kind = 'conference' if operation == 'book' else data.get('kind', 'conversation')
            if kind not in {'conversation', 'consent', 'conference'} or kind == 'conference' and operation != 'book':
                raise ValidationError('Invalid thread kind.')
            if kind == 'consent' and not manager:
                raise PermissionDenied('Classroom consent requests require assigned staff.')
            slot = None
            if operation == 'book':
                slot = get_object_or_404(ClassroomConferenceSlot.objects.select_for_update(), id=_uuid(data.get('slot_id'), 'slot_id'), school_id=school, section=section)
                if slot.state != 'available' or slot.starts_at <= timezone.now():
                    return Response({'detail': 'Conference slot is no longer available.'}, status=409)
                slot.state = 'booked'; slot.save()
            assignment = None
            if data.get('assignment_id'):
                assignment = get_object_or_404(Assignment, id=_uuid(data['assignment_id'], 'assignment_id'), school_id=school, section=section, is_published=True)
            row = ClassroomFamilyThread.objects.create(school_id=school, section=section, student=student, guardian=guardian, created_by=request.user,
                    kind=kind, slot=slot, assignment=assignment, title=text(data, 'title', 160))
            ClassroomFamilyMessage.objects.create(thread=row, actor=request.user, content=text(data, 'content'))
            result = {'thread': thread_data(row, request.user)}
        else:
            row = get_object_or_404(threads.select_for_update(), id=_uuid(data.get('thread_id'), 'thread_id'))
            if isinstance(data.get('version'), bool) or data.get('version') != row.version:
                return Response({'detail': 'Conversation changed; refresh before acting.'}, status=409)
            if operation in {'resolve', 'reopen'} and not manager:
                raise PermissionDenied('Staff record concern resolution and follow-up.')
            if operation == 'consent' and (row.kind != 'consent' or audience != 'parent' or row.guardian.account_id != request.user.id or row.state != 'open'):
                raise PermissionDenied('Only the designated guardian may respond to an open consent request.')
            if operation == 'cancel' and (row.kind != 'conference' or row.state == 'cancelled'):
                raise ValidationError('Choose an active conference.')
            if operation == 'reply' and row.state != 'open':
                raise ValidationError('Reopen the conversation before adding a reply.')
            decision = data.get('decision', '') if operation == 'consent' else ''
            if operation == 'consent' and decision not in {'agreed', 'declined'}:
                raise ValidationError('Consent must be agreed or declined.')
            if operation in {'resolve', 'reopen', 'cancel', 'consent'}:
                row.state = {'resolve': 'resolved', 'reopen': 'open', 'cancel': 'cancelled', 'consent': decision}[operation]
            if operation == 'cancel':
                slot = ClassroomConferenceSlot.objects.select_for_update().get(id=row.slot_id)
                slot.state = 'cancelled'; slot.save()
            ClassroomFamilyMessage.objects.create(thread=row, actor=request.user, content=text(data, 'content'), decision=decision)
            row.version += 1; row.save()
            result = {'thread': thread_data(row, request.user)}
        if result.get('thread'):
            row = ClassroomFamilyThread.objects.get(id=result['thread']['id'])
            recipients = [row.guardian.account, row.section.teacher]
            for recipient in recipients:
                if recipient and recipient.id != request.user.id:
                    queue_notice(school, recipient, f'thread:{row.id}:version:{row.version}', 'A classroom conversation has an update', thread=row)
        result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
        ClassroomFamilyMutation.objects.create(school_id=school, actor=request.user, request_key=key, fingerprint=fingerprint, operation=operation, result=result)
        return Response(result)
