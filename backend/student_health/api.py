import hashlib
import json
import uuid
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Q, Count, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core.models import Student, Guardian
from core.permissions import CrownModulePermission, user_has_permission
from .models import HealthEntry, MedicationAuthorization, HealthMutation, school_date


def identifier(value, name):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(f'{name} requires a UUID.')


def text(data, name, limit, optional=False):
    value = data.get(name, '')
    if not isinstance(value, str) or len(value) > limit or (not optional and not value.strip()):
        raise ValidationError(f'{name} must contain at most {limit} characters and is required unless marked optional.')
    return value.strip()


def day(data, name, optional=False):
    value = data.get(name)
    if optional and value in (None, ''):
        return None
    try:
        result = parse_date(value)
    except (ValueError, TypeError):
        result = None
    if not result:
        raise ValidationError(f'{name} requires an ISO date.')
    return result


def amount(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Dose must be a positive decimal with at most three decimal places.')
    if not result.is_finite() or result <= 0 or result >= 100000 or result.as_tuple().exponent < -3:
        raise ValidationError('Dose must be a positive decimal with at most three decimal places.')
    return result


def event_time(data):
    try:
        result = parse_datetime(data.get('occurred_at'))
    except (ValueError, TypeError):
        result = None
    if result is None or timezone.is_naive(result) or result > timezone.now():
        raise ValidationError('occurred_at requires a timezone-aware timestamp no later than now.')
    return result


def authorization_data(row):
    today = school_date(row.school)
    state = 'revoked' if row.revoked_at else 'scheduled' if row.starts_on > today else 'expired' if row.ends_on < today else 'active'
    return {'id': str(row.id), 'student_id': str(row.student_id), 'guardian_id': str(row.guardian_id),
        'medication': row.medication, 'dose': str(row.dose), 'unit': row.unit, 'route': row.route,
        'directions': row.directions, 'order_evidence': row.order_evidence, 'consent_evidence': row.consent_evidence,
        'starts_on': row.starts_on.isoformat(), 'ends_on': row.ends_on.isoformat(), 'state': state,
        'revoked_at': row.revoked_at, 'revocation_reason': row.revocation_reason, 'version': row.version}


def page_offset(request, name):
    try:
        value = int(request.query_params.get(name, '0'))
    except (ValueError, TypeError):
        raise ValidationError(f'{name} must be a nonnegative integer.')
    if not 0 <= value <= 100000:
        raise ValidationError(f'{name} must be between 0 and 100000.')
    return value


@extend_schema(methods=['GET'], responses=OpenApiTypes.OBJECT)
@extend_schema(methods=['POST'], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([CrownModulePermission('student_health.view', write_code='student_health.edit')])
def health_workspace(request):
    if not request.headers.get('X-School-Id'):
        raise ValidationError('X-School-Id is required for clinical records.')
    if not request.user.is_active:
        raise PermissionDenied('Active clinical account required.')
    school = request.school
    try:
        today = school_date(school)
    except ModelValidationError as exc:
        raise ValidationError(exc.messages)
    if request.method == 'GET':
        students = Student.objects.filter(school=school)
        search = request.query_params.get('search', '')[:100]
        if search:
            students = students.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(student_number__icontains=search))
        result = {'source': 'live', 'generated_at': timezone.now(),
            'can_edit': user_has_permission(request.user, 'student_health.edit', school),
            'students': list(students.values('id', 'first_name', 'last_name', 'student_number', 'status')[:200]), 'students_total': students.count()}
        if not request.query_params.get('student_id'):
            return Response(result)
        student = get_object_or_404(Student, school=school, id=identifier(request.query_params['student_id'], 'student_id'))
        entries = HealthEntry.objects.filter(school=school, student=student, student__school=school).annotate(
            superseded=Exists(HealthEntry.objects.filter(school=school, corrects_id=OuterRef('pk'))))
        authorizations = MedicationAuthorization.objects.filter(school=school, student=student, guardian__school=school).select_related('school')
        offset = page_offset(request, 'offset')
        order_offset = page_offset(request, 'authorization_offset')
        history_offset = page_offset(request, 'history_offset')
        history = HealthMutation.objects.filter(school=school, student=student).order_by('-created_at', '-id')
        history_total = history.count()
        order_total = authorizations.count()
        total = entries.count()
        result.update({'student_id': str(student.id), 'student_status': student.status,
            'guardians': list(Guardian.objects.filter(school=school, family=student.family, custody_flag__in=[False]).values('id', 'first_name', 'last_name')),
            'entries': list(entries.values('id', 'kind', 'occurred_at', 'topic', 'summary', 'follow_up_on', 'evidence_reference',
                'authorization_id', 'administration_state', 'administered_dose', 'administered_unit', 'corrects_id', 'created_at', 'recorded_by_id', 'superseded')[offset:offset+100]),
            'entries_total': total, 'offset': offset, 'next_offset': offset+100 if offset+100 < total else None,
            'summary': {r['kind']: r['count'] for r in entries.filter(superseded=False).order_by().values('kind').annotate(count=Count('id'))},
            'follow_up_due': entries.filter(superseded=False, follow_up_on__lte=today).count(),
            'authorizations': [authorization_data(row) for row in authorizations[order_offset:order_offset+100]],
            'authorizations_total': order_total, 'authorization_offset': order_offset,
            'authorizations_next_offset': order_offset+100 if order_offset+100 < order_total else None,
            'history': list(history.values('operation', 'reason', 'result', 'created_at', 'actor_id')[history_offset:history_offset+100]),
            'history_total': history_total, 'history_offset': history_offset,
            'history_next_offset': history_offset+100 if history_offset+100 < history_total else None})
        return Response(result)
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError('Request must be an object.')
    key = identifier(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    operation = data.get('operation')
    if not isinstance(operation, str) or operation not in {'authorize', 'revoke', 'record'}:
        raise ValidationError('Choose authorize, revoke or record.')
    reason = text(data, 'reason', 2000)
    try:
        with transaction.atomic():
            actor = get_user_model().objects.select_for_update().get(id=request.user.id)
            if not actor.is_active or not user_has_permission(actor, 'student_health.edit', school):
                raise PermissionDenied('Clinical record edit permission required.')
            replay = HealthMutation.objects.filter(school=school, actor=request.user, request_key=key).first()
            if replay:
                return Response(replay.result) if replay.fingerprint == fingerprint else Response({'detail': 'Retry key conflict.'}, status=409)
            student = get_object_or_404(Student.objects.select_for_update(), school=school, id=identifier(data.get('student_id'), 'student_id'))
            if operation == 'authorize':
                if student.status != 'ACTIVE':
                    raise ValidationError('New medication authorizations require an active canonical student.')
                guardian = get_object_or_404(Guardian.objects.select_for_update(), school=school, family=student.family, id=identifier(data.get('guardian_id'), 'guardian_id'))
                row = MedicationAuthorization.objects.create(school=school, student=student, guardian=guardian,
                    guardian_authority_verified=data.get('guardian_authority_verified') is True,
                    medication=text(data, 'medication', 160), dose=amount(data.get('dose')), unit=text(data, 'unit', 24),
                    route=text(data, 'route', 40), directions=text(data, 'directions', 2000),
                    order_evidence=text(data, 'order_evidence', 300), consent_evidence=text(data, 'consent_evidence', 300),
                    starts_on=day(data, 'starts_on'), ends_on=day(data, 'ends_on'), recorded_by=request.user)
                result = {'saved': True, 'authorization_id': str(row.id), 'version': row.version}
            elif operation == 'revoke':
                row = get_object_or_404(MedicationAuthorization.objects.select_for_update(), school=school, student=student,
                    id=identifier(data.get('authorization_id'), 'authorization_id'))
                if isinstance(data.get('version'), bool) or not isinstance(data.get('version'), int) or data.get('version') != row.version or row.revoked_at:
                    return Response({'detail': 'Authorization changed or was revoked; refresh.'}, status=409)
                row.revoked_at = timezone.now(); row.revocation_reason = reason; row.version += 1; row.save()
                result = {'saved': True, 'authorization_id': str(row.id), 'version': row.version}
            else:
                kind = data.get('kind')
                if not isinstance(kind, str) or kind not in dict(HealthEntry._meta.get_field('kind').choices):
                    raise ValidationError('Choose a supported health record kind.')
                correction = None
                if data.get('corrects_id'):
                    correction = get_object_or_404(HealthEntry.objects.select_for_update(), school=school, student=student,
                        kind=kind, id=identifier(data['corrects_id'], 'corrects_id'))
                    if HealthEntry.objects.filter(corrects=correction).exists():
                        return Response({'detail': 'This entry already has a correction; refresh and correct the latest entry.'}, status=409)
                elif student.status != 'ACTIVE':
                    raise ValidationError('New health entries require an active canonical student; retained entries may be corrected.')
                authorization = None
                dose = None; unit = ''; state = ''
                if kind == 'administration':
                    authorization = get_object_or_404(MedicationAuthorization.objects.select_for_update(), school=school,
                        student=student, id=identifier(data.get('authorization_id'), 'authorization_id'))
                    authorization.guardian = Guardian.objects.select_for_update().get(id=authorization.guardian_id)
                    state = data.get('administration_state')
                    if not isinstance(state, str) or state not in {'given', 'refused', 'not_given'}:
                        raise ValidationError('Choose given, refused or not given.')
                    if state == 'given':
                        dose = amount(data.get('administered_dose')); unit = text(data, 'administered_unit', 24)
                    elif data.get('administered_dose') not in (None, '') or data.get('administered_unit'):
                        raise ValidationError('Refused/not-given records must not include an administered dose.')
                elif data.get('authorization_id') or data.get('administration_state') or data.get('administered_dose') not in (None, '') or data.get('administered_unit'):
                    raise ValidationError('Medication fields require an administration entry.')
                row = HealthEntry.objects.create(school=school, student=student, kind=kind, occurred_at=event_time(data),
                    topic=text(data, 'topic', 160), summary=text(data, 'summary', 4000), follow_up_on=day(data, 'follow_up_on', optional=True),
                    evidence_reference=text(data, 'evidence_reference', 300, optional=True), authorization=authorization,
                    administration_state=state, administered_dose=dose, administered_unit=unit, corrects=correction, recorded_by=request.user)
                result = {'saved': True, 'entry_id': str(row.id), 'corrects_id': str(correction.id) if correction else None}
            HealthMutation.objects.create(school=school, student=student, actor=request.user, request_key=key, fingerprint=fingerprint,
                operation=operation, reason=reason, result=result)
            return Response(result, status=201 if operation != 'revoke' else 200)
    except ModelValidationError as exc:
        raise ValidationError(exc.messages)
