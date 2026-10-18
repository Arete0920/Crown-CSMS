"""The existing import wizard owns a reviewed, atomic canonical student writer."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from .models import StudentImportWizardSession as Session
from .permissions import ImportPermission
from .services import prepare, reconcile, validate_configuration, write_prepared

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [ImportPermission]
TERMINAL = {Session.STATUS_COMMITTED, Session.STATUS_VERIFIED}


def context(request):
    actor = get_user_model().objects.select_for_update().get(pk=request.user.pk)
    school = get_object_or_404(School.objects.select_for_update(), pk=get_request_school_id(request, required=True), is_active=True)
    if not actor.is_active or not user_has_permission(actor, 'rosters.edit', school):
        raise PermissionDenied('Active school roster-edit authority required.')
    return actor, school


def body(request):
    if not isinstance(request.data, dict):
        raise ValidationError('Request must be an object.')
    return request.data


def locked_session(session_id, school):
    return get_object_or_404(Session.objects.select_for_update(), id=session_id, school=school)


def model_error(exc):
    return Response({'error': '; '.join(exc.messages)}, status=400)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    with transaction.atomic():
        actor, school = context(request)
        session = Session.objects.create(school=school, created_by=actor)
        return Response({'session_id': str(session.id)}, status=201)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    try:
        data = body(request)
        with transaction.atomic():
            _, school = context(request); session = locked_session(session_id, school)
            if session.status in TERMINAL:
                return Response({'error': 'Committed import evidence is retained; start a new reviewed session.'}, status=409)
            validate_configuration(data.get('column_map'), data.get('staged_rows'))
            session.column_map = data['column_map']; session.staged_rows = data['staged_rows']
            session.preview_result = None; session.status = Session.STATUS_CONFIGURED; session.save()
            return Response({'session_id': str(session.id), 'status': session.status, 'row_count': len(session.staged_rows)})
    except ModelValidationError as exc:
        return model_error(exc)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def preview_session(request, session_id):
    try:
        with transaction.atomic():
            _, school = context(request); session = locked_session(session_id, school)
            if session.status not in {Session.STATUS_CONFIGURED, Session.STATUS_PREVIEWED}:
                return Response({'error': 'Configure an uncommitted session before preview.'}, status=400)
            _, preview = prepare(session, lock=True)
            session.preview_result = preview; session.status = Session.STATUS_PREVIEWED; session.save()
            return Response({'session_id': str(session.id), 'status': session.status, **preview})
    except ModelValidationError as exc:
        return model_error(exc)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    try:
        data = body(request)
        if data.get('confirm') is not True:
            raise ValidationError('confirm must be true for the reviewed canonical changes.')
        reason = data.get('reason')
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            raise ValidationError('A review reason of at most 2000 characters is required.')
        with transaction.atomic():
            actor, school = context(request); session = locked_session(session_id, school)
            if session.status in TERMINAL:
                old = session.commit_result or {}
                if old.get('schema') != 2 or old.get('fingerprint') != data.get('fingerprint') or old.get('reason') != reason.strip():
                    return Response({'error': 'Committed session evidence differs; reconcile before a new import.'}, status=409)
                return Response({'session_id': str(session.id), 'status': session.status, **old})
            if session.status != Session.STATUS_PREVIEWED or not session.preview_result or session.preview_result.get('errors'):
                return Response({'error': 'A complete valid preview is required.'}, status=409)
            if data.get('fingerprint') != session.preview_result.get('fingerprint'):
                return Response({'error': 'Submit the exact reviewed preview fingerprint.'}, status=409)
            prepared, current = prepare(session, lock=True)
            if current['errors'] or current['fingerprint'] != session.preview_result['fingerprint']:
                return Response({'error': 'Canonical data or mappings changed; preview again before committing.'}, status=409)
            result = write_prepared(session, prepared, actor, reason.strip(), current['fingerprint'])
            session.commit_result = result; session.status = Session.STATUS_COMMITTED; session.save()
            return Response({'session_id': str(session.id), 'status': session.status, **result})
    except ModelValidationError as exc:
        return model_error(exc)
    except IntegrityError:
        return Response({'error': 'Canonical identity conflict; no import rows committed. Reconcile and preview again.'}, status=409)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    try:
        with transaction.atomic():
            _, school = context(request); session = locked_session(session_id, school)
            if session.status not in TERMINAL:
                return Response({'error': 'Commit before verifying canonical rows.'}, status=400)
            verification = reconcile(session)
            if verification['verified'] and session.status == Session.STATUS_COMMITTED:
                session.status = Session.STATUS_VERIFIED; session.save(update_fields=['status', 'updated_at'])
            return Response({'session_id': str(session.id), 'status': session.status, **session.commit_result,
                **verification, 'verified_at': timezone.now(), 'source': 'live'})
    except ModelValidationError as exc:
        return model_error(exc)
