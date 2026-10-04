import hashlib
import json
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Case, When, Value, CharField, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from core.models import Staff
from core.permissions import CrownModulePermission, user_has_permission
from .requirement_models import StaffRequirement, StaffRequirementEvent, school_today


def identifier(value, name):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(f'{name} requires a UUID.')


def text(data, name, limit):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValidationError(f'{name} is required and must be at most {limit} characters.')
    return value.strip()


def date_value(data, name, optional=False):
    value = data.get(name)
    if optional and value in (None, ''):
        return None
    try:
        result = parse_date(value)
    except (ValueError, TypeError):
        result = None
    if result is None:
        raise ValidationError(f'{name} requires an ISO date.')
    return result


def snapshot(row):
    return {'id': str(row.id), 'staff_id': str(row.staff_id), 'title': row.title,
        'category': row.category, 'due_date': row.due_date.isoformat(),
        'completed_on': row.completed_on.isoformat() if row.completed_on else None,
        'valid_until': row.valid_until.isoformat() if row.valid_until else None,
        'evidence_reference': row.evidence_reference, 'version': row.version}


def scoped_requirements(school):
    today = school_today(school)
    return StaffRequirement.objects.filter(school=school, staff__school=school).select_related('staff').annotate(
        status=Case(
            When(completed_on__isnull=False, valid_until__lt=today, then=Value('expired')),
            When(completed_on__isnull=False, valid_until__lte=today+timedelta(days=30), then=Value('expiring')),
            When(completed_on__isnull=False, then=Value('complete')),
            When(due_date__lt=today, then=Value('overdue')),
            default=Value('pending'), output_field=CharField()))


@extend_schema(methods=['GET'], responses=OpenApiTypes.OBJECT)
@extend_schema(methods=['POST'], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([CrownModulePermission('hr.view', write_code='hr.edit')])
def staff_requirements(request):
    if not request.headers.get('X-School-Id'):
        raise ValidationError('X-School-Id is required for staff requirements.')
    if not request.user.is_active:
        raise PermissionDenied('Active account required.')
    school = request.school
    try:
        today = school_today(school)
    except ModelValidationError as exc:
        raise ValidationError(exc.messages)
    if request.method == 'GET':
        rows = scoped_requirements(school)
        staff = Staff.objects.filter(school=school, status='ACTIVE')
        if request.query_params.get('staff_id'):
            selected = get_object_or_404(Staff, school=school, id=identifier(request.query_params['staff_id'], 'staff_id'))
            rows = rows.filter(staff=selected)
        if request.query_params.get('staff_search'):
            search = request.query_params['staff_search'][:100]
            staff = staff.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search))
        try:
            offset = int(request.query_params.get('offset', '0'))
        except (ValueError, TypeError):
            raise ValidationError('offset must be a nonnegative integer.')
        if not 0 <= offset <= 100000:
            raise ValidationError('offset must be between 0 and 100000.')
        total = rows.count()
        summary = {r['status']: r['count'] for r in rows.order_by().values('status').annotate(count=Count('id'))}
        visible = [{**snapshot(row), 'staff_name': f'{row.staff.first_name} {row.staff.last_name}',
                    'staff_status': row.staff.status, 'status': row.status} for row in rows[offset:offset+100]]
        history = None
        if request.query_params.get('requirement_id'):
            selected = get_object_or_404(rows, id=identifier(request.query_params['requirement_id'], 'requirement_id'))
            events = selected.events.filter(school=school)
            try:
                history_offset = int(request.query_params.get('history_offset', '0'))
            except (ValueError, TypeError):
                raise ValidationError('history_offset must be a nonnegative integer.')
            if not 0 <= history_offset <= 100000:
                raise ValidationError('history_offset must be between 0 and 100000.')
            history_total = events.count()
            history = {'requirement_id': str(selected.id), 'total': history_total, 'offset': history_offset,
                'next_offset': history_offset+100 if history_offset+100 < history_total else None,
                'events': list(events.order_by('-created_at', '-id').values('action', 'version', 'before', 'after', 'reason', 'created_at', 'actor_id')[history_offset:history_offset+100])}
        return Response({'source': 'live', 'generated_at': timezone.now(), 'today': today.isoformat(), 'can_edit': user_has_permission(request.user, 'hr.edit', school),
            'requirements': visible, 'total': total, 'offset': offset, 'next_offset': offset+100 if offset+100 < total else None,
            'summary': summary, 'staff': list(staff.values('id', 'first_name', 'last_name')[:200]), 'staff_total': staff.count(), 'history': history})
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    key = identifier(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    operation = data.get('operation')
    if not isinstance(operation, str) or operation not in {'create', 'complete', 'reopen', 'reschedule'}:
        raise ValidationError('Choose create, complete, reopen or reschedule.')
    reason = text(data, 'reason', 2000)
    with transaction.atomic():
        actor = get_user_model().objects.select_for_update().get(id=request.user.id)
        if not actor.is_active or not user_has_permission(actor, 'hr.edit', school):
            raise PermissionDenied('Staff requirement edit permission required.')
        replay = StaffRequirementEvent.objects.filter(school=school, actor=request.user, request_key=key).first()
        if replay:
            return Response(replay.after) if replay.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
        before = {}
        if operation == 'create':
            staff = get_object_or_404(Staff.objects.select_for_update(), school=school,
                id=identifier(data.get('staff_id'), 'staff_id'), status='ACTIVE')
            category = data.get('category')
            if not isinstance(category, str) or category not in dict(StaffRequirement._meta.get_field('category').choices):
                raise ValidationError('Choose a supported requirement category.')
            row = StaffRequirement.objects.create(school=school, staff=staff, title=text(data, 'title', 160),
                category=category, due_date=date_value(data, 'due_date'))
        else:
            row = get_object_or_404(StaffRequirement.objects.select_for_update(), school=school,
                staff__school=school, id=identifier(data.get('requirement_id'), 'requirement_id'))
            if isinstance(data.get('version'), bool) or not isinstance(data.get('version'), int) or data['version'] != row.version:
                return Response({'detail': 'Requirement changed; refresh before saving.'}, status=409)
            before = snapshot(row)
            if operation == 'complete':
                if row.completed_on is not None:
                    return Response({'detail': 'Reopen the requirement before recording new completion evidence.'}, status=409)
                row.completed_on = date_value(data, 'completed_on')
                row.valid_until = date_value(data, 'valid_until', optional=True)
                if row.completed_on > today or (row.valid_until and row.valid_until < row.completed_on):
                    raise ValidationError('Completion cannot be in the future; expiry cannot precede completion.')
                row.evidence_reference = text(data, 'evidence_reference', 300)
            elif operation == 'reopen':
                row.completed_on = None; row.valid_until = None; row.evidence_reference = ''
            else:
                row.due_date = date_value(data, 'due_date')
            row.version += 1; row.save()
        after = snapshot(row)
        StaffRequirementEvent.objects.create(school=school, requirement=row, actor=request.user, request_key=key,
            fingerprint=fingerprint, action=operation, version=row.version, before=before, after=after, reason=reason)
        return Response(after, status=201 if operation == 'create' else 200)
