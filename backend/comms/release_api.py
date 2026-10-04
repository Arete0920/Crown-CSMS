"""School workbench and authenticated guardian feed for coordinated releases."""
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.models import AuditLog
from households.models import Guardian
from households.scoping import get_request_school_id
from reenrollment.models import ReenrollmentSession
from core.permissions import user_has_permission
from .models import ContentRelease, ReleaseReceipt
from .release_services import audit, metrics, preview, public_content, publish, invalidate_session_releases


class ReleaseInput(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    blocks = serializers.JSONField()
    publish_at = serializers.DateTimeField(required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    supersedes = serializers.UUIDField(required=False, allow_null=True)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise ValidationError({'non_field_errors': ['Provide a JSON object.']})
        if set(data) - set(self.fields):
            raise ValidationError({'non_field_errors': ['Unknown release fields.']})
        for key in ('publish_at', 'expires_at'):
            if data.get(key):
                value = parse_datetime(data[key]) if isinstance(data[key], str) else None
                if value is None or timezone.is_naive(value):
                    raise ValidationError({key: ['Schedule timestamps must include timezone offsets.']})
        return super().to_internal_value(data)


def manager(request, session):
    if not (request.user.is_superuser or user_has_permission(request.user, 'admissions.edit', school=session.school)):
        raise PermissionDenied('Re-enrollment editing permission required.')


def summary(release):
    return {'id': str(release.pk), 'title': release.title, 'blocks': release.blocks, 'revision': release.revision, 'status': release.status, 'publish_at': release.publish_at, 'expires_at': release.expires_at, 'last_error': release.last_error, 'supersedes': str(release.supersedes_id) if release.supersedes_id else None, 'metrics': metrics(release)}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def releases(request, session_id):
    session = get_object_or_404(ReenrollmentSession, pk=session_id, school_id=get_request_school_id(request))
    manager(request, session)
    if request.method == 'GET':
        return Response([summary(r) for r in session.content_releases.order_by('-updated_at')[:100]])
    serializer = ReleaseInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    supersedes_id = data.pop('supersedes', None)
    if supersedes_id:
        previous = get_object_or_404(ContentRelease, pk=supersedes_id, session__school=session.school, status='published')
        data['supersedes'] = previous
    try:
        with transaction.atomic():
            release = ContentRelease(session=session, owner=request.user, **data)
            release.save()
            audit(release, request.user, 'created')
    except ModelValidationError as exc:
        raise ValidationError(exc.messages) from exc
    return Response(summary(release), status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_action(request, release_id, action):
    school_id = get_request_school_id(request)
    if not isinstance(request.data, dict):
        raise ValidationError("Provide a JSON object.")
    try:
        with transaction.atomic():
            initial = get_object_or_404(ContentRelease, pk=release_id, session__school_id=school_id)
            session = ReenrollmentSession.objects.select_for_update().select_related('school').get(pk=initial.session_id)
            manager(request, session)
            release = ContentRelease.objects.select_for_update().get(pk=release_id)
            release.session = session
            if action == 'preview':
                data = preview(release)
                return Response({**public_content(data), 'fingerprint': data['fingerprint'], 'recipients': len(data['audience']), 'portal_recipients': sum(bool(t['account_id']) for t in data['audience']), 'email_recipients': sum(t['email_enabled'] for t in data['audience'])})
            if type(request.data.get('revision')) is not int or request.data.get('revision') != release.revision:
                return Response({'detail': 'Release changed; refresh before continuing.'}, status=409)
            if action == 'publish' and release.status == 'published':
                return Response(summary(release))
            if release.status in ('published', 'cancelled'):
                raise ValidationError('Create a correction release; this release is immutable.')
            if action == 'update':
                serializer = ReleaseInput(data=request.data.get('content', {}))
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                if 'supersedes' in data:
                    raise ValidationError('Correction relationship cannot be edited.')
                for key, value in data.items():
                    setattr(release, key, value)
                release.revision += 1
                release.status = 'draft'
                release.approved_fingerprint = ''
                release.approved_by = None
                release.last_error = ''
                release.save()
            elif action == 'approve':
                data = preview(release)
                if request.data.get('fingerprint') != data['fingerprint']:
                    return Response({'detail': 'Preview changed; preview again.'}, status=409)
                if release.expires_at and release.expires_at <= timezone.now():
                    raise ValidationError('Release has expired.')
                release.status = 'approved'
                release.approved_fingerprint = data['fingerprint']
                release.approved_by = request.user
                release.save()
            elif action == 'publish':
                release = publish(release.pk, request.user)
            elif action == 'cancel':
                release.status = 'cancelled'
                release.save()
            else:
                raise ValidationError('Unknown release action.')
            if action != 'publish':
                audit(release, request.user, action)
            return Response(summary(release))
    except ModelValidationError as exc:
        raise ValidationError(exc.messages) from exc



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def session_deadline(request, session_id):
    with transaction.atomic():
        session = get_object_or_404(ReenrollmentSession.objects.select_for_update(), pk=session_id, school_id=get_request_school_id(request))
        manager(request, session)
        if not isinstance(request.data, dict) or set(request.data) != {'deadline_at', 'communication_timezone'}:
            raise ValidationError('Provide only deadline_at and communication_timezone.')
        raw = request.data['deadline_at']
        zone = request.data['communication_timezone']
        try:
            deadline = parse_datetime(raw) if isinstance(raw, str) else None
            if deadline is None or timezone.is_naive(deadline) or not isinstance(zone, str):
                raise ValueError('Invalid deadline or timezone.')
            ZoneInfo(zone)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValidationError('Use an offset-aware deadline and a valid timezone.') from exc
        session.deadline_at = deadline
        session.communication_timezone = zone
        session.save(update_fields=['deadline_at', 'communication_timezone', 'updated_at'])
        invalidate_session_releases(session, request.user)
        AuditLog.objects.create(user_id=request.user.pk, action='content.deadline_updated', model='reenrollment.ReenrollmentSession', object_id=str(session.pk), metadata={'school_id': str(session.school_id), 'deadline_at': deadline.isoformat(), 'communication_timezone': zone})
        return Response({'deadline_at': deadline.isoformat(), 'communication_timezone': zone})


def guardian_for(request):
    return get_object_or_404(Guardian, school_id=get_request_school_id(request), account=request.user, account__is_active=True, household__is_active=True)


def visible_receipts(guardian):
    return ReleaseReceipt.objects.filter(guardian=guardian, release__session__school_id=guardian.school_id, release__status='published').filter(Q(release__expires_at__isnull=True) | Q(release__expires_at__gt=timezone.now())).exclude(release__superseded_by__status='published')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def family_feed(request):
    guardian = guardian_for(request)
    return Response([{'id': str(r.release_id), **r.release.snapshot, 'acknowledged_at': r.acknowledged_at, 'response': r.response} for r in visible_receipts(guardian).select_related('release').order_by('-release__published_at')[:100]])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def family_response(request, release_id):
    guardian = guardian_for(request)
    if not isinstance(request.data, dict):
        raise ValidationError('Provide a JSON object.')
    response = request.data.get('response', '')
    if response not in ('returning', 'declining', 'undecided') or set(request.data) != {'response'}:
        raise ValidationError('Choose returning, declining or undecided.')
    with transaction.atomic():
        receipt = get_object_or_404(visible_receipts(guardian).select_for_update(), release_id=release_id)
        receipt.response = response
        receipt.acknowledged_at = timezone.now()
        receipt.save()
        audit(receipt.release, request.user, 'family_response')
    return Response({'response': response, 'acknowledged_at': receipt.acknowledged_at})
